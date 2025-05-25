#backend/app/core/mood_mapping.py
mood_mapping = mood_mapping = {
    "euphoria_wave": {
        "description": "Pure happiness—big laughs, catchy tunes, and feel-good adventures.",
        "primary_genres": ["Comedy", "Animation", "Musical"],
        "secondary_genres": ["Adventure", "Family"],
        "excluded_genres": ["Horror", "Crime", "Thriller", "War", "Drama", "Mystery"],
        "tags": ["funny", "hilarious", "feel-good", "uplifting", "silly", "lighthearted", "energetic", "fun"],
        "tmdb_keywords": ["comedy", "humor", "friendship", "happy ending", "singing", "dancing", "laughter"],
        "runtime_preference": {"min": 80, "ideal": 100, "max": 130},
        "year_preference": "not_important",
        "pace_preference": "medium_to_fast",
        "sentiment": "positive",
        "color_palette": "bright",
        "neuro_signature": "Linked to dopamine-driven reward circuits"
    },
    
    "victory_high": {
        "description": "Get pumped with stories of big wins and epic comebacks.",
        "primary_genres": ["Action", "Sport", "Biography"],
        "secondary_genres": ["War", "Documentary"],
        "excluded_genres": ["Horror", "Film-Noir", "Romance", "Comedy", "Mystery"],
        "tags": ["inspiring", "sports", "victory", "triumph", "motivational", "comeback", "heroic",  "achievement", "underdog", "competition"],
        "tmdb_keywords": ["triumph", "underdog", "sports", "victory", "competition", "achievement", "heroism", "biography", "true story"],
        "runtime_preference": {"min": 90, "ideal": 120, "max": 150},
        "year_preference": "recency_bonus",
        "pace_preference": "fast",
        "sentiment": "positive",
        "color_palette": "vibrant",
        "neuro_signature": "Associated with nucleus accumbens activation"
    },
    
    "fury_awakened": {
        "description": "Channel your fire with films about standing up and fighting back.",
        "primary_genres": ["Crime", "Western", "Action"],
        "secondary_genres": ["Film-Noir"],
        "excluded_genres": ["Comedy", "Children", "Animation", "Romance", "Horror", "Musical", "Fantasy"],
        "tags": ["revenge", "justice", "intense", "powerful", "gritty", "violent", "dark", "conspiracy", "vigilante", "corruption"],
        "tmdb_keywords": ["revenge", "justice", "rebellion", "vigilante", "fighting", "corruption", "uprising", "crime boss", "mafia", "heist"],
        "runtime_preference": {"min": 100, "ideal": 130, "max": 160},
        "year_preference": "not_important",
        "pace_preference": "medium_to_fast",
        "sentiment": "negative_but_cathartic",
        "color_palette": "dark_contrasts",
        "neuro_signature": "Amygdala-driven aggression response"
    },
    
    "phantom_fear": {
        "description": "Heart-racing scares that'll have you double-checking the locks.",
        "primary_genres": ["Horror", "Thriller"],
        "secondary_genres": ["Sci-Fi"],
        "excluded_genres": ["Comedy", "Children", "Musical", "Romance", "Animation", "Documentary", "Sport"],
        "tags": ["scary", "horror", "tense", "suspense", "terrifying", "creepy", "haunting", "disturbing", "supernatural", "monster"],
        "tmdb_keywords": ["fear", "suspense", "supernatural", "monster", "ghost", "killer", "paranormal", "danger", "zombie", "vampire"],
        "runtime_preference": {"min": 85, "ideal": 105, "max": 130},
        "year_preference": "not_important",
        "pace_preference": "varied_with_building_tension",
        "sentiment": "fearful",
        "color_palette": "dark_muted",
        "neuro_signature": "Fear processing in anterior insula"
    },
    
    "tranquil_haven": {
        "description": "Relax and unwind with soothing, gentle movies—a cozy escape.",
        "primary_genres": ["Documentary", "Fantasy"],
        "secondary_genres": ["Animation"],
        "excluded_genres": ["Horror", "Action", "Thriller", "Crime", "War", "Mystery"],
        "tags": ["peaceful", "beautiful", "calm", "relaxing", "visually stunning", "soothing", "meditative", "nature", "serene", "gentle"],
        "tmdb_keywords": ["nature", "journey", "beautiful scenery", "meditation", "peaceful", "landscapes", "animals", "zen", "mindfulness"],
        "runtime_preference": {"min": 80, "ideal": 100, "max": 120},
        "year_preference": "not_important",
        "pace_preference": "slow_to_medium",
        "sentiment": "peaceful",
        "color_palette": "natural_soft",
        "neuro_signature": "Default mode network activation"
    },
    
    "heartfelt_harmony": {
        "description": "Celebrate love, friendship, and all the warm, fuzzy moments of life.",
        "primary_genres": ["Romance", "Comedy"],
        "secondary_genres": ["Musical"],
        "excluded_genres": ["Horror", "Thriller", "War", "Crime", "Action", "Sci-Fi"],
        "tags": ["romantic", "touching", "emotional", "heartwarming", "love", "sweet", "moving", "poignant", "relationship", "dating"],
        "tmdb_keywords": ["love", "romance", "relationship", "family", "friendship", "emotional", "wedding", "dating", "marriage"],
        "runtime_preference": {"min": 90, "ideal": 110, "max": 130},
        "year_preference": "recency_bonus",
        "pace_preference": "medium",
        "sentiment": "warm",
        "color_palette": "warm_tones",
        "neuro_signature": "Oxytocin-mediated social bonding"
    },
    
    "somber_ruminations": {
        "description": "Thoughtful dramas for when you want to slow down and reflect.",
        "primary_genres": ["Drama", "Film-Noir"],
        "secondary_genres": ["Documentary"],
        "excluded_genres": ["Comedy", "Children", "Action", "Musical", "Horror", "Romance"],
        "tags": ["depressing", "sad", "melancholy", "thoughtful", "profound", "philosophical", "dark", "intelligent", "introspective", "psychological"],
        "tmdb_keywords": ["tragedy", "loss", "reflection", "grief", "depression", "solitude", "suicide", "failure", "psychology", "mental health"],
        "runtime_preference": {"min": 100, "ideal": 130, "max": 180},
        "year_preference": "not_important",
        "pace_preference": "slow",
        "sentiment": "sad",
        "color_palette": "desaturated",
        "neuro_signature": "Prefrontal-amygdala decoupling"
    },
    
    "cosmic_emptiness": {
        "description": "Explore life's big questions and existential mysteries—you're not alone.",
        "primary_genres": ["Sci-Fi", "Drama"],
        "secondary_genres": ["Fantasy"],
        "excluded_genres": ["Comedy", "Children", "Musical", "Western", "Horror", "Romance"],
        "tags": ["existential", "philosophical", "surreal", "abstract", "experimental", "weird", "cerebral", "mind-bending", "metaphysical", "cosmic"],
        "tmdb_keywords": ["existential", "surreal", "dream", "reality", "consciousness", "universe", "perception", "space", "time", "philosophy"],
        "runtime_preference": {"min": 100, "ideal": 130, "max": 180},
        "year_preference": "not_important",
        "pace_preference": "varied_often_slow",
        "sentiment": "contemplative",
        "color_palette": "otherworldly",
        "neuro_signature": "Anterior cingulate cortex activity"
    },
    
    "timeworn_echoes": {
        "description": "Nostalgic journeys that bring back memories and bittersweet smiles.",
        "primary_genres": ["Drama", "Romance"],
        "secondary_genres": ["Fantasy", "Musical"],
        "excluded_genres": ["Horror", "Thriller", "War", "Action", "Sci-Fi"],
        "tags": ["nostalgic", "classic", "retro", "historical", "period", "memory", "childhood", "bittersweet", "vintage", "timeless"],
        "tmdb_keywords": ["nostalgia", "memory", "childhood", "coming of age", "flashback", "reminiscence", "history", "period piece", "vintage"],
        "runtime_preference": {"min": 100, "ideal": 120, "max": 160},
        "year_preference": {"classic_eras": [1940, 1950, 1960, 1970, 1980], "bonus_cutoff": 1990},
        "pace_preference": "medium",
        "sentiment": "bittersweet",
        "color_palette": "warm_vintage",
        "neuro_signature": "Hippocampal-prefrontal interplay"
    },
    
    "wonder_hunt": {
        "description": "Feed your curiosity with discoveries, mysteries, and mind-bending revelations.",
        "primary_genres": ["Mystery", "Documentary", "Thriller"],
        "secondary_genres": ["Adventure"],
        "excluded_genres": ["Horror", "Comedy", "Romance", "Musical", "War"],
        "tags": ["fascinating", "thought-provoking", "educational", "intriguing", "mystery", "intelligent", "twist", "discovery", "investigation"],
        "tmdb_keywords": ["discovery", "investigation", "science", "mystery", "truth", "revelation", "journey", "detective", "puzzle", "conspiracy"],
        "runtime_preference": {"min": 90, "ideal": 120, "max": 150},
        "year_preference": "not_important",
        "pace_preference": "medium",
        "sentiment": "curious",
        "color_palette": "rich_contrast",
        "neuro_signature": "Dopaminergic novelty-seeking"
    }
}

