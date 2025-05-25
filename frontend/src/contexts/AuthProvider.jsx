// frontend/src/contexts/AuthContext.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import { AuthContext } from './AuthContext';

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [user, setUser] = useState(localStorage.getItem('user') || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Set up axios defaults when token changes
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      localStorage.setItem('token', token);
    } else {
      delete axios.defaults.headers.common['Authorization'];
      localStorage.removeItem('token');
    }
  }, [token]);
  
  const login = async (username, password) => {
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await axios.post('http://localhost:8000/api/v1/auth/token', formData);

      setToken(response.data.access_token);
      // Store the username (not email) in localStorage
      const displayName = username.includes('@') ? username.split('@')[0] : username;
      setUser(displayName);
      localStorage.setItem('user', displayName);
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
      return false;
    } finally {
      setLoading(false);
    }
  };
  
  const register = async (email, username, password) => {
    setLoading(true);
    setError(null);
    
    try {
      await axios.post('http://localhost:8000/api/v1/auth/register', {
        email,
        username,
        password
      });
      
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
      return false;
    } finally {
      setLoading(false);
    }
  };
  
  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('user');
  };
  
  return (
    <AuthContext.Provider value={{ token, user, loading, error, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

