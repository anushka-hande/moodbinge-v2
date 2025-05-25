// frontend/src/pages/Home.jsx
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import './Home.css';
import LandingAnimation from '../components/LandingAnimation';
import { useEffect, useRef } from 'react';
import Feature from '../components/Feature';

const Home = () => {
  const { token } = useAuth();
  const emojiRef = useRef(null);

  useEffect(() => {
  const emojis = ['😄', '🏆', '💪', '👻', '🌿', '❤️', '🤔', '🌌', '⏳', '🔍'];
  const container = emojiRef.current;
  
  if (!container) return;
  
  // Create random emojis in the background
  for (let i = 0; i < 20; i++) {
    const emoji = document.createElement('div');
    emoji.className = 'floating-emoji';
    emoji.textContent = emojis[Math.floor(Math.random() * emojis.length)];
    emoji.style.left = `${Math.random() * 100}%`;
    emoji.style.top = `${Math.random() * 100}%`;
    emoji.style.animationDelay = `${Math.random() * 5}s`;
    emoji.style.animationDuration = `${10 + Math.random() * 20}s`;
    emoji.style.opacity = '0.1';
    emoji.style.fontSize = `${20 + Math.random() * 30}px`;
    container.appendChild(emoji);
  }
  
  return () => {
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
  };
}, []);

  return (
    <div className="home-container">
     <LandingAnimation />
      <div ref={emojiRef} className="emoji-background"></div>
      <div className="hero">
        <h1>Find Movies That Match Your Mood</h1>
        <p>Discover personalized movie recommendations based on how you're feeling right now.</p>
        {token ? (
          <Link to="/moods" className="btn btn-primary">Get Started</Link>
        ) : (
          <div className="hero-buttons">
            <Link to="/login" className="btn btn-primary">Login</Link>
            <Link to="/register" className="btn btn-secondary">Register</Link>
          </div>
        )}
      </div>
      
      <div className="features">
        <Feature 
          icon="🎭" 
          title="Mood-Based" 
          description="Find movies that perfectly match your current emotional state" 
        />
        <Feature 
          icon="🔍" 
          title="Discover" 
          description="Explore new films you might have never found otherwise" 
        />
        <Feature 
          icon="🎬" 
          title="Similar Movies" 
          description="Find related movies to your favorites with our recommendations" 
        />
      </div>
    </div>
  );
};

export default Home;