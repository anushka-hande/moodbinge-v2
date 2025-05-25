// frontend/src/pages/MovieDetail.jsx
import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getMovieDetails, getSimilarMovies } from '../services/api';
import MovieCard from '../components/MovieCard';
import { SkeletonMovieDetail } from '../components/skeletons/SkeletonCard';
import './MovieDetail.css';

const MovieDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [movie, setMovie] = useState(null);
  const [similarMovies, setSimilarMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchMovieDetails = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Get movie details from our API
        const details = await getMovieDetails(id);
        console.log("Movie details:", details);
        setMovie(details);
        
        try {
          // Get similar movies - this is a separate try/catch to still show movie details
          // even if similar movies fail to load
          const similar = await getSimilarMovies(id);
          console.log("Similar movies:", similar);
          setSimilarMovies(similar || []);
        } catch (similarErr) {
          console.error("Error fetching similar movies:", similarErr);
          setSimilarMovies([]);
        }
      } catch (err) {
        console.error("Error fetching movie details:", err);
        if (err.response && err.response.status === 404) {
          setError('Movie not found.');
        } else {
          setError('Failed to load movie details. Please try again later.');
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchMovieDetails();
  }, [id]);
  
  if (loading) {
    return <SkeletonMovieDetail />;
  }
  
  if (error) {
    return (
      <div className="error-container">
        <div className="error-message">{error}</div>
        <button className="btn btn-primary" onClick={() => navigate(-1)}>Go Back</button>
      </div>
    );
  }
  
  if (!movie) {
    return (
      <div className="no-results">
        <p>Movie not found. Please try a different selection.</p>
        <Link to="/moods" className="btn btn-primary">Back to Moods</Link>
      </div>
    );
  }
  
  const posterUrl = movie.poster_path 
    ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
    : '/placeholder-movie.png';
    
  const backdropUrl = movie.backdrop_path 
    ? `https://image.tmdb.org/t/p/original${movie.backdrop_path}`
    : null;
  
  // Extract year from title if not available in data
  const year = movie.year || (movie.title && movie.title.match(/\((\d{4})\)$/) ? movie.title.match(/\((\d{4})\)$/)[1] : null);
  
  // Format runtime as hours and minutes
  const formatRuntime = (minutes) => {
    if (!minutes) return null;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };
  
  // Clean title by removing year in parentheses
  const cleanTitle = movie.title ? movie.title.replace(/\s*\(\d{4}\)$/, '') : 'Unknown Title';
  
  // Clean genres - replace | with commas
  const cleanGenres = movie.genres ? movie.genres.replace(/\|/g, ', ') : '';
  
  return (
    <div className="movie-detail">
      {backdropUrl && (
        <div className="movie-backdrop" style={{ backgroundImage: `url(${backdropUrl})` }}></div>
      )}
      
      <div className="movie-content">
        <div className="movie-main">
          <div className="movie-poster-large">
            <img 
              src={posterUrl} 
              alt={cleanTitle}
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = '/placeholder-movie.png';
              }}
            />
            {movie.rating && (
              <div className="movie-rating-badge">
                {parseFloat(movie.rating).toFixed(1)}
              </div>
            )}
          </div>
          
          <div className="movie-info-large">
            <h1>{cleanTitle}</h1>
            
            <div className="movie-meta">
              {year && <span className="movie-year">{year}</span>}
              {movie.runtime && <span className="movie-runtime">{formatRuntime(movie.runtime)}</span>}
              {cleanGenres && <span className="movie-genres-large">{cleanGenres}</span>}
            </div>
            
            {movie.tagline && (
              <div className="movie-tagline">"{movie.tagline}"</div>
            )}
            
            {movie.overview ? (
              <div className="movie-overview">
                <h3>Overview</h3>
                <p>{movie.overview}</p>
              </div>
            ) : (
              <div className="movie-overview">
                <h3>Overview</h3>
                <p>No overview available for this movie.</p>
              </div>
            )}
            
            {movie.production_companies && movie.production_companies.length > 0 && (
              <div className="movie-companies">
                <h3>Production</h3>
                <p>{movie.production_companies.map(company => company.name).join(', ')}</p>
              </div>
            )}
            
            <div className="movie-actions">
              <button className="btn btn-secondary" onClick={() => navigate(-1)}>
                Back to Recommendations
              </button>
            </div>
          </div>
        </div>
        
        {similarMovies && similarMovies.length > 0 ? (
          <div className="similar-movies">
            <h2>Similar Movies You Might Enjoy</h2>
            <div className="movie-grid">
              {similarMovies.map((movie, index) => (
                <div key={movie.movieId || movie.tmdbId || `similar-${index}`} className="movie-item">
                  <MovieCard movie={movie} />
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="no-similar-movies">
            <h2>Similar Movies</h2>
            <p>No similar movies found for this title.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MovieDetail;