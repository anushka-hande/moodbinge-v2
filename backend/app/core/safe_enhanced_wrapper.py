# backend/app/core/safe_enhanced_wrapper.py
import pandas as pd
from typing import List, Dict, Optional
from .session_manager import SessionBasedAntiRepetition
from .smart_randomizer import SmartRandomizer
from .mood_scorer_enhanced import EnhancedMoodScorer

class SafeEnhancedWrapper:
    """
    Safe wrapper around your existing EnhancedMoodRecommender
    Adds new features without modifying original code
    """
    
    def __init__(self, original_recommender, mood_mapping):
        """
        Initialize with your existing recommender instance
        
        Args:
            original_recommender: Your existing EnhancedMoodRecommender instance
            mood_mapping: Your mood mapping dictionary
        """
        # Your existing system (completely untouched)
        self.original_recommender = original_recommender
        self.mood_mapping = mood_mapping
        
        # New enhancement components
        self.session_manager = SessionBasedAntiRepetition()
        self.randomizer = SmartRandomizer()
        self.enhanced_scorer = EnhancedMoodScorer()
        
        # Initialize enhanced scorer with mood mapping
        self.enhanced_scorer.set_mood_mapping(mood_mapping)
        
        print("SafeEnhancedWrapper initialized - original system preserved")
    
    def get_recommendations(self, mood: str, n: int = 10, 
                          session_id: Optional[str] = None, 
                          use_enhancements: bool = True) -> List[Dict]:
        """
        Get recommendations with optional enhancements
        
        Args:
            mood: Mood category
            n: Number of recommendations
            session_id: Optional session ID for anti-repetition
            use_enhancements: If False, uses your original system exactly
        
        Returns:
            List of movie dictionaries
        """
        
        # FALLBACK: Use your original system if requested
        if not use_enhancements or not session_id:
            print("Using original recommendation system")
            original_results = self.original_recommender.get_recommendations(mood, n)
            return self._convert_to_list_format(original_results)
        
        try:
            print(f"Using enhanced system for mood: {mood}, session: {session_id}")
            return self._get_enhanced_recommendations(mood, n, session_id)
            
        except Exception as e:
            print(f"Enhanced system failed, falling back to original: {e}")
            # SAFETY: Always fallback to your proven system
            original_results = self.original_recommender.get_recommendations(mood, n)
            return self._convert_to_list_format(original_results)
    
    def _get_enhanced_recommendations(self, mood: str, n: int, session_id: str) -> List[Dict]:
        """Apply all enhancements safely"""
        
        # Step 1: Get excluded movies (anti-repetition)
        excluded_movies = self.session_manager.get_excluded_movies(session_id, mood)
        print(f"Excluding {len(excluded_movies)} movies for anti-repetition")
        
        # Step 2: Get larger candidate pool from your original system
        # Request 3x more to have variety for filtering and randomization
        candidate_pool_size = min(n * 3, 50)  # Cap at 50 to avoid performance issues
        
        # Use your original system to get candidates
        original_candidates = self.original_recommender.get_recommendations(mood, candidate_pool_size)
        candidates = self._convert_to_list_format(original_candidates)
        
        # Step 3: Filter out excluded movies
        available_candidates = [
            movie for movie in candidates 
            if movie.get('movieId') not in excluded_movies
        ]
        
        print(f"After exclusion: {len(available_candidates)} available candidates")
        
        # Step 4: If not enough candidates, get more from original system
        if len(available_candidates) < n:
            print("Not enough candidates after exclusion, getting more from original system")
            # Allow some repetition if absolutely necessary
            available_candidates = candidates[:n*2]
        
        # Step 5: Apply enhanced mood-specific scoring
        for candidate in available_candidates:
            original_score = candidate.get('score', 1.0)
            enhanced_score = self.enhanced_scorer.enhance_movie_score(
                candidate, mood, original_score
            )
            candidate['enhanced_score'] = enhanced_score
        
        # Step 6: Sort by enhanced score
        available_candidates.sort(key=lambda x: x.get('enhanced_score', 0), reverse=True)
        
        # Step 7: Apply smart randomization
        randomized_candidates = self.randomizer.add_smart_randomization(
            available_candidates[:n*2], session_id, randomization_strength=0.25
        )
        
        # Step 8: Sort by randomized score and apply final diversity selection
        randomized_candidates.sort(key=lambda x: x.get('randomized_score', x.get('enhanced_score', 0)), reverse=True)
        
        # Step 9: Select final recommendations with diversity
        final_recommendations = self._select_diverse_final(randomized_candidates, n)
        
        # Step 10: Record recommendations to prevent future repetition
        movie_ids = [rec['movieId'] for rec in final_recommendations]
        self.session_manager.add_recommendations(session_id, mood, movie_ids)
        
        print(f"Selected {len(final_recommendations)} final recommendations")
        return final_recommendations
    
    def _select_diverse_final(self, candidates: List[Dict], n: int) -> List[Dict]:
        """Apply diversity selection to final candidates"""
        selected = []
        used_decades = set()
        used_primary_genres = set()
        
        for candidate in candidates:
            if len(selected) >= n:
                break
            
            # Check diversity factors
            year = candidate.get('year')
            decade = (year // 10) * 10 if year else None
            
            genres = candidate.get('genres', '')
            primary_genre = genres.split('|')[0] if genres else None
            
            # Diversity penalty
            diversity_penalty = 1.0
            
            if decade and decade in used_decades:
                diversity_penalty *= 0.8  # Slight penalty for same decade
            
            if primary_genre and primary_genre in used_primary_genres:
                diversity_penalty *= 0.9  # Slight penalty for same primary genre
            
            # Apply diversity penalty to score
            final_score = candidate.get('randomized_score', candidate.get('enhanced_score', 0)) * diversity_penalty
            candidate['final_score'] = final_score
            
            # Select if good enough or if we need to fill remaining slots
            remaining_slots = n - len(selected)
            if diversity_penalty > 0.7 or remaining_slots >= len(candidates) - candidates.index(candidate):
                selected.append(candidate)
                if decade:
                    used_decades.add(decade)
                if primary_genre:
                    used_primary_genres.add(primary_genre)
        
        return selected
    
    def _convert_to_list_format(self, df_or_list) -> List[Dict]:
        """Convert DataFrame to List[Dict] format safely"""
        if isinstance(df_or_list, pd.DataFrame):
            return df_or_list.to_dict('records')
        elif isinstance(df_or_list, list):
            return df_or_list
        else:
            print(f"Unexpected format: {type(df_or_list)}")
            return []
    
    def get_original_recommendations(self, mood: str, n: int = 10) -> List[Dict]:
        """Direct access to your original system"""
        original_results = self.original_recommender.get_recommendations(mood, n)
        return self._convert_to_list_format(original_results)
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics about a session"""
        if session_id not in self.session_manager.movie_history:
            return {"session_found": False}
        
        session_data = self.session_manager.movie_history[session_id]
        return {
            "session_found": True,
            "moods_requested": list(session_data['moods'].keys()),
            "total_movies_seen": sum(len(movies) for movies in session_data['moods'].values()),
            "last_activity": session_data['timestamp'].isoformat()
        }