// frontend/src/components/MoodCard.jsx
import { Link } from 'react-router-dom';
import { useState } from 'react';
import './MoodCard.css';

const MoodCard = ({ mood }) => {
  const [isHovered, setIsHovered] = useState(false);
  // Convert mood_name to display format (replace underscores with spaces and capitalize)
  const displayName = mood.id.replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
  
  return (
    <Link 
      to={`/recommendations/${mood.id}`} 
      className={`mood-card ${isHovered ? 'mood-card-hovered' : ''}`}
      style={{ backgroundColor: mood.color }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="mood-icon-container">
        <div className="mood-icon">{mood.emoji}</div>
        <div className="mood-pulse"></div>
      </div>
      <h3 className="mood-name">{displayName}</h3>
      <p className={`mood-description ${isHovered ? 'mood-description-visible' : ''}`}>
        {mood.description}
      </p>
      <div className="mood-glow"></div>
    </Link>
  );
};

export default MoodCard;