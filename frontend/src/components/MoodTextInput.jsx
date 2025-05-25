// frontend/src/components/MoodTextInput.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeMoodText } from '../services/api';
import { useToast } from '../hooks/useToast';
import './MoodTextInput.css';

const MoodTextInput = () => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!text.trim()) {
      toast.warning('Please tell us how you are feeling');
      return;
    }
    
    setLoading(true);
    
    try {
      console.log('Sending text for analysis:', text);
      const result = await analyzeMoodText(text);
      
      console.log('Analysis result:', result);
      
      if (result && result.mood) {
        toast.success(`Great! We detected you're feeling ${result.mood.replace(/_/g, ' ')}. Finding perfect movies for you!`);
        
        // Small delay to let user see the success message
        setTimeout(() => {
          navigate(`/recommendations/${result.mood}`);
        }, 1000);
      } else {
        toast.error('Could not determine your mood. Please try again or choose from the options below.');
      }
    } catch (err) {
      console.error('Error analyzing mood:', err);
      
      // More specific error messages
      if (err.response?.status === 401) {
        toast.error('Please log in to analyze your mood');
      } else if (err.response?.status >= 500) {
        toast.error('Server error. Please try again later.');
      } else {
        toast.error('Something went wrong. Please try again or choose from the options below.');
      }
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="mood-text-input-container">      
      <form onSubmit={handleSubmit} className="mood-text-form">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Feeling happy, sad, excited, or something else? Type it here!"
          className="mood-text-area"
          rows={3}
          disabled={loading}
        />
        
        <button 
          type="submit" 
          className="btn btn-primary mood-submit-btn" 
          disabled={loading || !text.trim()}
        >
          {loading ? (
            <>
              <span className="button-spinner"></span>
              Analyzing...
            </>
          ) : (
            'Find Movies'
          )}
        </button>
      </form>
    </div>
  );
};

export default MoodTextInput;