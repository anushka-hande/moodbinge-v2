# backend/app/core/collaborative_recommender.py

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix

class CollaborativeFilteringRecommender:
    """
    Collaborative filtering recommendation system based on user-item interactions
    """
    
    def __init__(self, ratings_path, movies_path, min_ratings=5):
        """
        Initialize the collaborative filtering recommender
        
        Args:
            ratings_path (str): Path to ratings CSV file
            movies_path (str): Path to movies CSV file
            min_ratings (int): Minimum number of ratings for a user to be included
        """
        self.min_ratings = min_ratings
        self.ratings = pd.read_csv(ratings_path)
        self.movies = pd.read_csv(movies_path)
        
        # Filter users with min_ratings
        user_counts = self.ratings['userId'].value_counts()
        self.active_users = user_counts[user_counts >= min_ratings].index
        
        # Create user-item matrix
        self._create_matrix()
        
        # Build similarity matrices
        self._build_similarity_matrices()
        
    def _create_matrix(self):
        """Create the user-item matrix for collaborative filtering"""
        # Filter to only include active users
        filtered_ratings = self.ratings[self.ratings['userId'].isin(self.active_users)]
        
        # Create pivot table: rows=users, columns=movies, values=ratings
        self.user_item_matrix = filtered_ratings.pivot(
            index='userId', 
            columns='movieId', 
            values='rating'
        ).fillna(0)
        
        # Create mappings between matrix positions and IDs
        self.user_to_idx = {user: i for i, user in enumerate(self.user_item_matrix.index)}
        self.idx_to_user = {i: user for user, i in self.user_to_idx.items()}
        
        self.movie_to_idx = {movie: i for i, movie in enumerate(self.user_item_matrix.columns)}
        self.idx_to_movie = {i: movie for movie, i in self.movie_to_idx.items()}
        
        # Convert to sparse matrix for efficiency with large datasets
        self.matrix_sparse = csr_matrix(self.user_item_matrix.values)
        
    def _build_similarity_matrices(self):
        """Build user-user and item-item similarity matrices"""
        # Item-Item similarity matrix (movie similarities)
        # Transpose to get movie-movie similarity
        item_sparse = self.matrix_sparse.T
        
        # Calculate cosine similarity between movies
        # This creates a matrix where each cell [i,j] is the 
        # similarity between movie i and movie j
        self.item_similarity = cosine_similarity(item_sparse)
        
        # User-User similarity matrix (user similarities)
        # Calculate cosine similarity between users
        self.user_similarity = cosine_similarity(self.matrix_sparse)
    
    def get_similar_movies(self, movie_id, n=10):
        """
        Get movies similar to the given movie based on collaborative filtering
        
        Args:
            movie_id (int): MovieID to find similar movies for
            n (int): Number of similar movies to return
            
        Returns:
            list: List of (movie_id, similarity_score) tuples
        """
        # Check if movie exists in our matrix
        if movie_id not in self.movie_to_idx:
            return []
            
        # Get movie index
        idx = self.movie_to_idx[movie_id]
        
        # Get similarity scores for this movie with all others
        similarity_scores = self.item_similarity[idx]
        
        # Get indices of most similar movies (excluding itself)
        similar_indices = np.argsort(similarity_scores)[::-1][1:n+1]
        
        # Convert indices back to movie IDs and include similarity score
        similar_movies = [
            (self.idx_to_movie[i], float(similarity_scores[i])) 
            for i in similar_indices
        ]
        
        return similar_movies
    
    def get_recommendations_for_user(self, user_id, n=10, exclude_rated=True):
        """
        Get movie recommendations for a specific user
        
        Args:
            user_id (int): User ID to get recommendations for
            n (int): Number of recommendations to return
            exclude_rated (bool): Whether to exclude movies the user has already rated
            
        Returns:
            list: List of (movie_id, predicted_rating) tuples
        """
        # Check if user exists in our matrix
        if user_id not in self.user_to_idx:
            # New user - return popular movies
            return self._get_popular_movies(n)
            
        # Get user's ratings
        user_idx = self.user_to_idx[user_id]
        user_ratings = self.user_item_matrix.iloc[user_idx].values
        
        # Find similar users
        user_similarities = self.user_similarity[user_idx]
        
        # Calculate predicted ratings for all movies
        # This is a weighted average of ratings from similar users
        weighted_ratings = np.zeros(len(self.movie_to_idx))
        similarity_sums = np.zeros(len(self.movie_to_idx))
        
        # For each user
        for other_idx, similarity in enumerate(user_similarities):
            # Skip self or users with zero similarity
            if other_idx == user_idx or similarity <= 0:
                continue
                
            # Get other user's ratings
            other_ratings = self.user_item_matrix.iloc[other_idx].values
            
            # For each movie
            for movie_idx, rating in enumerate(other_ratings):
                if rating > 0:  # If the user has rated this movie
                    weighted_ratings[movie_idx] += similarity * rating
                    similarity_sums[movie_idx] += similarity
        
        # Calculate predicted ratings (avoiding division by zero)
        predicted_ratings = np.zeros(len(self.movie_to_idx))
        for i in range(len(predicted_ratings)):
            if similarity_sums[i] > 0:
                predicted_ratings[i] = weighted_ratings[i] / similarity_sums[i]
        
        # Create movie_id, predicted_rating pairs
        movie_ratings = list(enumerate(predicted_ratings))
        
        # Filter out movies the user has already rated if requested
        if exclude_rated:
            rated_indices = np.where(user_ratings > 0)[0]
            movie_ratings = [(idx, rating) for idx, rating in movie_ratings if idx not in rated_indices]
        
        # Sort by predicted rating (descending)
        movie_ratings.sort(key=lambda x: x[1], reverse=True)
        
        # Convert indices to movie IDs and take top n
        recommendations = [
            (self.idx_to_movie[idx], float(rating))
            for idx, rating in movie_ratings[:n]
            if rating > 0  # Only include positive predictions
        ]
        
        return recommendations
    
    def _get_popular_movies(self, n=10):
        """Get most popular movies based on number of ratings and average rating"""
        # Calculate movie popularity
        movie_stats = self.ratings.groupby('movieId').agg(
            avg_rating=('rating', 'mean'),
            num_ratings=('rating', 'count')
        ).reset_index()
        
        # Calculate a popularity score
        # This balances average rating with number of ratings
        movie_stats['popularity'] = (
            movie_stats['avg_rating'] * 0.7 + 
            np.log1p(movie_stats['num_ratings']) * 0.3
        )
        
        # Sort by popularity (descending)
        popular_movies = movie_stats.sort_values('popularity', ascending=False)
        
        # Return top n movie IDs with their scores
        return [
            (row['movieId'], float(row['popularity']))
            for _, row in popular_movies.head(n).iterrows()
        ]