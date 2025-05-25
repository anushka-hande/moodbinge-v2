// frontend/src/pages/MoodSelection.jsx
import { useState, useEffect } from 'react';
import { getMoods } from '../services/api';
import MoodCard from '../components/MoodCard';
import { SkeletonGrid } from '../components/skeletons/SkeletonCard';
import './MoodSelection.css';
import MoodTextInput from '../components/MoodTextInput';

const MoodSelection = () => {
  const [moods, setMoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchMoods = async () => {
      try {
        const data = await getMoods();
        setMoods(data);
      } catch (err) {
        setError('Failed to load moods. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchMoods();
  }, []);
  
  if (error) {
    return (
      <div className="mood-selection">
        <div className="error-message">
          <div className="error-icon">😞</div>
          <h2>Oops! Something went wrong</h2>
          <p>{error}</p>
          <button 
            className="btn btn-primary" 
            onClick={() => window.location.reload()}
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="mood-selection">
      <div className="mood-header">
        <h1>How are you feeling today?</h1>
        <p className="subtitle">
          Let us know how you're feeling, and we'll suggest the perfect film.
        </p>
      </div>
      
      {/* Text-based mood input */}
      <MoodTextInput />
      
      <div className="mood-divider">
        <span>Or, select a mood below</span>
      </div>
      
      {loading ? (
        <SkeletonGrid count={10} type="mood" />
      ) : (
        <div className="mood-grid">
          {moods.map((mood) => (
            <MoodCard key={mood.id} mood={mood} />
          ))}
        </div>
      )}
    </div>
  );
};

export default MoodSelection;