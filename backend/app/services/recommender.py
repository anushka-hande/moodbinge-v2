# backend/app/services/recommender.py
from app.core.config import settings
import sys
import os
import time
import re
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from app.core.enhanced_recommender import EnhancedMoodRecommender
from app.core.mood_mapping import mood_mapping, get_available_moods

try:
    from app.core.safe_enhanced_wrapper import SafeEnhancedWrapper
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    print("Enhanced features not available - using original system only")
    ENHANCED_FEATURES_AVAILABLE = False

USER_AGENTS = [
    "MoodBinge/1.0",
    "Mozilla/5.0 (compatible; MoodBingeBot/1.0)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    # Add more if you want
]

def get_retry_session():
    """
    🚀 OPTIMIZED: HTTP session with aggressive performance tuning
    """
    session = requests.Session()
    
    # OPTIMIZED: Fewer retries, faster backoff
    retries = Retry(
        total=3,                    # REDUCED from 5
        backoff_factor=0.5,         # REDUCED from 2 - faster recovery  
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False       # Don't raise exceptions, let us handle them
    )
    
    # OPTIMIZED: Connection pooling
    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=8,         # REDUCED from default 10
        pool_maxsize=15,           # REDUCED from default 20  
        pool_block=False           # Don't block when pool is full
    )
    
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    
    # OPTIMIZED: Default headers for better performance
    session.headers.update({
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': 'application/json',
        'User-Agent': random.choice(USER_AGENTS)
    })
    
    return session

