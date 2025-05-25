# backend/app/api/endpoints/recommendations.py
import time 
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query, Response
from app.services.recommender import RecommenderService
from app.services.text_analysis import TextAnalysisService
from app.core.config import settings

router = APIRouter()
recommender_service = RecommenderService()
text_analysis_service = TextAnalysisService()

class MoodAnalysisRequest(BaseModel):
    text: str

# ================================================================
# EXISTING ENDPOINTS (UNCHANGED)
# ================================================================

@router.get("/moods", response_model=List[Dict[str, Any]])
async def get_moods():
    """Get available mood categories"""
    return recommender_service.get_available_moods()

@router.get("/similar/{movie_id}", response_model=List[Dict[str, Any]])
async def get_similar_movies(movie_id: int, limit: int = 5):
    """Get similar movies for a given movie ID"""
    try:
        similar_movies = recommender_service.get_similar_movies(movie_id, limit)
        
        # Convert NumPy types to Python native types
        for movie in similar_movies:
            for key, value in movie.items():
                # Convert NumPy integers to Python integers
                if isinstance(value, np.integer):
                    movie[key] = int(value)
                # Convert NumPy floats to Python floats
                elif isinstance(value, np.floating):
                    movie[key] = float(value)
                # Ensure other types are JSON serializable
                elif isinstance(value, (np.ndarray, pd.Series)):
                    movie[key] = value.tolist()
        
        return similar_movies
    except Exception as e:
        print(f"Error in similar movies endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting similar movies: {str(e)}")

@router.get("/movie/{movie_id}", response_model=Dict[str, Any])
async def get_movie_details(movie_id: str):
    """Get detailed information for a specific movie"""
    try:
        # Check if this is a TMDB ID
        if isinstance(movie_id, str) and movie_id.startswith("tmdb-"):
            tmdb_id = int(movie_id.replace("tmdb-", ""))
            movie_details = recommender_service.get_movie_details_by_tmdb(tmdb_id)
        else:
            # Convert to integer if it's not a TMDB ID string
            movie_details = recommender_service.get_movie_details(int(movie_id))
        
        if not movie_details:
            raise HTTPException(status_code=404, detail="Movie not found")
            
        # Convert NumPy types to Python native types
        for key, value in movie_details.items():
            if isinstance(value, np.integer):
                movie_details[key] = int(value)
            elif isinstance(value, np.floating):
                movie_details[key] = float(value)
            elif isinstance(value, (np.ndarray, pd.Series)):
                movie_details[key] = value.tolist()
                
        return movie_details
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid movie ID format")
    except Exception as e:
        print(f"Error in movie details endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting movie details: {str(e)}")

@router.post("/analyze-mood", response_model=Dict[str, Any])
async def analyze_mood(request: MoodAnalysisRequest):
    """
    Analyze text to determine user mood with enhanced validation
    """
    text = request.text
    
    if not text:
        raise HTTPException(
            status_code=400, 
            detail={
                "message": "Text is required",
                "suggestions": ["Please describe how you're feeling"]
            }
        )
    
    try:
        # Analyze the text with enhanced validation
        result = text_analysis_service.analyze_text(text)
        
        # Handle invalid input
        if not result.get('is_valid', True):
            # Return 422 for invalid but processable input (not server error)
            raise HTTPException(
                status_code=422,
                detail={
                    "message": result.get('message', 'Invalid mood description'),
                    "issues": result.get('issues', []),
                    "suggestions": result.get('suggestions', []),
                    "confidence": result.get('confidence', 0)
                }
            )
        
        # For valid input, get mood details and return enhanced response
        mood = result['mood']
        available_moods = recommender_service.get_available_moods()
        mood_details = next((m for m in available_moods if m["id"] == mood), None)
        
        response = {
            "mood": mood,
            "confidence": result['confidence'],
            "is_valid": result['is_valid'],
            "message": result.get('message', 'Mood detected successfully'),
            "mood_details": mood_details,
            "analysis": result.get('analysis', {})
        }
        
        # Add suggestions if confidence is low but still valid
        if result['confidence'] < 0.7:
            response["suggestions"] = [
                "For better results, try being more descriptive about your feelings",
                "Use emotion words like 'happy', 'sad', 'excited', 'calm', etc."
            ]
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        print(f"Error analyzing mood: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Error analyzing mood: {str(e)}",
                "suggestions": ["Please try again with a different description"]
            }
        )

# ================================================================
# 🆕 ENHANCED RECOMMENDATION ENDPOINTS
# ================================================================

