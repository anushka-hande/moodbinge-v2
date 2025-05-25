# backend/app/core/smart_randomizer.py
import hashlib
import numpy as np
from datetime import datetime
from typing import List, Dict

class SmartRandomizer:
    """Adds controlled randomization while maintaining relevance"""
    
    def __init__(self, base_seed=None):
        self.base_seed = base_seed or int(datetime.now().timestamp())
    
    def get_session_random_state(self, session_id: str):
        """Get consistent random state for a session"""
        session_seed = int(hashlib.md5(f"{self.base_seed}_{session_id}".encode()).hexdigest()[:8], 16)
        return np.random.RandomState(session_seed)
    
    def add_smart_randomization(self, candidates: List[Dict], session_id: str, 
                               randomization_strength: float = 0.25) -> List[Dict]:
        """Add controlled randomization to candidate movies"""
        if not candidates or not session_id:
            return candidates
        
        rng = self.get_session_random_state(session_id)
        
        # Add randomization factors to each candidate
        for candidate in candidates:
            # Base score preservation (75-90% of original score maintained)
            preservation_factor = 0.75 + (randomization_strength * 0.15)
            
            # Random boost (0-25% bonus based on randomization strength)
            random_boost = rng.random() * randomization_strength
            
            # Temporal variety (slight preference for different decades)
            decade_boost = 0
            if 'year' in candidate and candidate['year']:
                decade = (candidate['year'] // 10) * 10
                # Small random preference for different decades
                if rng.random() < 0.3:  # 30% chance
                    decade_boost = rng.random() * 0.08  # Up to 8% boost
            
            # Apply randomization
            original_score = candidate.get('score', 1.0)
            randomized_score = (original_score * preservation_factor) + (original_score * random_boost) + decade_boost
            
            candidate['randomized_score'] = randomized_score
            candidate['original_score'] = original_score
            candidate['randomization_applied'] = True
        
        return candidates