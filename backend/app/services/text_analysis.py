# backend/app/services/text_analysis.py
from textblob import TextBlob
import numpy as np
import re
import string
from app.core.mood_mapping import mood_mapping

class TextAnalysisService:
    def __init__(self):
        # Define the valence-arousal space for each mood
        self.mood_coordinates = {
            "euphoria_wave": (0.8, 0.7),     # High valence, high arousal
            "victory_high": (0.9, 0.9),      # Very high valence, very high arousal
            "fury_awakened": (-0.7, 0.8),    # Negative valence, high arousal
            "phantom_fear": (-0.8, 0.5),     # Negative valence, medium-high arousal
            "tranquil_haven": (0.5, -0.7),   # Positive valence, low arousal
            "heartfelt_harmony": (0.7, 0.2),  # High valence, medium-low arousal
            "somber_ruminations": (-0.6, -0.5), # Negative valence, low arousal
            "cosmic_emptiness": (-0.3, -0.8),  # Slightly negative valence, very low arousal
            "timeworn_echoes": (0.4, -0.4),   # Moderately positive valence, moderately low arousal
            "wonder_hunt": (0.6, 0.4)         # Positive valence, medium arousal
        }
        
        # Mood keywords for better matching
        self.mood_keywords = self._initialize_mood_keywords()
        
        # Initialize validation components
        self._initialize_validation_data()
    
    def _initialize_mood_keywords(self):
        """Extract keywords from mood mapping to improve text matching"""
        mood_keywords = {}
        
        for mood, details in mood_mapping.items():
            keywords = set()
            
            # Add tags and TMDB keywords
            if 'tags' in details:
                keywords.update(details['tags'])
            if 'tmdb_keywords' in details:
                keywords.update(details['tmdb_keywords'])
                
            # Add sentiment keywords based on mood description
            mood_keywords[mood] = keywords
        
        return mood_keywords
    
    def _initialize_validation_data(self):
        """Initialize data structures for input validation"""
        
        # Common English words (basic dictionary for validation)
        self.common_words = {
            # Emotions and feelings
            'happy', 'sad', 'angry', 'excited', 'tired', 'lonely', 'peaceful', 'stressed',
            'anxious', 'calm', 'frustrated', 'cheerful', 'depressed', 'motivated', 'bored',
            'confident', 'nervous', 'relaxed', 'overwhelmed', 'content', 'melancholy',
            'energetic', 'exhausted', 'hopeful', 'disappointed', 'scared', 'brave',
            'confused', 'clear', 'worried', 'carefree', 'nostalgic', 'optimistic',
            'pessimistic', 'curious', 'indifferent', 'passionate', 'apathetic',
            
            # Common adjectives
            'good', 'bad', 'great', 'terrible', 'amazing', 'awful', 'wonderful', 'horrible',
            'fantastic', 'nice', 'pleasant', 'unpleasant', 'beautiful', 'ugly', 'pretty',
            'weird', 'strange', 'normal', 'unusual', 'typical', 'special', 'ordinary',
            'extraordinary', 'simple', 'complex', 'easy', 'difficult', 'hard', 'soft',
            'bright', 'dark', 'light', 'heavy', 'big', 'small', 'large', 'tiny',
            'fast', 'slow', 'quick', 'loud', 'quiet', 'silent', 'noisy', 'smooth', 'rough',
            
            # Time and temporal words
            'today', 'yesterday', 'tomorrow', 'now', 'later', 'soon', 'recently', 'lately',
            'morning', 'afternoon', 'evening', 'night', 'weekend', 'week', 'month', 'year',
            'past', 'present', 'future', 'old', 'new', 'recent', 'ancient', 'modern',
            
            # Activities and situations
            'work', 'working', 'job', 'school', 'study', 'studying', 'home', 'family',
            'friends', 'relationship', 'love', 'breakup', 'party', 'celebration',
            'vacation', 'travel', 'movie', 'music', 'book', 'reading', 'watching',
            'listening', 'eating', 'sleeping', 'exercise', 'workout', 'running',
            'walking', 'driving', 'cooking', 'shopping', 'cleaning', 'playing',
            
            # Common verbs
            'feel', 'feeling', 'want', 'need', 'like', 'love', 'hate', 'enjoy', 'prefer',
            'think', 'believe', 'know', 'understand', 'remember', 'forget', 'learn',
            'teach', 'help', 'try', 'attempt', 'succeed', 'fail', 'win', 'lose',
            'start', 'begin', 'finish', 'end', 'continue', 'stop', 'pause', 'wait',
            'go', 'come', 'arrive', 'leave', 'stay', 'visit', 'meet', 'see', 'look',
            'watch', 'hear', 'listen', 'speak', 'talk', 'say', 'tell', 'ask', 'answer',
            
            # Common pronouns and articles
            'i', 'me', 'my', 'mine', 'you', 'your', 'yours', 'he', 'him', 'his',
            'she', 'her', 'hers', 'it', 'its', 'we', 'us', 'our', 'ours', 'they',
            'them', 'their', 'theirs', 'this', 'that', 'these', 'those', 'a', 'an', 'the',
            
            # Common prepositions and conjunctions
            'in', 'on', 'at', 'by', 'for', 'with', 'without', 'to', 'from', 'of',
            'about', 'over', 'under', 'above', 'below', 'through', 'between', 'among',
            'during', 'before', 'after', 'since', 'until', 'while', 'and', 'or', 'but',
            'so', 'because', 'if', 'when', 'where', 'why', 'how', 'what', 'which', 'who'
        }
        
        # Gibberish patterns to detect
        self.gibberish_patterns = [
            r'^[a-z]{1,2}$',  # Single or double letters
            r'^[0-9]+$',      # Only numbers
            r'^[^a-zA-Z]*$',  # No letters at all
            r'(.)\1{4,}',     # Repeated characters (5 or more)
            r'^[qwerty]+$|^[asdfgh]+$|^[zxcvbn]+$',  # Keyboard patterns
            r'^(test|testing|abc|xyz|hello|hi)$',     # Common test inputs
        ]
        
        # Emotion indicator words (high-value words for mood detection)
        self.emotion_indicators = {
            'positive': ['happy', 'joy', 'excited', 'great', 'amazing', 'wonderful', 'fantastic',
                        'cheerful', 'delighted', 'elated', 'euphoric', 'blissful', 'content',
                        'satisfied', 'pleased', 'glad', 'thrilled', 'ecstatic'],
            'negative': ['sad', 'depressed', 'angry', 'furious', 'upset', 'disappointed',
                        'frustrated', 'anxious', 'worried', 'stressed', 'overwhelmed',
                        'miserable', 'devastated', 'heartbroken', 'bitter', 'resentful'],
            'calm': ['peaceful', 'calm', 'relaxed', 'serene', 'tranquil', 'quiet',
                    'still', 'centered', 'balanced', 'composed'],
            'energetic': ['energetic', 'pumped', 'motivated', 'driven', 'determined',
                         'ambitious', 'active', 'dynamic', 'vigorous'],
            'contemplative': ['thoughtful', 'reflective', 'pensive', 'contemplative',
                             'philosophical', 'introspective', 'meditative']
        }
    
    def _validate_input(self, text):
        """
        Comprehensive input validation with multi-layer confidence scoring
        
        Returns:
            dict: Validation results with confidence score and issues
        """
        validation_result = {
            'is_valid': True,
            'confidence': 1.0,
            'issues': [],
            'suggestions': []
        }
        
        # Layer 1: Basic structural validation
        text_clean = text.lower().strip()
        
        # Check minimum length
        if len(text_clean) < 3:
            validation_result['is_valid'] = False
            validation_result['confidence'] = 0.0
            validation_result['issues'].append("Input too short")
            validation_result['suggestions'].append("Please describe how you're feeling in a few words")
            return validation_result
        
        # Check for gibberish patterns
        for pattern in self.gibberish_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                validation_result['is_valid'] = False
                validation_result['confidence'] = 0.0
                validation_result['issues'].append("Input appears to be gibberish")
                validation_result['suggestions'].append("Please describe your current mood or feelings")
                return validation_result
        
        # Layer 2: Word-level analysis
        words = re.findall(r'\b[a-zA-Z]+\b', text_clean)
        
        if len(words) == 0:
            validation_result['is_valid'] = False
            validation_result['confidence'] = 0.0
            validation_result['issues'].append("No meaningful words found")
            validation_result['suggestions'].append("Try describing your feelings with words like 'happy', 'sad', 'excited', etc.")
            return validation_result
        
        # Calculate word quality ratio
        meaningful_words = sum(1 for word in words if word in self.common_words or len(word) > 2)
        word_quality_ratio = meaningful_words / len(words) if words else 0
        
        # Layer 3: Character composition analysis
        total_chars = len(text_clean.replace(' ', ''))
        if total_chars > 0:
            letter_ratio = sum(1 for c in text_clean if c.isalpha()) / total_chars
            number_ratio = sum(1 for c in text_clean if c.isdigit()) / total_chars
            special_ratio = sum(1 for c in text_clean if c in string.punctuation) / total_chars
        else:
            letter_ratio = number_ratio = special_ratio = 0
        
        # Apply confidence penalties
        confidence = 1.0
        
        # Penalty for low word quality
        if word_quality_ratio < 0.3:
            confidence *= 0.4
            validation_result['issues'].append("Most words don't appear to be meaningful")
        elif word_quality_ratio < 0.6:
            confidence *= 0.7
            validation_result['issues'].append("Some words may not be meaningful")
        
        # Penalty for poor character composition
        if letter_ratio < 0.6:
            confidence *= 0.5
            validation_result['issues'].append("Too many numbers or symbols")
        
        if number_ratio > 0.3:
            confidence *= 0.6
            validation_result['issues'].append("Contains too many numbers")
        
        # Layer 4: Semantic validation using TextBlob
        try:
            blob = TextBlob(text)
            # If TextBlob can't process it properly, it might be gibberish
            sentiment = blob.sentiment
            
            # Check if sentiment analysis returns reasonable values
            if abs(sentiment.polarity) < 0.01 and abs(sentiment.subjectivity) < 0.01:
                confidence *= 0.7
                validation_result['issues'].append("Text may lack emotional content")
        except:
            confidence *= 0.5
            validation_result['issues'].append("Text structure appears unusual")
        
        # Layer 5: Emotion word detection (boost confidence for emotion words)
        emotion_word_found = False
        for category, emotion_words in self.emotion_indicators.items():
            if any(word in text_clean for word in emotion_words):
                emotion_word_found = True
                confidence = min(1.0, confidence * 1.2)  # Boost confidence
                break
        
        if not emotion_word_found:
            confidence *= 0.8
            validation_result['issues'].append("No clear emotion words detected")
            validation_result['suggestions'].append("Try using emotion words like 'happy', 'sad', 'excited', 'calm', etc.")
        
        # Final validation decision
        validation_result['confidence'] = max(0.0, min(1.0, confidence))
        
        # Set validity threshold
        if validation_result['confidence'] < 0.3:
            validation_result['is_valid'] = False
            if not validation_result['suggestions']:
                validation_result['suggestions'].append("Try describing your current feelings or mood more clearly")
        
        return validation_result
    
    def analyze_text(self, text):
        """
        Analyze text and return the most likely mood with enhanced validation
        
        Args:
            text (str): User input text describing their mood
        
        Returns:
            dict: Dictionary with mood ID, confidence score, validation results, and analysis details
        """
        if not text or len(text.strip()) == 0:
            return {
                "mood": None,
                "confidence": 0,
                "is_valid": False,
                "message": "Please describe how you're feeling",
                "suggestions": ["Try phrases like 'I feel happy', 'feeling sad today', or 'excited about something'"]
            }
        
        # Step 1: Validate input quality
        validation = self._validate_input(text)
        
        if not validation['is_valid']:
            return {
                "mood": None,
                "confidence": validation['confidence'],
                "is_valid": False,
                "message": "Input doesn't appear to be a meaningful mood description",
                "issues": validation['issues'],
                "suggestions": validation['suggestions']
            }
        
        # Step 2: Perform sentiment analysis (only for validated input)
        try:
            # Analyze the text using TextBlob
            blob = TextBlob(text.lower().strip())
            
            # Get sentiment polarity (-1 to 1, negative to positive)
            polarity = blob.sentiment.polarity
            
            # Get subjectivity (0 to 1, objective to subjective)
            subjectivity = blob.sentiment.subjectivity
            
            # Map subjectivity to arousal with validation confidence factor
            arousal = subjectivity * 0.5
            arousal += abs(polarity) * 0.3
            
            # Analyze language features for arousal adjustments
            exclamation_count = text.count('!')
            question_count = text.count('?')
            caps_count = sum(1 for c in text if c.isupper())
            
            # Adjust arousal based on language features
            if exclamation_count > 0:
                arousal += 0.1 * min(exclamation_count, 3)
            
            if caps_count > 3:
                arousal += 0.2
            
            if question_count > 2:
                arousal += 0.1
            
            # Normalize arousal to range from -1 to 1
            arousal = min(max(arousal * 2 - 1, -1), 1)
            valence = polarity
            
            # Extract key words for mood keyword matching
            key_words = set(word.lower() for word in blob.words if len(word) > 2)
            
            # Calculate distances to each mood in valence-arousal space
            distances = {}
            keyword_matches = {}
            
            for mood, (mood_valence, mood_arousal) in self.mood_coordinates.items():
                # Euclidean distance in valence-arousal space
                distance = np.sqrt((valence - mood_valence)**2 + (arousal - mood_arousal)**2)
                distances[mood] = distance
                
                # Count keyword matches
                mood_keywords = self.mood_keywords.get(mood, set())
                matches = len(key_words.intersection(mood_keywords))
                keyword_matches[mood] = matches
            
            # Normalize distances (smaller is better)
            max_distance = max(distances.values()) if distances.values() else 1
            normalized_distances = {m: 1 - (d / max_distance) for m, d in distances.items()}
            
            # Normalize keyword matches (larger is better)
            max_matches = max(keyword_matches.values()) if max(keyword_matches.values()) > 0 else 1
            normalized_matches = {m: k / max_matches for m, k in keyword_matches.items()}
            
            # Combine scores (70% distance-based, 30% keyword-based)
            combined_scores = {
                mood: 0.7 * normalized_distances[mood] + 0.3 * normalized_matches.get(mood, 0)
                for mood in distances.keys()
            }
            
            # Find best match
            best_mood = max(combined_scores.items(), key=lambda x: x[1])
            mood_id = best_mood[0]
            base_confidence = best_mood[1]
            
            # Adjust confidence based on validation quality
            final_confidence = base_confidence * validation['confidence']
            
            # Additional confidence checks
            if final_confidence < 0.4:
                return {
                    "mood": None,
                    "confidence": final_confidence,
                    "is_valid": False,
                    "message": "Unable to determine mood with sufficient confidence",
                    "suggestions": [
                        "Try being more specific about your feelings",
                        "Use descriptive words about your current emotional state",
                        "Examples: 'feeling excited about the weekend', 'sad after watching a movie'"
                    ],
                    "analysis": {
                        "valence": valence,
                        "arousal": arousal,
                        "key_words": list(key_words),
                        "validation_confidence": validation['confidence']
                    }
                }
            
            return {
                "mood": mood_id,
                "confidence": final_confidence,
                "is_valid": True,
                "message": "Mood detected successfully",
                "analysis": {
                    "valence": valence,
                    "arousal": arousal,
                    "key_words": list(key_words),
                    "mood_scores": combined_scores,
                    "validation_confidence": validation['confidence'],
                    "base_confidence": base_confidence
                }
            }
            
        except Exception as e:
            return {
                "mood": None,
                "confidence": 0,
                "is_valid": False,
                "message": "Error analyzing text",
                "error": str(e),
                "suggestions": ["Please try rephrasing your mood description"]
            }