# backend/app/core/hybrid_recommender.py

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple

class HybridRecommender:
    """
    Hybrid recommender that combines mood-based, collaborative filtering,
    and popularity-based recommendations
    """
    
    def __init__(self, mood_recommender, collaborative_recommender, movies_df):
        """
        Initialize the hybrid recommender
        
        Args:
            mood_recommender: Mood-based recommender instance
            collaborative_recommender: Collaborative filtering recommender instance
            movies_df: DataFrame containing movie information
        """
        self.mood_recommender = mood_recommender
        self.collaborative_recommender = collaborative_recommender
        self.movies_df = movies_df
        
    def get_recommendations(self, 
                           mood: str, 
                           user_id: int = None, 
                           n: int = 10, 
                           weights: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        Get hybrid recommendations combining mood-based and collaborative filtering
        
        Args:
            mood (str): Mood category for recommendations
            user_id (int, optional): User ID for personalization
            n (int): Number of recommendations to return
            weights (dict, optional): Custom weights for each recommendation type
                e.g., {'mood': 0.6, 'collaborative': 0.3, 'popularity': 0.1}
                
        Returns:
            list: List of recommended movies with scores
        """
        # Default weights if not provided
        if weights is None:
            if user_id is not None:
                # If we have a user, give more weight to collaborative filtering
                weights = {'mood': 0.5, 'collaborative': 0.4, 'popularity': 0.1}
            else:
                # For anonymous users, rely more on mood-based
                weights = {'mood': 0.7, 'collaborative': 0.0, 'popularity': 0.3}
        
        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        # Get recommendations from each approach
        
        # 1. Mood-based recommendations
        mood_recs = self.mood_recommender.get_recommendations(mood, n=n*2)
        mood_scores = {
            int(movie['movieId']): self._normalize_score(movie['score'])
            for movie in mood_recs
        }
        
        # 2. Collaborative filtering recommendations (if user_id provided)
        collab_scores = {}
        if user_id is not None and weights['collaborative'] > 0:
            try:
                collab_recs = self.collaborative_recommender.get_recommendations_for_user(
                    user_id, n=n*2
                )
                collab_scores = {
                    movie_id: self._normalize_score(score) 
                    for movie_id, score in collab_recs
                }
            except Exception as e:
                print(f"Error getting collaborative recommendations: {e}")
                # If collaborative filtering fails, shift weight to mood-based
                weights['mood'] += weights['collaborative']
                weights['collaborative'] = 0.0
        
        # 3. Popularity-based recommendations (fallback)
        popular_recs = self._get_popular_movies(n*2)
        popularity_scores = {
            movie_id: self._normalize_score(score)
            for movie_id, score in popular_recs
        }
        
        # Combine all movie IDs from the different recommendation sources
        all_movie_ids = set(list(mood_scores.keys()) + 
                           list(collab_scores.keys()) + 
                           list(popularity_scores.keys()))
        
        # Calculate combined scores
        combined_scores = {}
        for movie_id in all_movie_ids:
            # Get individual scores (default to 0 if not recommended by a method)
            mood_score = mood_scores.get(movie_id, 0.0)
            collab_score = collab_scores.get(movie_id, 0.0)
            popularity_score = popularity_scores.get(movie_id, 0.0)
            
            # Calculate weighted score
            weighted_score = (
                weights['mood'] * mood_score +
                weights['collaborative'] * collab_score +
                weights['popularity'] * popularity_score
            )
            
            combined_scores[movie_id] = weighted_score
        
        # Sort by combined score
        sorted_movies = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Take top n
        top_movies = sorted_movies[:n]
        
        # Convert to full movie objects with details
        results = []
        for movie_id, score in top_movies:
            # Find movie in DataFrame
            movie_row = self.movies_df[self.movies_df['movieId'] == movie_id]
            if len(movie_row) > 0:
                movie_data = movie_row.iloc[0].to_dict()
                movie_data['score'] = float(score)
                results.append(movie_data)
        
        return results
    
    def _normalize_score(self, score: float) -> float:
        """Normalize score to 0-1 range"""
        # Basic min-max scaling assuming scores are typically 0-5
        return min(max(score / 5.0, 0.0), 1.0)
    
    def _get_popular_movies(self, n: int = 10) -> List[Tuple[int, float]]:
        """Get popular movies based on number of ratings and average rating"""
        # Use a simple metric based on ratings data in the movies DataFrame
        if 'num_ratings' in self.movies_df.columns and 'avg_rating' in self.movies_df.columns:
            # Calculate a popularity score
            # This balances average rating with number of ratings
            self.movies_df['popularity'] = (
                self.movies_df['avg_rating'] * 0.7 + 
                np.log1p(self.movies_df['num_ratings']) * 0.3
            )
            
            # Sort by popularity (descending)
            popular_movies = self.movies_df.sort_values('popularity', ascending=False)
            
            # Return top n movie IDs with their scores
            return [
                (int(row['movieId']), float(row['popularity']))
                for _, row in popular_movies.head(n).iterrows()
                if 'movieId' in row
            ]
        else:
            # Fallback if rating columns don't exist
            return []
    
    def get_personalized_recommendations(self, 
                                        user_id: int, 
                                        n: int = 10) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations for a user (without mood filtering)
        
        Args:
            user_id (int): User ID
            n (int): Number of recommendations
            
        Returns:
            list: List of recommended movies
        """
        # For personalized recs, use mostly collaborative filtering
        weights = {'mood': 0.3, 'collaborative': 0.6, 'popularity': 0.1}
        
        # Pick a neutral mood as a baseline
        neutral_mood = "tranquil_haven"  # This could be configured based on user preference
        
        return self.get_recommendations(neutral_mood, user_id, n, weights)