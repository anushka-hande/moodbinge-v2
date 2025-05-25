# backend/app/core/session_manager.py
from datetime import datetime, timedelta
from typing import Dict, List, Set
import hashlib

class SessionBasedAntiRepetition:
    """Tracks movies shown to prevent repetition - completely independent"""
    
    def __init__(self, session_duration_hours=24, max_memory_size=1000):
        self.session_duration = timedelta(hours=session_duration_hours)
        self.max_memory_size = max_memory_size
        self.movie_history = {}  # {session_id: {mood: [movie_ids], timestamp}}
        self.global_recent = []  # Recent movies across all sessions
    
    def generate_session_id(self, user_identifier=None):
        """Generate session ID based on user or time"""
        if user_identifier:
            return hashlib.md5(f"{user_identifier}_{datetime.now().date()}".encode()).hexdigest()[:8]
        else:
            # Anonymous session based on hour blocks
            return hashlib.md5(f"anon_{datetime.now().strftime('%Y%m%d_%H')}".encode()).hexdigest()[:8]
    
    def add_recommendations(self, session_id: str, mood: str, movie_ids: List[int]):
        """Record recommended movies for this session and mood"""
        current_time = datetime.now()
        
        if session_id not in self.movie_history:
            self.movie_history[session_id] = {'timestamp': current_time, 'moods': {}}
        
        # Update mood history
        if mood not in self.movie_history[session_id]['moods']:
            self.movie_history[session_id]['moods'][mood] = []
        
        self.movie_history[session_id]['moods'][mood].extend(movie_ids)
        self.movie_history[session_id]['timestamp'] = current_time
        
        # Add to global recent list
        self.global_recent.extend(movie_ids)
        
        # Cleanup old sessions and limit memory
        self._cleanup_old_data()
    
    def get_excluded_movies(self, session_id: str, mood: str) -> Set[int]:
        """Get movies to exclude for this session and mood"""
        excluded = set()
        
        if session_id in self.movie_history:
            session_data = self.movie_history[session_id]
            
            # Exclude movies from THIS mood (prevent immediate repetition)
            if mood in session_data['moods']:
                excluded.update(session_data['moods'][mood])
            
            # Exclude movies from OTHER moods in this session (reduce cross-mood repetition)
            for other_mood, movies in session_data['moods'].items():
                if other_mood != mood:
                    # Only exclude most recent movies from other moods
                    excluded.update(movies[-3:])  # Last 3 movies from each other mood
        
        # Add some globally recent movies to encourage variety
        excluded.update(self.global_recent[-15:])  # Last 15 globally recommended movies
        
        return excluded
    
    def _cleanup_old_data(self):
        """Remove old sessions and limit memory usage"""
        current_time = datetime.now()
        
        # Remove expired sessions
        expired_sessions = []
        for session_id, data in self.movie_history.items():
            if current_time - data['timestamp'] > self.session_duration:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.movie_history[session_id]
        
        # Limit global recent list
        if len(self.global_recent) > self.max_memory_size:
            self.global_recent = self.global_recent[-self.max_memory_size//2:]