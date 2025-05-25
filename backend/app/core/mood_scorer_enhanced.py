# backend/app/core/mood_scorer_enhanced.py
from datetime import datetime
from typing import Dict, List

class EnhancedMoodScorer:
    """Enhanced mood-specific scoring with tag weights"""
    
    def __init__(self):
        # Mood-specific weights (including tag importance)
        self.mood_weights = {
            'euphoria_wave': {
                'genre_weight': 0.5,
                'rating_weight': 0.15,
                'popularity_weight': 0.2,
                'tag_weight': 0.15,
                'year_bias': 0.05  # Slight preference for newer
            },
            'victory_high': {
                'genre_weight': 0.4,
                'rating_weight': 0.3,
                'popularity_weight': 0.15,
                'tag_weight': 0.15,
                'year_bias': 0.1   # Prefer recent victories
            },
            'fury_awakened': {
                'genre_weight': 0.6,
                'rating_weight': 0.15,
                'popularity_weight': 0.05,
                'tag_weight': 0.2,
                'year_bias': 0.0
            },
            'phantom_fear': {
                'genre_weight': 0.7,
                'rating_weight': 0.05,
                'popularity_weight': 0.05,
                'tag_weight': 0.2,
                'year_bias': 0.0
            },
            'tranquil_haven': {
                'genre_weight': 0.3,
                'rating_weight': 0.4,
                'popularity_weight': 0.15,
                'tag_weight': 0.15,
                'year_bias': 0.0
            },
            'heartfelt_harmony': {
                'genre_weight': 0.4,
                'rating_weight': 0.25,
                'popularity_weight': 0.15,
                'tag_weight': 0.2,
                'year_bias': 0.1   # Prefer recent romance
            },
            'somber_ruminations': {
                'genre_weight': 0.3,
                'rating_weight': 0.4,
                'popularity_weight': 0.05,
                'tag_weight': 0.25,
                'year_bias': 0.0
            },
            'cosmic_emptiness': {
                'genre_weight': 0.5,
                'rating_weight': 0.2,
                'popularity_weight': 0.05,
                'tag_weight': 0.25,
                'year_bias': 0.0
            },
            'timeworn_echoes': {
                'genre_weight': 0.3,
                'rating_weight': 0.3,
                'popularity_weight': 0.15,
                'tag_weight': 0.25,
                'year_bias': -0.15  # Strong preference for older films
            },
            'wonder_hunt': {
                'genre_weight': 0.4,
                'rating_weight': 0.3,
                'popularity_weight': 0.05,
                'tag_weight': 0.25,
                'year_bias': 0.05
            }
        }
        
        # Mood-to-keywords mapping for tag matching
        self.mood_keywords = {}
    
    def set_mood_mapping(self, mood_mapping):
        """Initialize tag keywords from mood mapping"""
        for mood, details in mood_mapping.items():
            keywords = set()
            
            # Add tags
            for tag in details.get('tags', []):
                keywords.add(tag.lower().strip())
            
            # Add TMDB keywords
            for keyword in details.get('tmdb_keywords', []):
                keywords.add(keyword.lower().strip())
            
            self.mood_keywords[mood] = keywords
    
    def calculate_tag_score(self, movie_tags, mood):
        """Calculate tag matching score for a movie"""
        if mood not in self.mood_keywords or not movie_tags:
            return 0.0
        
        mood_keywords = self.mood_keywords[mood]
        
        # Handle different tag formats
        if isinstance(movie_tags, list):
            tags = [tag.lower().strip() for tag in movie_tags]
        elif isinstance(movie_tags, str):
            tags = [tag.strip().lower() for tag in movie_tags.split(',')]
        else:
            return 0.0
        
        # Count matches
        matches = sum(1 for tag in tags if tag in mood_keywords)
        
        # Convert matches to score (diminishing returns)
        if matches == 0:
            return 0.0
        elif matches == 1:
            return 0.4
        elif matches == 2:
            return 0.7
        elif matches == 3:
            return 0.9
        else:
            return min(1.0, 0.9 + 0.05 * (matches - 3))
    
    def enhance_movie_score(self, movie_data: Dict, mood: str, base_score: float) -> float:
        """Enhance movie score with mood-specific factors"""
        if mood not in self.mood_weights:
            return base_score
        
        weights = self.mood_weights[mood]
        
        # Start with base genre score
        enhanced_score = base_score * weights['genre_weight']
        
        # Add rating factor
        rating = movie_data.get('rating', movie_data.get('avg_rating', 0))
        if rating:
            rating_factor = rating / 5.0
            enhanced_score += rating_factor * weights['rating_weight']
        
        # Add popularity factor with diminishing returns
        popularity = movie_data.get('popularity', movie_data.get('num_ratings', 0))
        if popularity:
            import numpy as np
            pop_factor = min(np.log1p(popularity) / 8.0, 1.0)
            enhanced_score += pop_factor * weights['popularity_weight']
        
        # Add tag matching factor
        tags = movie_data.get('tags', movie_data.get('clean_tag'))
        tag_score = self.calculate_tag_score(tags, mood)
        enhanced_score += tag_score * weights['tag_weight']
        
        # Year adjustment
        year = movie_data.get('year')
        if year and weights['year_bias'] != 0:
            current_year = datetime.now().year
            years_old = current_year - year
            year_factor = weights['year_bias'] * (years_old / 40.0)  # Normalize by 40 years
            enhanced_score += year_factor
        
        return max(0.1, enhanced_score)  # Ensure positive score