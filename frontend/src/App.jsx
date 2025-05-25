// frontend/src/App.jsx
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';
import MoodSelection from './pages/MoodSelection';
import Recommendations from './pages/Recommendations';
import MovieDetail from './pages/MovieDetail';
import Navbar from './components/Navbar';
import { AuthProvider } from './contexts/AuthProvider';
import { useAuth } from './hooks/useAuth';
import { ToastProvider } from './components/Toast/ToastContainer';
import NotFound from './components/NotFound';

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { token } = useAuth();
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Router>
          <div className="app">
            <Navbar />
            <main>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route 
                  path="/moods" 
                  element={
                    <ProtectedRoute>
                      <MoodSelection />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/recommendations/:mood" 
                  element={
                    <ProtectedRoute>
                      <Recommendations />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/movie/:id" 
                  element={
                    <ProtectedRoute>
                      <MovieDetail />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="*" 
                  element={
                    <NotFound />
                  } 
                />
              </Routes>
            </main>
          </div>
        </Router>
      </AuthProvider>
    </ToastProvider>
  );
}

export default App;