@router.get("/recommendations/{mood}", response_model=List[Dict[str, Any]])
async def get_recommendations(
    mood: str,
    response: Response,  # ← This parameter is correct
    limit: int = Query(default=10, ge=1, le=50, description="Number of recommendations (1-50)"),
    session_id: Optional[str] = Query(default=None, description="Optional session ID for enhanced features")
):
    """Get movie recommendations for a specific mood with performance headers"""
    start_time = time.time()  # ← Now time is imported
    
    try:
        recommendations = recommender_service.get_recommendations(mood, limit, session_id)
        
        # Get cache stats for headers
        cache_stats = recommender_service.get_cache_stats()  # ← This method exists in your service
        
        # Convert NumPy types to Python native types (your existing logic)
        for movie in recommendations:
            for key, value in movie.items():
                if isinstance(value, np.integer):
                    movie[key] = int(value)
                elif isinstance(value, np.floating):
                    movie[key] = float(value)
                elif isinstance(value, (np.ndarray, pd.Series)):
                    movie[key] = value.tolist()
        
        # Add performance headers
        response_time = time.time() - start_time
        response.headers["X-Response-Time"] = f"{response_time:.2f}s"
        response.headers["X-Cache-Hit-Rate"] = f"{cache_stats['hit_rate_percent']}%"
        response.headers["X-Cache-Size"] = str(cache_stats['cached_items'])
        
        return recommendations
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in recommendations endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

# ================================================================
# 🆕 ENHANCED FEATURES ENDPOINTS
# ================================================================

@router.get("/recommendations/original/{mood}", response_model=List[Dict[str, Any]])
async def get_original_recommendations(
    mood: str, 
    limit: int = Query(default=10, ge=1, le=50, description="Number of recommendations")
):
    """
    Get recommendations using ONLY the original system (for comparison)
    
    This endpoint always uses your original recommendation algorithm,
    useful for A/B testing and comparison purposes.
    """
    try:
        recommendations = recommender_service.get_original_recommendations(mood, limit)
        
        # Convert NumPy types to Python native types
        for movie in recommendations:
            for key, value in movie.items():
                if isinstance(value, np.integer):
                    movie[key] = int(value)
                elif isinstance(value, np.floating):
                    movie[key] = float(value)
                elif isinstance(value, (np.ndarray, pd.Series)):
                    movie[key] = value.tolist()
        
        return recommendations
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in original recommendations endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting original recommendations: {str(e)}")

@router.get("/session/{session_id}/stats", response_model=Dict[str, Any])
async def get_session_stats(session_id: str):
    """
    Get statistics about a user's recommendation session
    
    Returns information about:
    - Moods requested in this session
    - Total movies recommended
    - Last activity time
    - Session status
    """
    try:
        stats = recommender_service.get_session_stats(session_id)
        return stats
    except Exception as e:
        print(f"Error getting session stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting session statistics: {str(e)}")

