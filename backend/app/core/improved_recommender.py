from app.core.base_recommender import MoodBasedRecommender
import pandas as pd
import numpy as np

class ImprovedMoodRecommender(MoodBasedRecommender):
    """Enhanced mood-based recommender with improved diversity and balance"""
    
    def calculate_movie_mood_score(self, movie, mood):
        """
        Enhanced scoring function with better balance
        """
        # Get mood details
        mood_details = self.mood_mapping[mood]
        
        # Get base score from original method
        base_score = self._calculate_genre_score(movie, mood_details)
        
        # Skip movies with poor genre match
        if base_score <= 0.2:
            return 0
        
        # Add tag matching if available
        if self.has_tags and isinstance(movie.get('clean_tag', None), list):
            base_score = self._enhance_with_tags(base_score, movie, mood)
        
        # Get movie metadata
        year = movie.get('year')
        popularity = movie.get('num_ratings', 0)
        rating = movie.get('avg_rating', 0)
        
        # Apply modifiers to address evaluation issues
        final_score = base_score
        
        # 1. REDUCE POPULARITY BIAS
        # Apply reverse logarithmic scaling to popularity
        # This will significantly reduce the impact of very popular movies
        if popularity > 0:
            # Convert linear popularity to logarithmic scale with diminishing returns
            pop_factor = np.log1p(popularity) / np.log1p(100)  # Normalize to log(101)
            pop_factor = min(pop_factor, 1.0)  # Cap at 1.0
            
            # Apply INVERSE popularity boost for less popular movies
            # Movies with fewer ratings get MORE of a boost
            inverse_pop_factor = 1 - (pop_factor * 0.5)  # Scale down the effect
            final_score *= (1 + inverse_pop_factor * 0.3)
        
        # 2. ENHANCE TEMPORAL DIVERSITY
        if year and not pd.isna(year):
            # Adjust scores to boost underrepresented decades
            decade = (year // 10) * 10
            
            # Boost older and underrepresented movies
            if decade < 1970:
                final_score *= 1.4  # Strong boost for pre-1970s
            elif decade < 1990:
                final_score *= 1.2  # Moderate boost for 70s and 80s
                
            # Slightly penalize overrepresented 2000s
            if 2000 <= decade <= 2009:
                final_score *= 0.85
        
        # 3. BOOST CATALOG COVERAGE
        # Randomly boost some lower-ranked movies to improve exploration
        if np.random.random() < 0.2:  # 20% chance
            # Apply a small random boost to encourage catalog exploration
            final_score *= (1 + (np.random.random() * 0.3))
        
        # 4. GENRE BALANCING
        # Slightly reduce the impact of drama to improve genre diversity
        if 'Drama' in movie['genres']:
            # Apply a small penalty to drama to prevent overrepresentation
            drama_penalty = 0.15 if 'Drama' in mood_details['primary_genres'] else 0.25
            final_score *= (1 - drama_penalty)
        
        # 5. APPLY QUALITY FACTOR (Rating still matters, but less than before)
        if rating > 0:
            # Convert 0-5 scale to 0-1
            rating_factor = rating / 5.0
            # Apply a moderate quality boost
            final_score *= (1 + (rating_factor * 0.3))
        
        return final_score
    
    def get_recommendations(self, mood, n=10):
        """
        Get recommendations with improved diversity mechanisms
        """
        if mood not in self.mood_mapping:
            raise ValueError(f"Unknown mood: {mood}")
            
        # Get a larger pool of candidates to enhance diversity
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
                    'score': score
                })
        
        # Sort candidates by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply diversity-aware selection
        selected = []
        decades_count = {}  # Track selected decades
        genres_count = {}   # Track selected genres
        
        # Take top 20% based purely on score
        top_count = max(1, int(n * 0.2))
        selected.extend(candidates[:top_count])
        candidates = candidates[top_count:]
        
        # Update tracking counts
        for movie in selected:
            # Track decade
            if pd.notna(movie['year']):
                decade = (movie['year'] // 10) * 10
                decades_count[decade] = decades_count.get(decade, 0) + 1
            
            # Track genres
            for genre in movie['genres'].split('|'):
                genres_count[genre] = genres_count.get(genre, 0) + 1
        
        # Fill remaining slots with diversity in mind
        while candidates and len(selected) < n:
            # Prioritize decade diversity first
            decade_diverse_candidates = []
            
            for candidate in candidates[:min(30, len(candidates))]:
                if pd.notna(candidate['year']):
                    decade = (candidate['year'] // 10) * 10
                    # Prioritize decades with fewer selections
                    if decade not in decades_count or decades_count[decade] < 2:
                        decade_diverse_candidates.append(candidate)
            
            # If we found decade-diverse candidates, prioritize them
            if decade_diverse_candidates:
                # Now look for genre diversity among decade-diverse candidates
                genre_diverse = None
                for candidate in decade_diverse_candidates:
                    # Count how many new genres this would add
                    new_genres = 0
                    for genre in candidate['genres'].split('|'):
                        if genre not in genres_count or genres_count[genre] < 2:
                            new_genres += 1
                    
                    if new_genres > 0:
                        genre_diverse = candidate
                        break
                
                # Select the candidate with genre diversity, or the first decade-diverse one
                next_selection = genre_diverse or decade_diverse_candidates[0]
            else:
                # If no decade diversity available, just take the highest scored remaining
                next_selection = candidates[0]
            
            # Add to selected list and remove from candidates
            selected.append(next_selection)
            candidates.remove(next_selection)
            
            # Update tracking counts
            if pd.notna(next_selection['year']):
                decade = (next_selection['year'] // 10) * 10
                decades_count[decade] = decades_count.get(decade, 0) + 1
            
            for genre in next_selection['genres'].split('|'):
                genres_count[genre] = genres_count.get(genre, 0) + 1
        
        # Return as DataFrame
        return pd.DataFrame(selected)