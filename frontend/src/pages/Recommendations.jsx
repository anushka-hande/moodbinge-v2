// frontend/src/pages/Recommendations.jsx
// frontend/src/pages/Recommendations.jsx
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  getRecommendations, 
  getSessionStats, 
  checkEnhancedFeatures 
} from '../services/api';
import MovieCard from '../components/MovieCard';
import { SkeletonGrid } from '../components/skeletons/SkeletonCard';
import './Recommendations.css';

const Recommendations = () => {
  const { mood } = useParams();
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sessionStats, setSessionStats] = useState(null);
  const [enhancedFeatures, setEnhancedFeatures] = useState({ available: false, enabled: false });
  const [refreshing, setRefreshing] = useState(false);
  
  // Format mood name for display (replace underscores with spaces and capitalize)
  const formatMoodName = (moodStr) => {
    return moodStr
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };
  
  // Get mood color based on mood ID
  const getMoodColor = (moodId) => {
    const moodColors = {
      'euphoria_wave': '#FFEB3B',
      'victory_high': '#FF9800', 
      'fury_awakened': '#D32F2F',
      'phantom_fear': '#512DA8',
      'tranquil_haven': '#4CAF50',
      'heartfelt_harmony': '#FF8A80',
      'somber_ruminations': '#90A4AE',
      'cosmic_emptiness': '#5C6BC0',
      'timeworn_echoes': '#FFD54F',
      'wonder_hunt': '#2196F3'
    };
    
    return moodColors[moodId] || '#6200ea';
  };
  
  // Fetch session statistics
  const fetchSessionStats = async () => {
    try {
      const stats = await getSessionStats();
      setSessionStats(stats);
    } catch (error) {
      console.error('Failed to fetch session stats:', error);
    }
  };
  
  // Handle "Show Different Movies" click
  const handleRefreshRecommendations = async () => {
    setRefreshing(true);
    try {
      // Force refresh with new session
      const response = await getRecommendations(mood, 10, { forceRefresh: true });
      setMovies(response);
      
      // Update session stats
      await fetchSessionStats();
      
      console.log('🔄 Recommendations refreshed successfully');
    } catch (err) {
      console.error('Error refreshing recommendations:', err);
      setError('Failed to refresh recommendations. Please try again.');
    } finally {
      setRefreshing(false);
    }
  };
  
  useEffect(() => {
    let isMounted = true;
    
    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Check enhanced features availability
        const features = await checkEnhancedFeatures();
        if (isMounted) {
          setEnhancedFeatures(features);
        }
        
        // Fetch recommendations with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
        
        const response = await getRecommendations(mood, 10, { 
          useEnhanced: features.enabled 
        });
        clearTimeout(timeoutId);
        
        if (!isMounted) return;
        
        if (response && response.length > 0) {
          console.log(`✅ Received ${response.length} movie recommendations`);
          setMovies(response);
          
          // Fetch session stats if enhanced features are enabled
          if (features.enabled) {
            await fetchSessionStats();
          }
        } else {
          setError('No movies found for this mood. Please try a different mood.');
        }
      } catch (err) {
        if (!isMounted) return;
        console.error("Error fetching recommendations:", err);
        
        if (err.name === 'AbortError') {
          setError('Request timed out. Please check your connection and try again.');
        } else {
          setError('Failed to load recommendations. Please try again later.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    
    fetchRecommendations();
    
    return () => {
      isMounted = false;
    };
  }, [mood]);
  
  if (loading) {
    return (
      <div className="recommendations-container">
        <div className="recommendations-header">
          <h1>
            Movies For Your{' '}
            <span className="mood-highlight" style={{ color: getMoodColor(mood) }}>
              {formatMoodName(mood)}
            </span>
            {' '}Mood
          </h1>
          <Link to="/moods" className="change-mood-btn">Change Mood</Link>
        </div>
        <div className="loading-message">
          <p>🎬 Finding perfect movies for your mood...</p>
          {enhancedFeatures.enabled && (
            <p className="loading-sub">Personalizing recommendations just for you</p>
          )}
        </div>
        <SkeletonGrid count={12} type="card" />
      </div>
    );
  }
  
  return (
    <div className="recommendations-container">
      <div className="recommendations-header">
        <h1>
          Movies For Your{' '}
          <span className="mood-highlight" style={{ color: getMoodColor(mood) }}>
            {formatMoodName(mood)}
          </span>
          {' '}Mood
        </h1>
        <div className="header-actions">
          <Link to="/moods" className="change-mood-btn">Change Mood</Link>
        </div>
      </div>
      
      {/* Enhanced Features Info Bar */}
      {enhancedFeatures.enabled && sessionStats && (
        <div className="session-info-bar">
          <div className="session-stats">
            ✨ <strong>Fresh picks just for you!</strong>
            {sessionStats.session_found && (
              <span className="stats-detail">
                {' '}• Discovered {sessionStats.total_movies_seen} movies across{' '}
                {sessionStats.moods_requested.length} mood{sessionStats.moods_requested.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <button 
            onClick={handleRefreshRecommendations}
            disabled={refreshing}
            className="refresh-btn"
            title="Get completely different movies"
          >
            {refreshing ? '🔄 Finding...' : '🎲 Show Different Movies'}
          </button>
        </div>
      )}
      
      {error ? (
        <div className="recommendations-error">
          <p>{error}</p>
          <div className="error-actions">
            <button 
              onClick={() => window.location.reload()} 
              className="btn btn-secondary"
            >
              Try Again
            </button>
            <Link to="/moods" className="btn btn-primary">Back to Moods</Link>
          </div>
        </div>
      ) : movies.length === 0 ? (
        <div className="recommendations-empty">
          <p>No movie recommendations found. Please try a different mood.</p>
          <Link to="/moods" className="btn btn-primary">Back to Moods</Link>
        </div>
      ) : (
        <>
          <div className="recommendations-summary">
            <p className="summary-text">
              {enhancedFeatures.enabled 
                ? `${movies.length} personalized recommendations • No repeats from your recent history`
                : `${movies.length} recommendations for ${formatMoodName(mood).toLowerCase()}`
              }
            </p>
          </div>
          
          <div className="movie-grid">
            {movies.map((movie, index) => (
              <div key={`${movie.movieId || movie.tmdbId || index}`} className="movie-item">
                <MovieCard movie={movie} />
                {enhancedFeatures.enabled && movie.randomization_applied && (
                  <div className="enhanced-badge" title="Enhanced with smart variety">
                    ✨
                  </div>
                )}
              </div>
            ))}
          </div>
          
          {/* Additional Actions */}
          <div className="recommendations-actions">
            {enhancedFeatures.enabled && (
              <button 
                onClick={handleRefreshRecommendations}
                disabled={refreshing}
                className="btn btn-secondary refresh-large"
              >
                {refreshing ? '🔄 Finding Different Movies...' : '🎲 Show Me Different Movies'}
              </button>
            )}
            <Link to="/moods" className="btn btn-outline">
              Explore Other Moods
            </Link>
          </div>
        </>
      )}
    </div>
  );
};

export default Recommendations;