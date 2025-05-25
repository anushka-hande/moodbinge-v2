// frontend/src/components/Navbar.jsx
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import ThemeToggle from './ThemeToggle';
import './Navbar.css';

const Navbar = () => {
  const { token, user, logout } = useAuth();
  
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">
          <span className="brand-text">MoodBinge</span>
        </Link>
      </div>
      <div className="navbar-menu">
        <ThemeToggle />
        {token ? (
          <>
            <Link to="/moods" className="navbar-item">Find Movies</Link>
            <span className="navbar-item navbar-username">Hi, {user}</span>
            <button className="navbar-item btn-link" onClick={logout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" className="navbar-item">Login</Link>
            <Link to="/register" className="navbar-item">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;