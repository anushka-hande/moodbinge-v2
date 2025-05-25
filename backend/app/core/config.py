import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MoodBinge"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "Mood-based movie recommendation system"
    
    # TMDB API configuration
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    
    # MovieLens data directory
    DATA_PATH: str = os.getenv("DATA_PATH", "data/ml-latest-small/")
    
    # API request settings
    REQUEST_TIMEOUT: int = 8
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 0.5
    RETRY_STATUS_FORCELIST: list = [429, 500, 502, 503, 504, 104]
    CONNECTION_POOL_SIZE: int = 8
    CONNECTION_POOL_MAXSIZE: int = 15
    
    # JWT Token settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./moodbinge.db")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-app.vercel.app",  # Update this with your Vercel URL
    ]
    
    # Add your custom domain when you get one
    if os.getenv("FRONTEND_URL"):
        BACKEND_CORS_ORIGINS.append(os.getenv("FRONTEND_URL"))
    
    # Production settings
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # ================================================================
    # 🆕 ENHANCED RECOMMENDATION FEATURES
    # ================================================================
    
    # Main feature toggle - START WITH FALSE FOR SAFETY
    USE_ENHANCED_RECOMMENDATIONS: bool = os.getenv("USE_ENHANCED_RECOMMENDATIONS", "false").lower() == "true"
    
    # Session management settings
    ENHANCED_SESSION_DURATION_HOURS: int = int(os.getenv("ENHANCED_SESSION_DURATION_HOURS", "24"))
    ENHANCED_MEMORY_SIZE: int = int(os.getenv("ENHANCED_MEMORY_SIZE", "1000"))
    
    # Randomization settings
    ENHANCED_RANDOMIZATION_STRENGTH: float = float(os.getenv("ENHANCED_RANDOMIZATION_STRENGTH", "0.25"))
    ENHANCED_RANDOMIZATION_SEED: int = int(os.getenv("ENHANCED_RANDOMIZATION_SEED", "42"))
    
    # Anti-repetition settings
    CROSS_MOOD_EXCLUSION_COUNT: int = int(os.getenv("CROSS_MOOD_EXCLUSION_COUNT", "3"))  # Movies to exclude from other moods
    GLOBAL_RECENT_EXCLUSION_COUNT: int = int(os.getenv("GLOBAL_RECENT_EXCLUSION_COUNT", "15"))  # Recent movies to avoid globally
    
    # Candidate pool settings
    CANDIDATE_POOL_MULTIPLIER: int = int(os.getenv("CANDIDATE_POOL_MULTIPLIER", "3"))  # Get N*3 candidates for variety
    MAX_CANDIDATE_POOL_SIZE: int = int(os.getenv("MAX_CANDIDATE_POOL_SIZE", "50"))  # Cap for performance
    
    # Diversity settings
    DIVERSITY_DECADE_PENALTY: float = float(os.getenv("DIVERSITY_DECADE_PENALTY", "0.8"))  # Penalty for same decade
    DIVERSITY_GENRE_PENALTY: float = float(os.getenv("DIVERSITY_GENRE_PENALTY", "0.9"))   # Penalty for same primary genre
    DIVERSITY_THRESHOLD: float = float(os.getenv("DIVERSITY_THRESHOLD", "0.7"))           # Minimum diversity score to accept
    
    # Logging and monitoring
    ENHANCED_FEATURES_LOGGING: bool = os.getenv("ENHANCED_FEATURES_LOGGING", "true").lower() == "true"
    TRACK_RECOMMENDATION_METRICS: bool = os.getenv("TRACK_RECOMMENDATION_METRICS", "false").lower() == "true"

    # TMDB caching settings
    TMDB_CACHE_DURATION_SECONDS: int = int(os.getenv("TMDB_CACHE_DURATION_SECONDS", "7200"))  # INCREASED to 2 hours
    TMDB_CACHE_MAX_SIZE: int = int(os.getenv("TMDB_CACHE_MAX_SIZE", "10000"))        # INCREASED from 5000
    TMDB_CACHE_404_DURATION: int = int(os.getenv("TMDB_CACHE_404_DURATION", "300"))  # NEW: Cache 404s for 5 min
    
    
    # Parallel processing settings
    TMDB_PARALLEL_CONNECTIONS: int = int(os.getenv("TMDB_PARALLEL_CONNECTIONS", "5"))
    TMDB_CONNECTION_TIMEOUT: int = int(os.getenv("TMDB_CONNECTION_TIMEOUT", "20"))
    TMDB_BATCH_SIZE: int = int(os.getenv("TMDB_BATCH_SIZE", "5"))    # NEW: Process 5 at a time
    
    # Preloading settings
    TMDB_PRELOAD_SIZE: int = int(os.getenv("TMDB_PRELOAD_SIZE", "2000"))   # INCREASED from 1000
    TMDB_PRELOAD_ON_STARTUP: bool = os.getenv("TMDB_PRELOAD_ON_STARTUP", "true").lower() == "true"

    TMDB_KEEPALIVE_TIMEOUT: int = 30
    TMDB_ENABLE_COMPRESSION: bool = True
    TMDB_FORCE_CONNECTION_REUSE: bool = True
    
    # Performance logging
    PERFORMANCE_LOGGING: bool = os.getenv("PERFORMANCE_LOGGING", "true").lower() == "true"

settings = Settings()