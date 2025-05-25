// frontend/src/components/Feature.jsx
import { useEffect, useRef } from 'react';
import './Feature.css';

const Feature = ({ icon, title, description }) => {
  const featureRef = useRef(null);
  
  useEffect(() => {
    const element = featureRef.current;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('feature-visible');
          observer.unobserve(entry.target);
        }
      },
      {
        root: null,
        threshold: 0.1,
      }
    );
    
    if (element) {
      observer.observe(element);
    }
    
    return () => {
      if (element) {
        observer.unobserve(element);
      }
    };
  }, []);
  
  return (
    <div ref={featureRef} className="feature">
      <div className="feature-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
};

export default Feature;