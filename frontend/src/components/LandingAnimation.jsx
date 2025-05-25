// frontend/src/components/LandingAnimation.jsx
import { useEffect, useRef } from 'react';
import './LandingAnimation.css';

const LandingAnimation = () => {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    
    // Set canvas dimensions
    const setCanvasDimensions = () => {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    };
    
    setCanvasDimensions();
    window.addEventListener('resize', setCanvasDimensions);
    
    // Create emoji particles (fewer since we now have floating emojis too)
    const emojis = ['🎬', '🍿', '🎭', '📺', '🎬', '🎞️', '📽️'];
    const particles = [];
    
    for (let i = 0; i < 8; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: 15 + Math.random() * 15,
        speedX: (Math.random() - 0.5) * 1.5, // Slightly slower
        speedY: (Math.random() - 0.5) * 1.5, // Slightly slower
        emoji: emojis[Math.floor(Math.random() * emojis.length)]
      });
    }
    
    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Update and draw particles
      particles.forEach(particle => {
        // Update position
        particle.x += particle.speedX;
        particle.y += particle.speedY;
        
        // Bounce off walls
        if (particle.x <= 0 || particle.x >= canvas.width) {
          particle.speedX *= -1;
        }
        
        if (particle.y <= 0 || particle.y >= canvas.height) {
          particle.speedY *= -1;
        }
        
        // Draw emoji
        ctx.font = `${particle.size}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(particle.emoji, particle.x, particle.y);
      });
      
      animationFrameId = requestAnimationFrame(animate);
    };
    
    animate();
    
    // Cleanup
    return () => {
      window.removeEventListener('resize', setCanvasDimensions);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);
  
  return <canvas ref={canvasRef} className="landing-animation"></canvas>;
};

export default LandingAnimation;