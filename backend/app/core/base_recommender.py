import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import settings

DATA_PATH = settings.DATA_PATH
TMDB_API_KEY = settings.TMDB_API_KEY
TMDB_BASE_URL = settings.TMDB_BASE_URL
REQUEST_TIMEOUT = settings.REQUEST_TIMEOUT
MAX_RETRIES = settings.MAX_RETRIES
RETRY_BACKOFF_FACTOR = settings.RETRY_BACKOFF_FACTOR
RETRY_STATUS_FORCELIST = settings.RETRY_STATUS_FORCELIST

class MoodBasedRecommender:
    def __init__(self, mood_mapping, tmdb_api_key=None, movielens_dir=DATA_PATH):
        self.mood_mapping = mood_mapping
        self.tmdb_api_key = tmdb_api_key
        self.tmdb_base_url = TMDB_BASE_URL
        self.movielens_dir = movielens_dir
        
        # Create a session with retry capability
        self.session = requests.Session()
        retries = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            status_forcelist=RETRY_STATUS_FORCELIST,
            allowed_methods=["GET"],
            respect_retry_after_header=True
        )
        
        # Configure connection pooling
        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=settings.CONNECTION_POOL_SIZE,
            pool_maxsize=settings.CONNECTION_POOL_MAXSIZE,
            pool_block=False
        )
        self.session.mount('https://', adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'MoodBinge/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        
        # Initialize data
        self.load_and_process_data()
        
    def load_and_process_data(self):
        """Load and preprocess the MovieLens datasets"""
        try:
            # Load core datasets
            self.movies = pd.read_csv(f"{self.movielens_dir}movies.csv")
            self.ratings = pd.read_csv(f"{self.movielens_dir}ratings.csv")
            self.links = pd.read_csv(f"{self.movielens_dir}links.csv")
            
            # Load tags if available
            try:
                self.tags = pd.read_csv(f"{self.movielens_dir}tags.csv")
                self.has_tags = True
            except:
                print("Tags file not found, continuing without tags")
                self.has_tags = False
            
            # Process data
            self.preprocess_data()
            self.create_keyword_indexes()
            
            print(f"Data loaded successfully: {len(self.movies)} movies")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def preprocess_data(self):
        """Prepare MovieLens data for recommendations"""
        # Extract year from title
        self.movies['year'] = self.movies['title'].str.extract(r'\((\d{4})\)$')
        self.movies['year'] = pd.to_numeric(self.movies['year'], errors='coerce')
        
        # Calculate average ratings
        ratings_summary = self.ratings.groupby('movieId').agg(
            avg_rating=('rating', 'mean'),
            num_ratings=('rating', 'count')
        ).reset_index()
        
        # Merge with movies dataframe
        self.movies = pd.merge(self.movies, ratings_summary, on='movieId', how='left')
        
        # Process tags if available
        if self.has_tags:
            # Clean tags - convert to lowercase and remove special characters
            self.tags['clean_tag'] = self.tags['tag'].str.lower().str.replace(r'[^\w\s]', '', regex=True)
            
            # Group tags by movie
            movie_tags = self.tags.groupby('movieId')['clean_tag'].apply(list).reset_index()
            self.movies = pd.merge(self.movies, movie_tags, on='movieId', how='left')
        else:
            self.movies['clean_tag'] = None
        
        # Merge with TMDB links
        self.movies = pd.merge(self.movies, self.links, on='movieId', how='left')
        
        # Fill missing values
        self.movies['avg_rating'] = self.movies['avg_rating'].fillna(0)
        self.movies['num_ratings'] = self.movies['num_ratings'].fillna(0)
        self.movies['clean_tag'] = self.movies['clean_tag'].fillna(lambda x: [])
    
    def create_keyword_indexes(self):
        """Create lookup dictionaries for efficient keyword matching"""
        # Create mood-to-keywords mapping
        self.mood_keyword_lookup = {}
        
        for mood, details in self.mood_mapping.items():
            # Normalize and combine all tags and keywords
            all_keywords = set()
            
            for tag in details.get('tags', []):
                all_keywords.add(tag.lower().strip())
                
            for keyword in details.get('tmdb_keywords', []):
                all_keywords.add(keyword.lower().strip())
                
            self.mood_keyword_lookup[mood] = all_keywords
    
    def fetch_tmdb_data(self, tmdb_id, max_retries=3):
        """
        Fetch movie data from TMDB API with improved error handling
        
        Parameters:
            tmdb_id (int): TMDB ID of the movie
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            dict: Movie data from TMDB API or None if unavailable
        """
        if not self.tmdb_api_key or not tmdb_id or pd.isna(tmdb_id):
            return None
            
        # Convert to integer if needed
        try:
            tmdb_id = int(tmdb_id)
        except:
            return None
            
        # Build request
        movie_url = f"{self.tmdb_base_url}/movie/{tmdb_id}"
        params = {
            'api_key': self.tmdb_api_key,
            'language': 'en-US',
            'append_to_response': 'keywords'
        }
        
        for attempt in range(max_retries):
            try:
                # Add jitter to prevent rate limiting
                if attempt > 0:
                    time.sleep(1 + random.random())
                    
                response = self.session.get(
                    movie_url, 
                    params=params, 
                    timeout=settings.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited - get retry-after header if available
                    retry_after = int(response.headers.get('Retry-After', 2))
                    print(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                elif response.status_code in [404, 400]:
                    # Movie not found or bad request
                    return None
                else:
                    print(f"Error: Status code {response.status_code} for movie ID {tmdb_id}")
                    time.sleep(1)  # Add small delay for other errors
                    
            except requests.exceptions.ConnectionError as e:
                wait_time = (attempt + 1) * 2
                print(f"Connection error: {str(e)}, retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                
            except requests.exceptions.Timeout:
                print(f"Timeout error for movie {tmdb_id}, retrying...")
                time.sleep(1)
                
            except Exception as e:
                print(f"Exception when fetching TMDB data for movie {tmdb_id}: {e}")
                time.sleep(1)
                
        print(f"Failed to fetch TMDB data for movie {tmdb_id} after {max_retries} attempts")
        return None
    
    def get_recommendations_without_tmdb(self, mood, n=10):
        """
        Get recommendations using only MovieLens data without TMDB API
        
        Parameters:
            mood (str): Target mood category
            n (int): Number of recommendations to return
            
        Returns:
            DataFrame: Top n recommended movies with scores
        """
        if mood not in self.mood_mapping:
            raise ValueError(f"Unknown mood: {mood}")
            
        mood_details = self.mood_mapping[mood]
        results = []
        
        # Process each movie
        for _, movie in self.movies.iterrows():
            # Skip movies with very few ratings
            if movie['num_ratings'] < 5:
                continue
                
            # Calculate base score from genre matching
            score = self._calculate_genre_score(movie, mood_details)
            
            # Skip movies with poor genre match
            if score <= 0.2:
                continue
                
            # Factor in tags if available
            if self.has_tags and 'clean_tag' in movie and isinstance(movie['clean_tag'], list):
                score = self._enhance_with_tags(score, movie, mood)
                
            # Factor in rating and popularity
            score = self._apply_rating_popularity(score, movie, mood)
            
            # Add to results if score is meaningful
            if score > 0.5:
                results.append({
                    'movieId': movie['movieId'],
                    'title': movie['title'],
                    'genres': movie['genres'],
                    'year': movie.get('year'),
                    'rating': movie['avg_rating'],
                    'popularity': movie['num_ratings'],
                    'score': score
                })
        
        # Sort by score and get top n
        results.sort(key=lambda x: x['score'], reverse=True)
        return pd.DataFrame(results[:n])
    
    def _calculate_genre_score(self, movie, mood_details):
        """Calculate score based on genre matching"""
        score = 1.0
        movie_genres = movie['genres'].split('|')
        
        # Primary genres (high weight)
        primary_matches = sum(1 for genre in mood_details['primary_genres'] 
                             if genre in movie_genres)
        if primary_matches > 0:
            score *= (1 + 0.5 * primary_matches)
        else:
            # No primary genres is a disadvantage
            score *= 0.5
        
        # Secondary genres (medium weight)
        secondary_matches = sum(1 for genre in mood_details['secondary_genres'] 
                               if genre in movie_genres)
        if secondary_matches > 0:
            score *= (1 + 0.2 * secondary_matches)
        
        # Excluded genres (strong penalty)
        excluded_matches = sum(1 for genre in mood_details['excluded_genres'] 
                              if genre in movie_genres)
        if excluded_matches > 0:
            score *= (0.3 ** excluded_matches)
            
        return score
    
    def _enhance_with_tags(self, score, movie, mood):
        """Enhance score using tag matching"""
        # Skip if no tags
        if not movie['clean_tag'] or len(movie['clean_tag']) == 0:
            return score
            
        # Get mood keywords
        mood_keywords = self.mood_keyword_lookup[mood]
        
        # Count matches
        matches = sum(1 for tag in movie['clean_tag'] if tag in mood_keywords)
        
        # Apply bonus based on matches (diminishing returns)
        if matches == 0:
            return score
        elif matches == 1:
            return score * 1.2
        elif matches == 2:
            return score * 1.35
        else:
            return score * min(1.5, 1.35 + 0.05 * (matches - 2))
    
    def _apply_rating_popularity(self, score, movie, mood):
        """Apply rating and popularity factors to score"""
        # Rating factor (0-5 scale)
        rating_factor = movie['avg_rating'] / 5.0
        
        # Popularity factor with diminishing returns
        popularity = movie['num_ratings'] 
        popularity_factor = min(np.log1p(popularity) / 6, 0.5)
        
        # Adjust weights based on mood
        if mood in ['cosmic_emptiness', 'wonder_hunt']:
            # These moods might value quality over popularity
            return score * (1 + (rating_factor * 0.6) + (popularity_factor * 0.2))
        else:
            # Default weight balance
            return score * (1 + (rating_factor * 0.4) + (popularity_factor * 0.3))
    
    def get_recommendations(self, mood, n=10):
        """
        Get movie recommendations for a specific mood
        
        Parameters:
            mood (str): Target mood category
            n (int): Number of recommendations to return
            
        Returns:
            DataFrame: Top n recommended movies with scores
        """
        # If TMDB is enabled, try to use it but fall back if issues occur
        if self.tmdb_api_key:
            try:
                return self._get_recommendations_with_tmdb(mood, n)
            except Exception as e:
                print(f"Error using TMDB data: {e}")
                print("Falling back to recommendations without TMDB")
                
        # Use MovieLens-only approach
        return self.get_recommendations_without_tmdb(mood, n)
    
    def _get_recommendations_with_tmdb(self, mood, n=10, max_candidates=100):
        """Implementation with TMDB integration"""
        # First get a larger set of candidates using basic matching
        candidates = self.get_recommendations_without_tmdb(mood, max_candidates)
        
        # Enhance top candidates with TMDB data
        enhanced_results = []
        
        for _, movie in candidates.iterrows():
            tmdb_data = None
            if 'tmdbId' in self.movies.columns:
                # Get movie row from main dataframe to access tmdbId
                movie_row = self.movies[self.movies['movieId'] == movie['movieId']].iloc[0]
                if not pd.isna(movie_row['tmdbId']):
                    tmdb_data = self.fetch_tmdb_data(movie_row['tmdbId'])
            
            # Recalculate score with TMDB data if available
            if tmdb_data:
                new_score = self._enhance_score_with_tmdb(movie['score'], tmdb_data, mood)
            else:
                new_score = movie['score']
                
            enhanced_results.append({
                'movieId': movie['movieId'],
                'title': movie['title'],
                'genres': movie['genres'],
                'year': movie.get('year'),
                'rating': movie['rating'],
                'popularity': movie['popularity'],
                'score': new_score,
                'has_tmdb_data': tmdb_data is not None
            })
        
        # Resort based on enhanced scores
        enhanced_results.sort(key=lambda x: x['score'], reverse=True)
        return pd.DataFrame(enhanced_results[:n])
    
    def _enhance_score_with_tmdb(self, base_score, tmdb_data, mood):
        """Enhance score with TMDB data features"""
        score = base_score
        mood_details = self.mood_mapping[mood]
        
        # 1. Runtime appropriateness
        if 'runtime' in tmdb_data and tmdb_data['runtime']:
            runtime = tmdb_data['runtime']
            pref = mood_details.get('runtime_preference', {})
            
            if pref:
                min_runtime = pref.get('min', 0)
                ideal_runtime = pref.get('ideal', 120)
                max_runtime = pref.get('max', 240)
                
                # Apply runtime factors
                if runtime < min_runtime:
                    score *= 0.8
                elif runtime > max_runtime:
                    score *= 0.7
                elif abs(runtime - ideal_runtime) <= 15:
                    score *= 1.2
        
        # 2. Release year relevance
        if 'release_date' in tmdb_data and tmdb_data['release_date']:
            try:
                year = int(tmdb_data['release_date'].split('-')[0])
                year_pref = mood_details.get('year_preference', 'not_important')
                
                if year_pref == 'recency_bonus':
                    current_year = datetime.now().year
                    if year >= current_year - 5:
                        score *= 1.2
                    elif year >= current_year - 10:
                        score *= 1.1
                elif isinstance(year_pref, dict) and 'classic_eras' in year_pref:
                    classic_eras = year_pref['classic_eras']
                    decade = (year // 10) * 10
                    if decade in classic_eras:
                        score *= 1.3
            except:
                pass
        
        # 3. TMDB keywords
        if 'keywords' in tmdb_data and 'keywords' in tmdb_data['keywords']:
            tmdb_keywords = [kw['name'].lower() for kw in tmdb_data['keywords']['keywords']]
            mood_keywords = self.mood_keyword_lookup[mood]
            
            # Count matches
            matches = sum(1 for kw in tmdb_keywords if kw in mood_keywords)
            
            if matches > 0:
                score *= min(1.5, 1 + (0.1 * matches))
        
        # 4. Overview/tagline sentiment
        if self.sia and (('overview' in tmdb_data and tmdb_data['overview']) or 
                        ('tagline' in tmdb_data and tmdb_data['tagline'])):
            text = tmdb_data.get('overview', '') + ' ' + tmdb_data.get('tagline', '')
            sentiment = self.sia.polarity_scores(text)
            
            # Get target sentiment for this mood
            target_sentiment = mood_details.get('sentiment', '')
            
            # Apply sentiment matching
            if target_sentiment == 'positive' and sentiment['compound'] > 0.5:
                score *= 1.2
            elif target_sentiment == 'negative_but_cathartic' and sentiment['compound'] < -0.3:
                score *= 1.15
            elif target_sentiment == 'fearful' and sentiment['neg'] > 0.3:
                score *= 1.2
            elif target_sentiment == 'peaceful' and sentiment['pos'] > 0.3 and sentiment['neg'] < 0.1:
                score *= 1.25
            elif target_sentiment == 'warm' and sentiment['pos'] > 0.4:
                score *= 1.2
            elif target_sentiment == 'sad' and sentiment['neg'] > 0.3:
                score *= 1.15
            elif target_sentiment == 'contemplative' and abs(sentiment['compound']) < 0.3:
                score *= 1.1
            elif target_sentiment == 'bittersweet' and sentiment['pos'] > 0.2 and sentiment['neg'] > 0.2:
                score *= 1.2
        
        return score
    
    def _normalize_score(self, score):
        """
        Normalize recommendation score to a 0-100 scale
        
        Parameters:
            score (float): Raw recommendation score
            
        Returns:
            float: Normalized score from 0-100
        """
        # Cap maximum score at 5 (before scaling)
        # This accounts for our multiplicative factors that could push scores above 5
        capped_score = min(5.0, score)
        
        # Scale to 0-100 range
        normalized_score = (capped_score / 5.0) * 100
        
        # Round to one decimal place
        return round(normalized_score, 1)