def get_available_moods():
    """Return a list of available mood categories with descriptions"""
    mood_colors = {
        "euphoria_wave": "#FFEB3B",      # Soft yellow
        "victory_high": "#FF9800",       # Vivid orange  
        "fury_awakened": "#D32F2F",      # Vivid crimson
        "phantom_fear": "#512DA8",       # Deep violet
        "tranquil_haven": "#4CAF50",     # Balanced green
        "heartfelt_harmony": "#FF8A80",  # Soft coral-pink
        "somber_ruminations": "#90A4AE", # Blue-gray
        "cosmic_emptiness": "#5C6BC0",   # Medium indigo
        "timeworn_echoes": "#FFD54F",    # Soft gold
        "wonder_hunt": "#2196F3"         # Sky blue
    }
    
    mood_emojis = {
        "euphoria_wave": "😄",
        "victory_high": "🏆",
        "fury_awakened": "💪",
        "phantom_fear": "👻",
        "tranquil_haven": "🌿",
        "heartfelt_harmony": "❤️",
        "somber_ruminations": "🤔",
        "cosmic_emptiness": "🌌",
        "timeworn_echoes": "⏳",
        "wonder_hunt": "🔍"
    }
    
    return [
        {
            "id": mood,
            "name": mood,
            "description": details["description"],
            "primary_genres": details["primary_genres"],
            "color": mood_colors[mood],
            "emoji": mood_emojis[mood]
        }
        for mood, details in mood_mapping.items()
    ]