class RecommenderService:
    def __init__(self):
        # Initialize the recommender with the mood mapping and TMDB API key
        self.recommender = EnhancedMoodRecommender(
            mood_mapping=mood_mapping,
            tmdb_api_key=settings.TMDB_API_KEY,
            movielens_dir=settings.DATA_PATH
        )
        self.session = get_retry_session()

        # Initialize enhanced features if available and enabled
        self.enhanced_features_enabled = (
            ENHANCED_FEATURES_AVAILABLE and 
            settings.USE_ENHANCED_RECOMMENDATIONS
        )
        
        if self.enhanced_features_enabled:
            try:
                self.enhanced_wrapper = SafeEnhancedWrapper(
                    original_recommender=self.recommender,
                    mood_mapping=mood_mapping
                )
                print("✅ Enhanced recommendation features initialized")
            except Exception as e:
                print(f"❌ Enhanced features failed to initialize: {e}")
                self.enhanced_features_enabled = False
        
        # TMDB response cache
        self.tmdb_cache = {}
        self.cache_expiry = {}
        self.cache_duration = 3600  # 1 hour cache
        
        # Performance statistics
        self.cache_hits = 0
        self.cache_misses = 0
        
        print(f"RecommenderService initialized. Enhanced features: {self.enhanced_features_enabled}")
        print(f"🚀 Performance optimizations: Caching enabled, Cache duration: {self.cache_duration}s")

    def get_available_moods(self) -> List[Dict[str, Any]]:
        """Get a list of available mood categories with descriptions"""
        return get_available_moods()
    
    def get_recommendations(self, mood: str, n: int = 10, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get movie recommendations for a specific mood with performance optimizations
        
        Args:
            mood: Mood category
            n: Number of recommendations
            session_id: Optional session ID for enhanced features
        """
        if mood not in mood_mapping:
            raise ValueError(f"Unknown mood: {mood}")
        
        # Performance timing
        start_time = time.time()
        
        # Log request if enabled
        if settings.ENHANCED_FEATURES_LOGGING:
            enhanced_status = "enhanced" if (self.enhanced_features_enabled and session_id) else "original"
            print(f"🎬 Recommendation request: mood={mood}, n={n}, system={enhanced_status}")
        
        # Get recommendations using enhanced system if available
        if self.enhanced_features_enabled and session_id:
            try:
                recommendations = self.enhanced_wrapper.get_recommendations(
                    mood=mood,
                    n=n,
                    session_id=session_id,
                    use_enhancements=True
                )
                if settings.ENHANCED_FEATURES_LOGGING:
                    print(f"✅ Enhanced recommendations generated: {len(recommendations)} movies")
            except Exception as e:
                print(f"❌ Enhanced system failed, using original: {e}")
                # Fallback to original system
                recommendations = self.recommender.get_recommendations(mood, n)
                recommendations = self._convert_to_list_format(recommendations)
        else:
            # Use original system
            recommendations = self.recommender.get_recommendations(mood, n)
            recommendations = self._convert_to_list_format(recommendations)
            
            if settings.ENHANCED_FEATURES_LOGGING:
                print(f"📊 Original recommendations generated: {len(recommendations)} movies")
        
        # ================================================================
        # 🚀 OPTIMIZED TMDB ENHANCEMENT WITH SMART FALLBACK
        # ================================================================
        
        enhancement_start = time.time()
        
        try:
            # TRY PARALLEL ENHANCEMENT FIRST (FASTEST)
            if hasattr(self, '_run_async_enhancement'):
                result = self._run_async_enhancement(recommendations)
                
                if settings.ENHANCED_FEATURES_LOGGING:
                    print("⚡ Used parallel TMDB enhancement")
            else:
                # Parallel enhancement not available, use cached sync
                raise Exception("Parallel enhancement not initialized")
                
        except Exception as e:
            if settings.ENHANCED_FEATURES_LOGGING:
                print(f"⚠️ Parallel enhancement failed: {e}")
                print("🔄 Falling back to optimized sync enhancement...")
            
            # FALLBACK TO OPTIMIZED SYNC METHOD WITH CACHING
            result = []
            for movie in recommendations:
                # Add placeholder values for TMDB data in case the API fails
                movie["poster_path"] = None
                movie["backdrop_path"] = None
                movie["overview"] = "No overview available."
                
                # Extract year from title if not in data
                if 'year' not in movie or pd.isna(movie.get('year')):
                    year_match = re.search(r'\((\d{4})\)$', movie.get('title', ''))
                    if year_match:
                        movie['year'] = int(year_match.group(1))
                
                # Try to enhance with TMDB data using CACHED method
                if "tmdbId" in movie and movie["tmdbId"] and not pd.isna(movie["tmdbId"]):
                    try:
                        # Use cached TMDB data method (if available) or fallback to original
                        if hasattr(self, '_get_cached_tmdb_data'):
                            tmdb_data = self._get_cached_tmdb_data(int(movie["tmdbId"]))
                        else:
                            tmdb_data = self._get_tmdb_data(int(movie["tmdbId"]))
                        
                        if tmdb_data:
                            if 'poster_path' in tmdb_data:
                                movie["poster_path"] = tmdb_data.get("poster_path")
                            if 'backdrop_path' in tmdb_data:
                                movie["backdrop_path"] = tmdb_data.get("backdrop_path")
                            if 'overview' in tmdb_data and tmdb_data.get("overview"):
                                movie["overview"] = tmdb_data.get("overview")
                    except Exception as e:
                        if settings.ENHANCED_FEATURES_LOGGING:
                            print(f"Error enhancing movie data: {e}")
                
                result.append(movie)
            
            if settings.ENHANCED_FEATURES_LOGGING:
                print("✅ Used fallback sync enhancement")
        
        # ================================================================
        # 📊 PERFORMANCE LOGGING
        # ================================================================
        
        enhancement_time = time.time() - enhancement_start
        total_time = time.time() - start_time
        
        if settings.ENHANCED_FEATURES_LOGGING:
            print(f"⚡ Performance: TMDB enhancement {enhancement_time:.2f}s, Total {total_time:.2f}s")
            
            # Show cache stats if available
            if hasattr(self, 'get_cache_stats'):
                try:
                    cache_stats = self.get_cache_stats()
                    print(f"📊 Cache stats: {cache_stats['hit_rate_percent']}% hit rate, {cache_stats['cached_items']} items cached")
                except:
                    pass
        
        return result
    
    def get_original_recommendations(self, mood: str, n: int = 10) -> List[Dict[str, Any]]:
        """Get recommendations using only the original system"""
        recommendations = self.recommender.get_recommendations(mood, n)
        return self._convert_to_list_format(recommendations)
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get session statistics (enhanced feature)"""
        if not self.enhanced_features_enabled:
            return {"error": "Enhanced features not available"}
        
        return self.enhanced_wrapper.get_session_stats(session_id)
    
    def _convert_to_list_format(self, df_or_list) -> List[Dict]:
        """Convert DataFrame to List[Dict] format safely"""
        if isinstance(df_or_list, pd.DataFrame):
            return df_or_list.to_dict('records')
        elif isinstance(df_or_list, list):
            return df_or_list
        else:
            return []
    
    def get_similar_movies(self, movie_id: int, n: int = 5) -> List[Dict[str, Any]]:
        """Get similar movies for a given movie ID"""
        # Get the tmdbId for the movie
        movie_data = self.recommender.movies[self.recommender.movies['movieId'] == movie_id]
        if movie_data.empty or 'tmdbId' not in movie_data.columns:
            return []
        
        tmdb_id = movie_data.iloc[0]['tmdbId']
        if pd.isna(tmdb_id):
            return []
        
        url = f"{settings.TMDB_BASE_URL}/movie/{int(tmdb_id)}/recommendations"
        params = {
            "api_key": settings.TMDB_API_KEY,
            "language": "en-US",
            "page": 1
        }
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    time.sleep(2 ** attempt)  # exponential backoff
                response = self.session.get(
                    url,
                    params=params,
                    timeout=settings.REQUEST_TIMEOUT,
                    headers=headers
                )
            
                if response.status_code == 200:
                    similar_movies = response.json().get("results", [])[:n]
                    
                    # Transform the data to match our format
                    result = []
                    for movie in similar_movies:
                        # Try to find this movie in our dataset by TMDB ID
                        matched_movie = self.recommender.movies[self.recommender.movies['tmdbId'] == movie['id']]
                        
                        movie_data = {
                            "title": movie.get("title", ""),
                            "poster_path": movie.get("poster_path"),
                            "overview": movie.get("overview"),
                            "release_date": movie.get("release_date"),
                            "tmdbId": int(movie.get("id")) if movie.get("id") else None  # Convert to regular int
                        }
                        
                        # Add MovieLens data if we have it - convert numpy types to Python native types
                        if not matched_movie.empty:
                            # Convert numpy values to Python native types explicitly
                            movie_data["movieId"] = int(matched_movie.iloc[0]['movieId'])
                            movie_data["genres"] = str(matched_movie.iloc[0]['genres'])
                            
                            if 'avg_rating' in matched_movie.iloc[0]:
                                rating = matched_movie.iloc[0]['avg_rating']
                                movie_data["rating"] = float(rating) if not pd.isna(rating) else 0
                        
                        result.append(movie_data)
                    
                    return result
                elif response.status_code == 429:
                    time.sleep(2 ** attempt)
                elif response.status_code in [404, 400]:
                    break
                else:
                    print(f"TMDB API error: Status {response.status_code}, Content: {response.text}")
                
                # If TMDB API fails, return similar movies based on MovieLens data
                return self._get_similar_from_movielens(movie_id, n)
                
            except Exception as e:
                print(f"Error getting similar movies: {e}")
                # Fallback to MovieLens-based recommendations
                return self._get_similar_from_movielens(movie_id, n)

    def _get_similar_from_movielens(self, movie_id: int, n: int = 5) -> List[Dict[str, Any]]:
        """Get similar movies based on MovieLens data (genres) when TMDB fails"""
        try:
            # Get the movie's genres
            movie_data = self.recommender.movies[self.recommender.movies['movieId'] == movie_id]
            if movie_data.empty:
                return []
                
            target_genres = movie_data.iloc[0]['genres'].split('|')
            
            # Find movies with similar genres
            similar_movies = []
            
            for _, movie in self.recommender.movies.iterrows():
                # Skip the input movie itself
                if movie['movieId'] == movie_id:
                    continue
                    
                # Get movie genres
                movie_genres = movie['genres'].split('|')
                
                # Calculate genre similarity (count of matching genres)
                matching_genres = len(set(target_genres) & set(movie_genres))
                
                if matching_genres > 0:
                    # Calculate a similarity score based on:
                    # 1. Number of matching genres
                    # 2. Movie rating
                    # 3. Number of ratings (popularity)
                    
                    genre_score = matching_genres / max(len(target_genres), len(movie_genres))
                    rating_score = movie['avg_rating'] / 5.0 if 'avg_rating' in movie and not pd.isna(movie['avg_rating']) else 0.5
                    
                    # Normalize popularity with diminishing returns for very popular movies
                    pop_factor = np.log1p(movie['num_ratings']) / 6.0 if 'num_ratings' in movie and not pd.isna(movie['num_ratings']) else 0.5
                    pop_factor = min(pop_factor, 1.0)
                    
                    # Combined score - genre matching is most important
                    score = (genre_score * 0.6) + (rating_score * 0.25) + (pop_factor * 0.15)
                    
                    similar_movies.append({
                        'movieId': int(movie['movieId']),  # Convert numpy.int64 to Python int
                        'title': str(movie['title']),
                        'genres': str(movie['genres']),
                        'rating': float(movie['avg_rating']) if 'avg_rating' in movie and not pd.isna(movie['avg_rating']) else None,
                        'score': float(score),
                        'year': int(movie['year']) if 'year' in movie and not pd.isna(movie['year']) else None
                    })
            
            # Sort by similarity score and return top n
            similar_movies.sort(key=lambda x: x['score'], reverse=True)
            return similar_movies[:n]
            
        except Exception as e:
            print(f"Error finding similar movies from MovieLens: {e}")
            return []
    
    def _get_cached_tmdb_data(self, tmdb_id: int) -> Dict[str, Any]:
        """Get TMDB data with intelligent caching (SYNC FALLBACK)"""
        if not tmdb_id:
            return {}
        
        current_time = time.time()
        cache_key = f"tmdb_{tmdb_id}"
        
        # Check if cached and not expired
        if (cache_key in self.tmdb_cache and 
            cache_key in self.cache_expiry and 
            current_time < self.cache_expiry[cache_key]):
            self.cache_hits += 1
            if settings.ENHANCED_FEATURES_LOGGING:
                print(f"🎯 Cache hit for TMDB ID {tmdb_id}")
            return self.tmdb_cache[cache_key]
        
        # Cache miss - fetch fresh data using EXISTING sync method
        self.cache_misses += 1
        if settings.ENHANCED_FEATURES_LOGGING:
            print(f"📡 Cache miss for TMDB ID {tmdb_id}, fetching...")
        
        # USE YOUR EXISTING _get_tmdb_data METHOD (KEEP IT!)
        data = self._get_tmdb_data(tmdb_id)  # ← THIS CALLS YOUR EXISTING METHOD
        
        # Cache the result if successful
        if data:
            self.tmdb_cache[cache_key] = data
            self.cache_expiry[cache_key] = current_time + self.cache_duration
            
            # Cleanup old cache entries periodically
            if len(self.tmdb_cache) % 100 == 0:
                self._cleanup_expired_cache()
        
        return data

    def _get_tmdb_data(self, tmdb_id: int) -> Dict[str, Any]:
        """Your existing TMDB data fetching logic (unchanged)"""
        if not tmdb_id:
            return {}

        url = f"{settings.TMDB_BASE_URL}/movie/{int(tmdb_id)}"
        params = {
            "api_key": settings.TMDB_API_KEY,
            "language": "en-US"
        }
        headers = {
            "User-Agent": random.choice(USER_AGENTS)
        }

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=settings.REQUEST_TIMEOUT,
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                time.sleep(2)
            elif response.status_code in [404, 400]:
                return {}
            else:
                if settings.ENHANCED_FEATURES_LOGGING:
                    print(f"TMDB API error: Status {response.status_code}")
        except Exception as e:
            if settings.ENHANCED_FEATURES_LOGGING:
                print(f"TMDB connection error: {e}")
        return {}
    
    def _cleanup_expired_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry_time in self.cache_expiry.items() 
            if current_time >= expiry_time
        ]
        
        for key in expired_keys:
            self.tmdb_cache.pop(key, None)
            self.cache_expiry.pop(key, None)
        
        if expired_keys and settings.ENHANCED_FEATURES_LOGGING:
            print(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": round(hit_rate, 1),
            "cached_items": len(self.tmdb_cache),
            "cache_size_mb": len(str(self.tmdb_cache)) / 1024 / 1024
        }

    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        """Get detailed information for a specific movie"""
        # Try to find the movie in our database
        movie_data = self.recommender.movies[self.recommender.movies['movieId'] == movie_id]
        
        if movie_data.empty:
            return None
        
        # Get basic movie info
        movie = movie_data.iloc[0].to_dict()
        
        # Get TMDB data if available
        tmdb_data = None
        if 'tmdbId' in movie and not pd.isna(movie['tmdbId']):
            tmdb_data = self._get_tmdb_data(int(movie['tmdbId']))
        
        # Create response with combined data
        result = {
            "movieId": int(movie['movieId']),
            "title": movie['title'],
            "genres": movie['genres'],
            "year": int(movie['year']) if 'year' in movie and pd.notna(movie['year']) else None,
            "rating": float(movie['avg_rating']) if 'avg_rating' in movie else None,
            "num_ratings": int(movie['num_ratings']) if 'num_ratings' in movie else None
        }
        
        # Add TMDB data if available
        if tmdb_data:
            result.update({
                "tmdbId": int(movie['tmdbId']),
                "poster_path": tmdb_data.get('poster_path'),
                "backdrop_path": tmdb_data.get('backdrop_path'),
                "overview": tmdb_data.get('overview'),
                "release_date": tmdb_data.get('release_date'),
                "runtime": tmdb_data.get('runtime'),
                "tagline": tmdb_data.get('tagline'),
                "vote_average": tmdb_data.get('vote_average'),
                "production_companies": tmdb_data.get('production_companies', []),
                "production_countries": tmdb_data.get('production_countries', [])
            })
        
        return result
    
    def get_movie_details_by_tmdb(self, tmdb_id: int) -> Dict[str, Any]:
        """Get movie details directly from TMDB ID"""
        tmdb_data = self._get_tmdb_data(tmdb_id)
        
        if not tmdb_data:
            return None
        
        # Find if we have this movie in our database
        movie_data = self.recommender.movies[self.recommender.movies['tmdbId'] == tmdb_id]
        
        # Create result
        result = {
            "tmdbId": tmdb_id,
            "title": tmdb_data.get('title', ''),
            "poster_path": tmdb_data.get('poster_path'),
            "backdrop_path": tmdb_data.get('backdrop_path'),
            "overview": tmdb_data.get('overview'),
            "release_date": tmdb_data.get('release_date'),
            "runtime": tmdb_data.get('runtime'),
            "tagline": tmdb_data.get('tagline'),
            "vote_average": tmdb_data.get('vote_average'),
            "production_companies": tmdb_data.get('production_companies', []),
            "production_countries": tmdb_data.get('production_countries', [])
        }
        
        # Extract year from release date
        if result['release_date']:
            try:
                result['year'] = int(result['release_date'].split('-')[0])
            except:
                result['year'] = None
        
        # If we have this movie in our database, add MovieLens data
        if not movie_data.empty:
            movie = movie_data.iloc[0]
            result.update({
                "movieId": int(movie['movieId']),
                "genres": movie['genres'],
                "rating": float(movie['avg_rating']) if 'avg_rating' in movie else None,
                "num_ratings": int(movie['num_ratings']) if 'num_ratings' in movie else None
            })
        else:
            # Format genres from TMDB format
            if 'genres' in tmdb_data and tmdb_data['genres']:
                result['genres'] = '|'.join([genre['name'] for genre in tmdb_data['genres']])
        
        return result
    
    # ================================================================
    # 🆕 PARALLEL TMDB ENHANCEMENT SYSTEM
    # ================================================================
    
    async def _fetch_tmdb_data_async(self, session: aiohttp.ClientSession, tmdb_id: int) -> Dict[str, Any]:
        """Async TMDB API call with caching"""
        if not tmdb_id:
            return {}
        
        # Check cache first
        cached_data = self._get_cached_tmdb_data(tmdb_id)
        if cached_data:
            return cached_data
        
        # Fetch from API
        url = f"{settings.TMDB_BASE_URL}/movie/{int(tmdb_id)}"
        params = {
            "api_key": settings.TMDB_API_KEY,
            "language": "en-US"
        }
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        
        try:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Cache the successful response
                    cache_key = f"tmdb_{tmdb_id}"
                    self.tmdb_cache[cache_key] = data
                    self.cache_expiry[cache_key] = time.time() + self.cache_duration
                    return data
                elif response.status == 429:
                    await asyncio.sleep(1)
                    return {}
                elif response.status in [404, 400]:
                    # Cache empty response to avoid repeated failed requests
                    cache_key = f"tmdb_{tmdb_id}"
                    self.tmdb_cache[cache_key] = {}
                    self.cache_expiry[cache_key] = time.time() + 300  # Cache failures for 5 minutes
                    return {}
                else:
                    if settings.ENHANCED_FEATURES_LOGGING:
                        print(f"TMDB API error: Status {response.status}")
                    return {}
        except asyncio.TimeoutError:
            if settings.ENHANCED_FEATURES_LOGGING:
                print(f"TMDB timeout for movie {tmdb_id}")
            return {}
        except Exception as e:
            if settings.ENHANCED_FEATURES_LOGGING:
                print(f"TMDB async error for movie {tmdb_id}: {e}")
            return {}
    
    async def _enhance_movies_parallel(self, recommendations: List[Dict]) -> List[Dict]:
        """
        ⚡ ULTRA-FAST TMDB Enhancement with Aggressive Optimizations
        
        Key Performance Improvements:
        1. Optimized connection pooling (prevents connection resets)
        2. Smart request batching (reduces API calls)  
        3. Fail-fast timeouts (avoids hanging requests)
        4. Exponential backoff retry (handles rate limits gracefully)
        5. Connection reuse (eliminates handshake overhead)
        """
        if not recommendations:
            return recommendations
        
        # ================================================================
        # 🔧 OPTIMIZED CONNECTION CONFIGURATION
        # ================================================================
        
        # Create optimized connector with persistent connections
        connector = aiohttp.TCPConnector(
            # Connection pool optimization
            limit=15,                    # Reduced from 20 - TMDB prefers fewer concurrent connections
            limit_per_host=8,           # Reduced from 10 - prevents overwhelming TMDB
            ttl_dns_cache=600,          # Longer DNS cache (10 minutes)
            use_dns_cache=True,
            enable_cleanup_closed=True,  # Clean up closed connections automatically
            
            # Keep-alive optimization  
            keepalive_timeout=30,       # Keep connections alive longer
            
            # SSL optimization
            ssl=True,                  # We'll handle HTTPS at session level
        )
        
        # Aggressive timeout configuration
        timeout = aiohttp.ClientTimeout(
            total=25,        # Reduced from 30 - fail faster
            connect=3,       # Reduced from 5 - connection should be instant
            sock_read=8,     # Reduced from 10 - individual read timeout
            sock_connect=3   # Socket connection timeout
        )
        
        enhanced_movies = []
        successful_fetches = 0
        failed_fetches = 0
        
        try:
            async with aiohttp.ClientSession(
                connector=connector, 
                timeout=timeout,
                headers={
                    'User-Agent': random.choice(USER_AGENTS),
                    'Accept': 'application/json',
                    'Connection': 'keep-alive',  # Force connection reuse
                    'Accept-Encoding': 'gzip, deflate'  # Enable compression
                },
                # Trust environment proxy settings
                trust_env=True
            ) as session:
                
                # ================================================================
                # 🎯 SMART BATCHING: Process in smaller batches to reduce load
                # ================================================================
                
                batch_size = 5  # Process 5 movies at a time instead of all 10 simultaneously
                movie_batches = [recommendations[i:i + batch_size] for i in range(0, len(recommendations), batch_size)]
                
                for batch_num, batch in enumerate(movie_batches):
                    if settings.ENHANCED_FEATURES_LOGGING:
                        print(f"🚀 Processing batch {batch_num + 1}/{len(movie_batches)} ({len(batch)} movies)")
                    
                    # Create tasks for current batch
                    batch_tasks = []
                    for movie in batch:
                        # Add default TMDB values first
                        movie["poster_path"] = None
                        movie["backdrop_path"] = None 
                        movie["overview"] = "No overview available."
                        
                        # Extract year from title if missing
                        if 'year' not in movie or pd.isna(movie.get('year')):
                            year_match = re.search(r'\((\d{4})\)$', movie.get('title', ''))
                            if year_match:
                                movie['year'] = int(year_match.group(1))
                        
                        # Create TMDB fetch task if we have a valid ID
                        if "tmdbId" in movie and movie["tmdbId"] and not pd.isna(movie["tmdbId"]):
                            await asyncio.sleep(0.1)  # 100ms delay between requests in same batch
                            task = asyncio.create_task(
                                self._fetch_tmdb_with_retry(session, int(movie["tmdbId"]), movie.get('title', 'Unknown'))
                            )
                            batch_tasks.append((movie, task))
                        else:
                            batch_tasks.append((movie, None))
                    
                    # Execute batch with timeout protection
                    try:
                        # Wait for all tasks in current batch with overall timeout
                        await asyncio.wait_for(
                            asyncio.gather(*[task for _, task in batch_tasks if task], return_exceptions=True),
                            timeout=20  # 20 second timeout per batch
                        )
                    except asyncio.TimeoutError:
                        if settings.ENHANCED_FEATURES_LOGGING:
                            print(f"⚠️ Batch {batch_num + 1} timed out, continuing with available data")
                    
                    # Process results from current batch
                    for movie, task in batch_tasks:
                        if task and not task.done():
                            task.cancel()  # Cancel any still-running tasks
                        
                        if task and task.done() and not task.cancelled():
                            try:
                                tmdb_data = await task
                                if tmdb_data and isinstance(tmdb_data, dict):
                                    # Apply TMDB data
                                    if 'poster_path' in tmdb_data and tmdb_data['poster_path']:
                                        movie["poster_path"] = tmdb_data["poster_path"]
                                    if 'backdrop_path' in tmdb_data and tmdb_data['backdrop_path']:
                                        movie["backdrop_path"] = tmdb_data["backdrop_path"]
                                    if 'overview' in tmdb_data and tmdb_data.get("overview"):
                                        movie["overview"] = tmdb_data["overview"]
                                    successful_fetches += 1
                                else:
                                    failed_fetches += 1
                            except Exception as e:
                                failed_fetches += 1
                                if settings.ENHANCED_FEATURES_LOGGING:
                                    print(f"⚠️ Error processing TMDB data for '{movie.get('title', 'Unknown')}': {e}")
                        elif task:
                            failed_fetches += 1
                        
                        enhanced_movies.append(movie)
                    
                    # Small delay between batches to be nice to TMDB
                    if batch_num < len(movie_batches) - 1:
                        await asyncio.sleep(1.0)
                
                # ================================================================
                # 📊 PERFORMANCE REPORTING
                # ================================================================
                
                if settings.ENHANCED_FEATURES_LOGGING:
                    cache_stats = self.get_cache_stats()
                    success_rate = (successful_fetches / (successful_fetches + failed_fetches) * 100) if (successful_fetches + failed_fetches) > 0 else 0
                    print(f"⚡ Parallel TMDB enhancement complete. Cache hit rate: {cache_stats['hit_rate_percent']}%")
                    print(f"📊 TMDB fetch success rate: {success_rate:.1f}% ({successful_fetches}/{successful_fetches + failed_fetches})")
        
        except Exception as e:
            if settings.ENHANCED_FEATURES_LOGGING:
                print(f"❌ Parallel enhancement failed: {e}")
            # Return movies without TMDB enhancement rather than crashing
            enhanced_movies = recommendations
        
        return enhanced_movies
    
    async def _fetch_tmdb_with_retry(self, session: aiohttp.ClientSession, tmdb_id: int, movie_title: str = "Unknown") -> Dict[str, Any]:
        """
        🛡️ ROBUST TMDB fetcher with intelligent retry logic
        
        Key improvements:
        - Exponential backoff for rate limits
        - Smart caching to avoid repeated failures
        - Quick timeout for hanging requests
        - Detailed error handling
        """
        
        # ============================================================
        # 🎯 CACHE CHECK FIRST (FASTEST PATH)
        # ============================================================
        
        cache_key = f"tmdb_{tmdb_id}"
        current_time = time.time()
        
        # Check cache first
        if (cache_key in self.tmdb_cache and 
            cache_key in self.cache_expiry and 
            current_time < self.cache_expiry[cache_key]):
            self.cache_hits += 1
            if settings.ENHANCED_FEATURES_LOGGING:
                print(f"🎯 Cache hit for TMDB ID {tmdb_id}")
            return self.tmdb_cache[cache_key]
        
        # Mark as cache miss
        self.cache_misses += 1
        if settings.ENHANCED_FEATURES_LOGGING:
            print(f"📡 Cache miss for TMDB ID {tmdb_id}, fetching...")
        
        # ============================================================
        # 🚀 FETCH WITH SMART RETRY LOGIC  
        # ============================================================
        
        url = f"{settings.TMDB_BASE_URL}/movie/{tmdb_id}"
        params = {
            "api_key": settings.TMDB_API_KEY,
            "language": "en-US"
        }
        
        max_retries = 3
        base_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                # Calculate exponential backoff delay
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))  # 0.5s, 1s, 2s
                    await asyncio.sleep(delay)
                    if settings.ENHANCED_FEATURES_LOGGING:
                        print(f"🔄 Retry {attempt}/{max_retries} for TMDB ID {tmdb_id} after {delay}s delay")
                
                # Make the request with individual timeout
                async with session.get(url, params=params, timeout=8) as response:  # 8 second timeout per request
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Cache successful response
                        self.tmdb_cache[cache_key] = data
                        self.cache_expiry[cache_key] = current_time + self.cache_duration
                        
                        return data
                    
                    elif response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 2))
                        if settings.ENHANCED_FEATURES_LOGGING:
                            print(f"⏱️ Rate limited for TMDB ID {tmdb_id}, waiting {retry_after}s")
                        await asyncio.sleep(min(retry_after, 5))  # Cap wait time at 5 seconds
                        continue
                        
                    elif response.status in [404, 400]:  # Not found or bad request
                        # Cache empty result to avoid retrying
                        self.tmdb_cache[cache_key] = {}
                        self.cache_expiry[cache_key] = current_time + 300  # Cache 404s for 5 minutes
                        return {}
                        
                    else:
                        if settings.ENHANCED_FEATURES_LOGGING:
                            print(f"⚠️ TMDB API error for {movie_title} (ID: {tmdb_id}): Status {response.status}")
                        
                        # Don't retry on client errors (4xx), only server errors (5xx)
                        if response.status < 500:
                            break
            
            except asyncio.TimeoutError:
                if settings.ENHANCED_FEATURES_LOGGING:
                    print(f"⏰ Timeout for TMDB ID {tmdb_id} on attempt {attempt + 1}")
                continue
                
            except aiohttp.ClientConnectorError as e:
                if settings.ENHANCED_FEATURES_LOGGING:
                    print(f"🔌 Connection error for TMDB ID {tmdb_id}: {e}")
                continue
                
            except Exception as e:
                if settings.ENHANCED_FEATURES_LOGGING:
                    print(f"❌ Unexpected error for TMDB ID {tmdb_id}: {e}")
                continue
        
        # All retries failed - cache empty result to avoid hammering the API
        if settings.ENHANCED_FEATURES_LOGGING:
            print(f"❌ All retries failed for TMDB ID {tmdb_id} ({movie_title})")
        
        self.tmdb_cache[cache_key] = {}
        self.cache_expiry[cache_key] = current_time + 60  # Cache failures for 1 minute
        return {}
    
    def _run_async_enhancement(self, recommendations: List[Dict]) -> List[Dict]:
        """Run async enhancement in thread to avoid blocking"""
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in a loop, run in thread pool
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._run_async_in_new_loop, recommendations)
                    return future.result(timeout=45)  # 45 second timeout
            except RuntimeError:
                # No event loop running, safe to create one
                return self._run_async_in_new_loop(recommendations)
        except Exception as e:
            print(f"❌ Async enhancement failed: {e}")
            return recommendations
    
    def _run_async_in_new_loop(self, recommendations: List[Dict]) -> List[Dict]:
        """Run async code in a new event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._enhance_movies_parallel(recommendations))
        finally:
            loop.close()
    