// frontend/src/components/LoadingSpinner.jsx
import './LoadingSpinner.css';

const LoadingSpinner = ({ message = 'Loading...', size = 'medium', variant = 'default' }) => {
  const sizeClasses = {
    small: 'spinner-small',
    medium: 'spinner-medium',
    large: 'spinner-large'
  };

  const variantClasses = {
    default: 'spinner-default',
    gradient: 'spinner-gradient',
    dots: 'spinner-dots'
  };

  if (variant === 'dots') {
    return (
      <div className="spinner-container">
        <div className={`spinner-dots-wrapper ${sizeClasses[size]}`}>
          <div className="spinner-dot"></div>
          <div className="spinner-dot"></div>
          <div className="spinner-dot"></div>
        </div>
        <p className="spinner-text">{message}</p>
      </div>
    );
  }

  return (
    <div className="spinner-container">
      <div className={`spinner ${sizeClasses[size]} ${variantClasses[variant]}`}>
        <div className="spinner-inner"></div>
      </div>
      <p className="spinner-text">{message}</p>
    </div>
  );
};

export default LoadingSpinner;