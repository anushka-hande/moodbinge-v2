// frontend/src/services/api.js
import axios from 'axios';

// Use environment variable for API URL
const API_URL = import.meta.env.VITE_API_URL || 'https://anushkah39.pythonanywhere.com/api/v1/movies';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// ================================================================
// 🆕 SESSION MANAGEMENT UTILITIES
// ================================================================

// Generate unique session ID for user
const generateSessionId = () => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2);
  return `session_${timestamp}_${random}`;
};

// Get or create session ID
export const getSessionId = () => {
  let sessionId = localStorage.getItem('moodbinge_session_id');
  
  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem('moodbinge_session_id', sessionId);
    console.log('🎬 New MoodBinge session created:', sessionId);
  }
  
  return sessionId;
};

// Clear session (for "show different movies" functionality)
export const clearSession = () => {
  const oldSessionId = localStorage.getItem('moodbinge_session_id');
  localStorage.removeItem('moodbinge_session_id');
  const newSessionId = getSessionId(); // Generate new one
  console.log('🔄 Session refreshed:', { old: oldSessionId, new: newSessionId });
  return newSessionId;
};

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle different error scenarios
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('token');
          window.location.href = '/login';
          break;
        case 422:
          // Validation error - pass through for handling
          console.warn('Validation error:', data);
          break;
        case 500:
          console.error('Server error:', data);
          break;
        default:
          console.error('API error:', error.response);
      }
    } else if (error.request) {
      // Network error
      console.error('Network error:', error.request);
    } else {
      // Other error
      console.error('Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Auth API functions
export const authAPI = {
  login: async (credentials) => {
    try {
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);
      
      const response = await apiClient.post('/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  register: async (userData) => {
    try {
      const response = await apiClient.post('/auth/register', userData);
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  },
};

// ================================================================
// 🆕 ENHANCED MOVIE API FUNCTIONS
// ================================================================

export const getMoods = async () => {
  try {
    const response = await apiClient.get('/moods'); // Fixed URL path
    return response.data;
  } catch (error) {
    console.error('Error fetching moods:', error);
    throw error;
  }
};

// Enhanced recommendations with session support
export const getRecommendations = async (mood, limit = 10, options = {}) => {
  try {
    const {
      useEnhanced = true,    // Use enhanced features by default
      sessionId = null,      // Custom session ID
      forceRefresh = false   // Force new session
    } = options;
    
    // Determine session ID
    let finalSessionId = sessionId;
    
    if (useEnhanced) {
      if (forceRefresh) {
        finalSessionId = clearSession();
      } else {
        finalSessionId = sessionId || getSessionId();
      }
    }
    
    // Build request parameters
    const params = { limit };
    if (finalSessionId && useEnhanced) {
      params.session_id = finalSessionId;
    }
    
    console.log('🎬 Fetching recommendations:', { 
      mood, 
      limit, 
      enhanced: useEnhanced, 
      sessionId: finalSessionId 
    });
    
    const response = await apiClient.get(`/recommendations/${mood}`, { params });
    
    console.log(`✅ Received ${response.data.length} recommendations`);
    return response.data;
  } catch (error) {
    console.error('Error fetching recommendations:', error);
    throw error;
  }
};

// Get original system recommendations (for comparison)
export const getOriginalRecommendations = async (mood, limit = 10) => {
  try {
    const response = await apiClient.get(`/recommendations/original/${mood}`, {
      params: { limit }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching original recommendations:', error);
    throw error;
  }
};

// Compare both recommendation systems
export const compareRecommendations = async (mood, limit = 10) => {
  try {
    const sessionId = getSessionId();
    const response = await apiClient.get(`/compare/${mood}`, {
      params: { limit, session_id: sessionId }
    });
    return response.data;
  } catch (error) {
    console.error('Error comparing recommendations:', error);
    throw error;
  }
};

// Get session statistics
export const getSessionStats = async (sessionId = null) => {
  try {
    const finalSessionId = sessionId || getSessionId();
    const response = await apiClient.get(`/session/${finalSessionId}/stats`);
    return response.data;
  } catch (error) {
    console.error('Error fetching session stats:', error);
    throw error;
  }
};

// Clear user session on server
export const clearServerSession = async (sessionId = null) => {
  try {
    const finalSessionId = sessionId || getSessionId();
    const response = await apiClient.delete(`/session/${finalSessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error clearing server session:', error);
    throw error;
  }
};

export const getSimilarMovies = async (movieId, limit = 5) => {
  try {
    const response = await apiClient.get(`/similar/${movieId}`, {
      params: { limit }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching similar movies:', error);
    throw error;
  }
};

export const getMovieDetails = async (movieId) => {
  try {
    const response = await apiClient.get(`/movie/${movieId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching movie details:', error);
    throw error;
  }
};

export const analyzeMoodText = async (text) => {
  try {
    const response = await apiClient.post('/analyze-mood', { text });
    console.log('Mood analysis response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error analyzing mood text:', error);
    
    // Handle specific validation errors
    if (error.response?.status === 422) {
      // Return the validation error details
      throw {
        ...error,
        validationError: true,
        details: error.response.data
      };
    }
    
    throw error;
  }
};

// Enhanced API health check
export const checkAPIHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.error('API health check failed:', error);
    throw error;
  }
};

// ================================================================
// 🆕 UTILITY FUNCTIONS
// ================================================================

// Check if enhanced features are available
export const checkEnhancedFeatures = async () => {
  try {
    const health = await checkAPIHealth();
    return {
      available: health.features?.enhanced_features_available || false,
      enabled: health.features?.enhanced_features_enabled || false,
      version: health.version || 'Unknown'
    };
  } catch {
    return { available: false, enabled: false, version: 'Unknown' };
  }
};

// Batch API calls for dashboard
export const getDashboardData = async (mood) => {
  try {
    const sessionId = getSessionId();
    
    const [recommendations, sessionStats, healthCheck] = await Promise.allSettled([
      getRecommendations(mood, 10, { sessionId }),
      getSessionStats(sessionId),
      checkAPIHealth()
    ]);
    
    return {
      recommendations: recommendations.status === 'fulfilled' ? recommendations.value : [],
      sessionStats: sessionStats.status === 'fulfilled' ? sessionStats.value : null,
      health: healthCheck.status === 'fulfilled' ? healthCheck.value : null,
      sessionId
    };
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    throw error;
  }
};

export default apiClient;