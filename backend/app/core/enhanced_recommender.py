from app.core.improved_recommender import ImprovedMoodRecommender
import pandas as pd

class EnhancedMoodRecommender(ImprovedMoodRecommender):
    """Enhanced mood-based recommender with international cinema representation"""
    
    def __init__(self, mood_mapping, tmdb_api_key=None, movielens_dir="./data/ml-latest-small/"):
        super().__init__(mood_mapping, tmdb_api_key, movielens_dir)
        
        # Cache for TMDB data to reduce API calls
        self.tmdb_cache = {}
        
        # Track diversity data
        self.movie_studios = {}
        self.movie_countries = {}
        self.movie_languages = {}
        
        # Initialize international metrics
        self.country_representation = {}
        self.language_representation = {}
        
        # Track underrepresented countries/regions for boosting
        self.underrepresented_regions = {
            "South America": ["Argentina", "Brazil", "Chile", "Colombia", "Peru", "Venezuela"],
            "Asia": ["China", "Japan", "South Korea", "India", "Thailand", "Vietnam", "Indonesia"],
            "Africa": ["South Africa", "Nigeria", "Kenya", "Morocco", "Egypt"],
            "Middle East": ["Iran", "Turkey", "Israel", "Lebanon", "Saudi Arabia"],
            "Eastern Europe": ["Russia", "Poland", "Czech Republic", "Hungary", "Romania"]
        }
        
        # Load or preload TMDB data if API key provided
        if tmdb_api_key:
            self.preload_tmdb_data()
    
    def preload_tmdb_data(self, sample_size=1000):  # CHANGED FROM 200 TO 1000
        """Preload TMDB data for more movies"""
        print(f"Preloading TMDB data for {sample_size} movies...")
        
        # Get movies with TMDB IDs
        movies_with_tmdb = self.movies[pd.notna(self.movies['tmdbId'])]
        
        # Take random sample with stratification by decade (to ensure diverse temporal coverage)
        if len(movies_with_tmdb) > sample_size:
            # Add decade column for stratification
            movies_with_tmdb = movies_with_tmdb.copy()
            movies_with_tmdb.loc[:, 'decade'] = movies_with_tmdb['year'].apply(
                lambda x: (x // 10) * 10 if pd.notna(x) else 2000
            )
            
            # Stratified sample by decade with MORE movies per decade
            sample = pd.DataFrame()
            for decade, group in movies_with_tmdb.groupby('decade'):
                n_samples = max(10, int((len(group) / len(movies_with_tmdb)) * sample_size))  # INCREASED FROM 5 TO 10
                decade_sample = group.sample(n_samples) if len(group) > n_samples else group
                sample = pd.concat([sample, decade_sample])
            
            # If needed, supplement with random samples to reach target size
            if len(sample) < sample_size:
                remaining = movies_with_tmdb[~movies_with_tmdb['movieId'].isin(sample['movieId'])]
                additional = remaining.sample(min(sample_size - len(sample), len(remaining)))
                sample = pd.concat([sample, additional])
        else:
            sample = movies_with_tmdb
        
        # Fetch TMDB data with progress tracking
        processed = 0
        for _, movie in sample.iterrows():
            tmdb_id = int(movie['tmdbId'])
            self._get_and_process_tmdb_data(movie['movieId'], tmdb_id)
            processed += 1
            
            # Progress logging every 100 movies
            if processed % 100 == 0:
                print(f"Preloaded {processed}/{len(sample)} movies...")
        
        # Summarize what we found
        print(f"Preloaded data for {len(self.tmdb_cache)} movies")
        
        if self.movie_studios:
            all_studios = set(sum(self.movie_studios.values(), []))
            print(f"Found {len(all_studios)} unique studios")
        
        if self.movie_countries:
            all_countries = set(sum(self.movie_countries.values(), []))
            print(f"Found {len(all_countries)} unique countries")
            
            # Calculate country representation
            for movie_id, countries in self.movie_countries.items():
                for country in countries:
                    self.country_representation[country] = self.country_representation.get(country, 0) + 1
            
            # Print top countries
            top_countries = sorted(self.country_representation.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"Top countries: {', '.join([f'{c[0]} ({c[1]})' for c in top_countries])}")
        
        if self.movie_languages:
            all_languages = set(sum(self.movie_languages.values(), []))
            print(f"Found {len(all_languages)} unique languages")
            
            # Calculate language representation
            for movie_id, languages in self.movie_languages.items():
                for language in languages:
                    self.language_representation[language] = self.language_representation.get(language, 0) + 1
            
            # Print top languages
            top_languages = sorted(self.language_representation.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"Top languages: {', '.join([f'{l[0]} ({l[1]})' for l in top_languages])}")
    
    def _get_and_process_tmdb_data(self, movie_id, tmdb_id):
        """Get TMDB data and extract diversity information"""
        if tmdb_id in self.tmdb_cache:
            return self.tmdb_cache[tmdb_id]
            
        data = self.fetch_tmdb_data(tmdb_id)
        if data:
            self.tmdb_cache[tmdb_id] = data
            
            # Extract studio information
            if 'production_companies' in data:
                studios = [company['name'] for company in data['production_companies']]
                self.movie_studios[movie_id] = studios
            
            # Extract country information
            if 'production_countries' in data:
                countries = [country['name'] for country in data['production_countries']]
                self.movie_countries[movie_id] = countries
                
            # Extract language information
            if 'spoken_languages' in data:
                languages = [lang['name'] for lang in data['spoken_languages']]
                self.movie_languages[movie_id] = languages
                
        return data
    
    def _is_from_underrepresented_region(self, movie_id):
        """Check if a movie is from an underrepresented region"""
        if movie_id not in self.movie_countries:
            return False
            
        countries = self.movie_countries[movie_id]
        
        # Check if any of the production countries are in our underrepresented regions
        for region, region_countries in self.underrepresented_regions.items():
            if any(country in region_countries for country in countries):
                return True
                
        # Check for non-US, non-Western European films (also underrepresented)
        western_europe = ["United Kingdom", "France", "Germany", "Italy", "Spain"]
        if "United States of America" not in countries and not any(country in western_europe for country in countries):
            return True
            
        return False
    
    def calculate_movie_mood_score(self, movie, mood):
        """
        Enhanced scoring function with international cinema representation
        """
        # Get base score from parent class
        score = super().calculate_movie_mood_score(movie, mood)
        
        # Skip if base score is too low
        if score <= 0:
            return 0
        
        # Add international diversity factors
        movie_id = movie['movieId']
        
        # Factor 1: Studio diversity
        if movie_id in self.movie_studios:
            studios = self.movie_studios[movie_id]
            
            # Boost for independent studios (not major Hollywood studios)
            major_studios = ["Warner Bros.", "Walt Disney Pictures", "Universal Pictures", 
                            "Columbia Pictures", "Paramount", "20th Century Fox", "Metro-Goldwyn-Mayer"]
            
            if not any(major in studio for studio in studios for major in major_studios):
                score *= 1.15  # 15% boost for independent studios
        
        # Factor 2: Country diversity
        if movie_id in self.movie_countries:
            # Significant boost for underrepresented regions
            if self._is_from_underrepresented_region(movie_id):
                score *= 1.25  # 25% boost for underrepresented regions
        
        # Factor 3: Language diversity
        if movie_id in self.movie_languages:
            languages = self.movie_languages[movie_id]
            
            # Boost for non-English films
            if languages and "English" not in languages:
                score *= 1.2  # 20% boost for non-English films
            # Smaller boost for multilingual films with English
            elif languages and len(languages) > 1 and "English" in languages:
                score *= 1.1  # 10% boost for multilingual films
        
        return score
    
    def get_recommendations(self, mood, n=10):
        """
        Get recommendations with enhanced diversity awareness
        """
        if mood not in self.mood_mapping:
            raise ValueError(f"Unknown mood: {mood}")
            
        # Get a larger candidate pool (3x desired recommendations)
        candidates = []
        for _, movie in self.movies.iterrows():
            # Skip movies with very few ratings to ensure quality
            if movie['num_ratings'] < 3:
                continue
                
            # Calculate mood score
            score = self.calculate_movie_mood_score(movie, mood)
            
            if score > 0:
                candidates.append({
                    'movieId': movie['movieId'],
                    'title': movie['title'],
                    'genres': movie['genres'],
                    'year': movie.get('year'),
                    'rating': movie['avg_rating'],
                    'popularity': movie['num_ratings'],
                    'score': score,
                    'tmdbId': movie.get('tmdbId')
                })
        
        # Sort candidates by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply diversity-aware selection
        selected = []
        
        # Tracking dictionaries for diversity
        decades_count = {}  # Track selected decades
        genres_count = {}   # Track selected genres
        studios_count = {}  # Track selected studios
        countries_count = {} # Track selected countries
        
        # Part 1: Take 20% of selections from top-scored movies
        top_count = max(1, int(n * 0.2))
        selected.extend(candidates[:top_count])
        candidates = candidates[top_count:]
        
        # Update tracking dictionaries
        for movie in selected:
            movie_id = movie['movieId']
            
            # Track decade
            if pd.notna(movie['year']):
                decade = (movie['year'] // 10) * 10
                decades_count[decade] = decades_count.get(decade, 0) + 1
            
            # Track genres
            for genre in movie['genres'].split('|'):
                genres_count[genre] = genres_count.get(genre, 0) + 1
            
            # Track studios and countries if available
            if movie_id in self.movie_studios:
                for studio in self.movie_studios[movie_id]:
                    studios_count[studio] = studios_count.get(studio, 0) + 1
                    
            if movie_id in self.movie_countries:
                for country in self.movie_countries[movie_id]:
                    countries_count[country] = countries_count.get(country, 0) + 1
        
        # Part 2: International cinema quota (20%)
        # Prioritize movies from underrepresented regions
        international_quota = max(1, int(n * 0.2))
        international_count = 0
        
        # Filter candidates that meet international criteria
        international_candidates = [
            c for c in candidates 
            if c['movieId'] in self.movie_countries and 
            self._is_from_underrepresented_region(c['movieId'])
        ]
        
        # Add international selections
        for candidate in international_candidates:
            if international_count >= international_quota or len(selected) >= n:
                break
                
            # Only add if not already too many from same decade/country
            decade = (candidate['year'] // 10) * 10 if pd.notna(candidate['year']) else None
            countries = self.movie_countries.get(candidate['movieId'], [])
            
            # Skip if already have 2+ movies from this decade or country
            if (decade and decades_count.get(decade, 0) >= 2) or any(countries_count.get(c, 0) >= 2 for c in countries):
                continue
                
            selected.append(candidate)
            candidates.remove(candidate)
            international_count += 1
            
            # Update tracking counts
            if decade:
                decades_count[decade] = decades_count.get(decade, 0) + 1
                
            for genre in candidate['genres'].split('|'):
                genres_count[genre] = genres_count.get(genre, 0) + 1
                
            for country in countries:
                countries_count[country] = countries_count.get(country, 0) + 1
        
        # Part 3: Fill remaining slots with diversity focus
        while candidates and len(selected) < n:
            # Calculate diversity scores for top candidates
            top_candidates = candidates[:min(30, len(candidates))]
            
            for candidate in top_candidates:
                # Start with normalized score
                normalized_score = candidate['score'] / top_candidates[0]['score']
                diversity_score = normalized_score * 0.5  # Initial weight is 50% of original score
                
                movie_id = candidate['movieId']
                
                # Decade diversity (temporal)
                if pd.notna(candidate['year']):
                    decade = (candidate['year'] // 10) * 10
                    if decade not in decades_count:
                        diversity_score += 0.15  # Big bonus for new decade
                    elif decades_count[decade] < 2:
                        diversity_score += 0.05  # Small bonus for underrepresented decade
                
                # Genre diversity
                new_genres = 0
                for genre in candidate['genres'].split('|'):
                    if genre not in genres_count:
                        new_genres += 1
                    elif genres_count[genre] < 2:
                        new_genres += 0.5
                        
                diversity_score += min(0.15, new_genres * 0.05)  # Up to 15% for genre diversity
                
                # Studio diversity
                if movie_id in self.movie_studios:
                    studios = self.movie_studios[movie_id]
                    if any(studio not in studios_count for studio in studios):
                        diversity_score += 0.1  # 10% bonus for new studio
                
                # Country/language diversity
                if movie_id in self.movie_countries:
                    countries = self.movie_countries[movie_id]
                    if any(country not in countries_count for country in countries):
                        diversity_score += 0.1  # 10% bonus for new country
                
                # Store the diversity score
                candidate['diversity_score'] = diversity_score
            
            # Sort by diversity score
            top_candidates.sort(key=lambda x: x.get('diversity_score', 0), reverse=True)
            
            # Select the highest scoring candidate
            next_selection = top_candidates[0]
            selected.append(next_selection)
            candidates.remove(next_selection)
            
            # Update tracking dictionaries
            movie_id = next_selection['movieId']
            
            # Track decade
            if pd.notna(next_selection['year']):
                decade = (next_selection['year'] // 10) * 10
                decades_count[decade] = decades_count.get(decade, 0) + 1
            
            # Track genres
            for genre in next_selection['genres'].split('|'):
                genres_count[genre] = genres_count.get(genre, 0) + 1
            
            # Track studios and countries
            if movie_id in self.movie_studios:
                for studio in self.movie_studios[movie_id]:
                    studios_count[studio] = studios_count.get(studio, 0) + 1
                    
            if movie_id in self.movie_countries:
                for country in self.movie_countries[movie_id]:
                    countries_count[country] = countries_count.get(country, 0) + 1
        
        # Return as DataFrame
        return pd.DataFrame(selected)
    
    def get_diversity_stats(self, recommendations):
        """
        Calculate diversity statistics for a set of recommendations
        
        Parameters:
            recommendations (DataFrame): Recommended movies
            
        Returns:
            dict: Diversity statistics
        """
        stats = {
            "total_movies": len(recommendations),
            "decades": {},
            "genres": {},
            "studios": {},
            "countries": {},
            "languages": {}
        }
        
        # Count decades
        years = recommendations['year'].dropna()
        if not years.empty:
            decades = years.apply(lambda x: (x // 10) * 10)
            stats["decades"] = decades.value_counts().to_dict()
        
        # Count genres
        all_genres = []
        for genres in recommendations['genres']:
            all_genres.extend(genres.split('|'))
        stats["genres"] = pd.Series(all_genres).value_counts().to_dict()
        
        # Count studios
        all_studios = []
        for movie_id in recommendations['movieId']:
            if movie_id in self.movie_studios:
                all_studios.extend(self.movie_studios[movie_id])
        if all_studios:
            stats["studios"] = pd.Series(all_studios).value_counts().to_dict()
            
        # Count countries
        all_countries = []
        for movie_id in recommendations['movieId']:
            if movie_id in self.movie_countries:
                all_countries.extend(self.movie_countries[movie_id])
        if all_countries:
            stats["countries"] = pd.Series(all_countries).value_counts().to_dict()
            
        # Count languages
        all_languages = []
        for movie_id in recommendations['movieId']:
            if movie_id in self.movie_languages:
                all_languages.extend(self.movie_languages[movie_id])
        if all_languages:
            stats["languages"] = pd.Series(all_languages).value_counts().to_dict()
            
        return stats