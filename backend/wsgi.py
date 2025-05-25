# backend/wsgi.py - for PythonAnywhere

import os
import sys

# Add your project directory to the sys.path
# On PythonAnywhere, your files will be in /home/yourusername/
path = '/home/anushkah39/moodbinge_v2/backend'  # ← Change 'yourusername'
if path not in sys.path:
    sys.path.append(path)

# Also add the parent directory for imports
parent_path = '/home/anushkah39/moodbinge_v2'  # ← Change 'yourusername'
if parent_path not in sys.path:
    sys.path.append(parent_path)

# Set environment variables - REPLACE WITH YOUR ACTUAL VALUES
os.environ['TMDB_API_KEY'] = '65614a39092c80f0380af9d36fb8ef01'  # ← Your TMDB key
os.environ['SECRET_KEY'] = 's_F9Lsxf5hVnzKoa4D8EqWJULf81EYvAQ-TZD-UiTko'  # ← Generate a secure key
os.environ['DATABASE_URL'] = 'mysql://anushkah39:anna0346@anushkah39.mysql.pythonanywhere-services.com/anushkah39$moodbinge'  # ← Replace yourusername and password
os.environ['DATA_PATH'] = '/home/anushkah39/moodbinge_v2/backend/data/ml-latest-small/'  # ← Change yourusername

# Import your FastAPI app
try:
    from main import app as application
except ImportError as e:
    # Debugging: Print the error and paths
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"Files in backend directory: {os.listdir('/home/anushkah39/moodbinge_v2/backend') if os.path.exists('/home/anushkah39/moodbinge_v2/backend') else 'Directory not found'}")
    raise

# For debugging - remove this after everything works
print("WSGI file loaded successfully!")
print(f"FastAPI app loaded: {application}")

if __name__ == "__main__":
    application.run()