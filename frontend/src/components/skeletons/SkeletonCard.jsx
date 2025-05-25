// frontend/src/components/skeletons/SkeletonCard.jsx
import './Skeleton.css';

export const SkeletonCard = () => {
  return (
    <div className="skeleton-card">
      <div className="skeleton-poster"></div>
      <div className="skeleton-content">
        <div className="skeleton-title"></div>
        <div className="skeleton-subtitle"></div>
        <div className="skeleton-text short"></div>
      </div>
    </div>
  );
};

// frontend/src/components/skeletons/SkeletonMoodCard.jsx
export const SkeletonMoodCard = () => {
  return (
    <div className="skeleton-mood-card">
      <div className="skeleton-icon"></div>
      <div className="skeleton-mood-title"></div>
      <div className="skeleton-mood-desc line1"></div>
      <div className="skeleton-mood-desc line2"></div>
      <div className="skeleton-mood-desc line3"></div>
    </div>
  );
};

// frontend/src/components/skeletons/SkeletonMovieDetail.jsx
export const SkeletonMovieDetail = () => {
  return (
    <div className="skeleton-movie-detail">
      <div className="skeleton-backdrop"></div>
      <div className="skeleton-detail-content">
        <div className="skeleton-detail-main">
          <div className="skeleton-detail-poster"></div>
          <div className="skeleton-detail-info">
            <div className="skeleton-detail-title"></div>
            <div className="skeleton-detail-meta">
              <div className="skeleton-meta-item"></div>
              <div className="skeleton-meta-item"></div>
              <div className="skeleton-meta-item"></div>
            </div>
            <div className="skeleton-overview">
              <div className="skeleton-overview-title"></div>
              <div className="skeleton-overview-text line1"></div>
              <div className="skeleton-overview-text line2"></div>
              <div className="skeleton-overview-text line3"></div>
              <div className="skeleton-overview-text line4"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// frontend/src/components/skeletons/SkeletonGrid.jsx
export const SkeletonGrid = ({ count = 8, type = 'card' }) => {
  const SkeletonComponent = type === 'mood' ? SkeletonMoodCard : SkeletonCard;
  
  return (
    <div className={`skeleton-grid ${type === 'mood' ? 'mood-grid' : 'movie-grid'}`}>
      {Array.from({ length: count }, (_, index) => (
        <SkeletonComponent key={index} />
      ))}
    </div>
  );
};