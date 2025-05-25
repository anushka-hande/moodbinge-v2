// frontend/src/contexts/AuthProvider.jsx
import { useState, useEffect } from 'react';
import { AuthContext } from './AuthContext';
import { authAPI } from '../services/api';

export const AuthProvider = ({ children }) => {
 const [token, setToken] = useState(localStorage.getItem('token') || null);
 const [user, setUser] = useState(localStorage.getItem('user') || null);
 const [loading, setLoading] = useState(false);
 const [error, setError] = useState(null);
 
 // Handle token storage
 useEffect(() => {
   if (token) {
     localStorage.setItem('token', token);
   } else {
     localStorage.removeItem('token');
   }
 }, [token]);
 
 const login = async (username, password) => {
   setLoading(true);
   setError(null);
   
   try {
     const response = await authAPI.login({ username, password });
     setToken(response.access_token);
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
     await authAPI.register({ email, username, password });
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