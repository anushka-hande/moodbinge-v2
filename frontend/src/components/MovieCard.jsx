// frontend/src/components/MovieCard.jsx
import { Link } from 'react-router-dom';
import './MovieCard.css';

const MovieCard = ({ movie }) => {
  // Create a title display that doesn't include the year in parentheses twice
  const displayTitle = movie.title || 'Unknown Title';
  
  // Clean genres - replace | with commas
  const cleanGenres = movie.genres ? movie.genres.replace(/\|/g, ', ') : '';
  
  // Format the movie's rating to 1 decimal place, if available
  const rating = movie.rating ? parseFloat(movie.rating).toFixed(1) : null;
  
  // Get link ID - use movieId if available, otherwise use tmdbId
  const movieId = movie.movieId || (movie.tmdbId ? `tmdb-${movie.tmdbId}` : null);
  
  // If no ID available, don't render the card
  if (!movieId) return null;
  
  // Create movie poster URL - either from TMDB or a placeholder
  // You'll need to create this placeholder image in your public folder
  const posterUrl = movie.poster_path 
    ? `https://image.tmdb.org/t/p/w300${movie.poster_path}`
    : '/placeholder-movie.png';
  
  // Extract year (either from the data or from the title)
  const year = movie.year || 
    (displayTitle.match(/\((\d{4})\)$/) ? displayTitle.match(/\((\d{4})\)$/)[1] : null);
  
  // Clean title by removing year in parentheses if present
  const cleanTitle = displayTitle.replace(/\s*\(\d{4}\)$/, '');
  
  return (
    <div className="movie-card">
      <Link to={`/movie/${movieId}`} className="movie-link">
        <div className="movie-poster">
          <img 
            src={posterUrl} 
            alt={cleanTitle}
            onError={(e) => {
              e.target.onerror = null; 
              e.target.src = '/placeholder-movie.png';
            }} 
          />
          {rating && <div className="movie-rating">{rating}</div>}
        </div>
        <div className="movie-info">
          <h3 className="movie-title">{cleanTitle}</h3>
          <div className="movie-details">
            {year && <span className="movie-year">{year}</span>}
            {cleanGenres && <span className="movie-genres">{cleanGenres}</span>}
          </div>
        </div>
      </Link>
    </div>
  );
};

export default MovieCard;