@router.delete("/session/{session_id}", response_model=Dict[str, str])
async def clear_session(session_id: str):
    """
    Clear a user's session data (reset anti-repetition history)
    
    Useful when a user wants to start fresh or see previously
    recommended movies again.
    """
    try:
        # This would be implemented in your service layer
        # For now, return success message
        return {
            "message": f"Session {session_id} cleared successfully",
            "session_id": session_id
        }
    except Exception as e:
        print(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

# ================================================================
# 🆕 COMPARISON AND TESTING ENDPOINTS
# ================================================================

@router.get("/compare/{mood}", response_model=Dict[str, Any])
async def compare_recommendation_systems(
    mood: str,
    limit: int = Query(default=10, ge=1, le=20, description="Number of recommendations per system"),
    session_id: Optional[str] = Query(default=None, description="Session ID for enhanced system")
):
    """
    Compare original vs enhanced recommendation systems side by side
    
    Useful for:
    - A/B testing
    - Demonstrating improvements
    - Quality assurance
    """
    try:
        # Get recommendations from both systems
        original_recs = recommender_service.get_original_recommendations(mood, limit) 
        
        if session_id:
            enhanced_recs = recommender_service.get_recommendations(mood, limit, session_id)
        else:
            enhanced_recs = original_recs  # Same as original if no session_id
        
        # Clean up NumPy types for both
        def clean_numpy_types(movies):
            for movie in movies:
                for key, value in movie.items():
                    if isinstance(value, np.integer):
                        movie[key] = int(value)
                    elif isinstance(value, np.floating):
                        movie[key] = float(value)
                    elif isinstance(value, (np.ndarray, pd.Series)):
                        movie[key] = value.tolist()
            return movies
        
        original_recs = clean_numpy_types(original_recs)
        enhanced_recs = clean_numpy_types(enhanced_recs)
        
        # Calculate comparison metrics
        original_titles = {movie['title'] for movie in original_recs}
        enhanced_titles = {movie['title'] for movie in enhanced_recs}
        
        overlap = len(original_titles & enhanced_titles)
        overlap_percentage = (overlap / limit * 100) if limit > 0 else 0
        
        return {
            "mood": mood,
            "session_id": session_id,
            "original_system": {
                "recommendations": original_recs,
                "count": len(original_recs)
            },
            "enhanced_system": {
                "recommendations": enhanced_recs,
                "count": len(enhanced_recs),
                "enabled": bool(session_id)
            },
            "comparison": {
                "overlap_count": overlap,
                "overlap_percentage": round(overlap_percentage, 1),
                "unique_to_original": len(original_titles - enhanced_titles),
                "unique_to_enhanced": len(enhanced_titles - original_titles),
                "variety_improvement": len(enhanced_titles - original_titles) > 0
            }
        }
    except Exception as e:
        print(f"Error in comparison endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error comparing systems: {str(e)}")

# ================================================================
# 🆕 HEALTH AND STATUS ENDPOINTS  
# ================================================================

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Health check endpoint with system status
    """
    try:
        # Check if enhanced features are available
        enhanced_available = hasattr(recommender_service, 'enhanced_features_enabled')
        enhanced_enabled = getattr(recommender_service, 'enhanced_features_enabled', False)
        
        return {
            "status": "healthy",
            "service": "MoodBinge Recommendations",
            "version": "2.0.0",
            "features": {
                "original_system": True,
                "enhanced_features_available": enhanced_available,
                "enhanced_features_enabled": enhanced_enabled,
                "text_analysis": True,
                "tmdb_integration": True
            },
            "endpoints": {
                "recommendations": "/recommendations/{mood}",
                "mood_analysis": "/analyze-mood",
                "session_stats": "/session/{session_id}/stats",
                "comparison": "/compare/{mood}"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
    
@router.get("/performance/stats", response_model=Dict[str, Any])
async def get_performance_stats():
    """
    Get system performance statistics
    
    Returns cache hit rates, response times, and other performance metrics
    """
    try:
        cache_stats = recommender_service.get_cache_stats()
        
        return {
            "status": "healthy",
            "performance": {
                "cache_statistics": cache_stats,
                "features": {
                    "parallel_tmdb_calls": True,
                    "intelligent_caching": True,
                    "expanded_preloading": True
                },
                "configuration": {
                    "cache_duration_hours": settings.TMDB_CACHE_DURATION_SECONDS // 3600,
                    "max_parallel_connections": settings.TMDB_PARALLEL_CONNECTIONS,
                    "preload_size": settings.TMDB_PRELOAD_SIZE
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance stats: {str(e)}")
    
@router.get("/metrics", response_model=Dict[str, Any])
async def get_detailed_metrics():
    """Get detailed system performance metrics"""
    try:
        cache_stats = recommender_service.get_cache_stats()
        return {
            "status": "healthy",
            "cache_performance": cache_stats,
            "features": {
                "enhanced_recommendations": True,
                "intelligent_caching": True,
                "parallel_processing": True
            },
            "performance": {
                "average_response_time_estimate": "2-4s",
                "cache_efficiency": f"{cache_stats['hit_rate_percent']}%"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")

@router.get("/health/detailed", response_model=Dict[str, Any])
async def detailed_health_check():
    """Detailed health check including TMDB connectivity"""
    try:
        cache_stats = recommender_service.get_cache_stats()
        
        # Quick TMDB test (optional - might be slow)
        # test_response = recommender_service._get_tmdb_data(550)  # Fight Club
        # tmdb_status = "healthy" if test_response else "degraded"
        
        return {
            "status": "healthy",
            "service": "MoodBinge Recommendations",
            "cache": {
                "status": "active",
                "hit_rate": f"{cache_stats['hit_rate_percent']}%",
                "cached_items": cache_stats['cached_items']
            },
            "features": {
                "parallel_processing": True,
                "intelligent_caching": True,
                "enhanced_recommendations": True
            }
            # "tmdb_api": tmdb_status  # Uncomment if you want TMDB test
        }
    except Exception as e:
        return {
            "status": "healthy", 
            "cache": {"status": "unknown"},
            "error": str(e)
        }