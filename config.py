import os
import sys
import secrets

def load_local_env():
    """Load optional secrets from a gitignored .env file next to the app.
    Used for API keys (URLHAUS_KEY, etc.) that must NOT be committed.
    Environment variables already set take precedence.
    """
    env_file = os.path.join(get_base_dir(), '.env')
    if not os.path.exists(env_file):
        return
    try:
        with open(env_file, 'r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass


def get_base_dir():
    """Get the base directory, works for both script and PyInstaller exe."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_database_path():
    """Get the absolute path for the database file."""
    return os.path.join(get_base_dir(), 'cybershield.db')

def get_upload_folder():
    """Get the absolute path for the upload folder."""
    folder = os.path.join(get_base_dir(), 'uploads')
    os.makedirs(folder, exist_ok=True)
    return folder

def get_secret_key():
    """Return a persistent random secret key.
    In production (no SECRET_KEY env var) the key is generated once and stored
    next to the database so session cookies survive app restarts.
    """
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    key_file = os.path.join(get_base_dir(), '.secret_key')
    if os.path.exists(key_file):
        with open(key_file, 'r') as fh:
            key = fh.read().strip()
            if key:
                return key
    key = secrets.token_hex(32)
    try:
        with open(key_file, 'w') as fh:
            fh.write(key)
    except OSError:
        pass  # Fall back to ephemeral key if we cannot persist
    return key

# Load optional secrets (.env) BEFORE Config is defined so the class picks them up.
load_local_env()

class Config:
    SECRET_KEY = get_secret_key()
    UPLOAD_FOLDER = get_upload_folder()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'csv', 'zip'}
    # Firebase Web API key - public by design (used for the Auth REST endpoint)
    FIREBASE_WEB_API_KEY = os.environ.get('FIREBASE_WEB_API_KEY', 'AIzaSyBefRp77pRx93GvbhUQ9AZ0a4oX9hlZ7Tc')
    # Optional free threat-intel keys (empty = keyless checks only)
    # Loaded from the gitignored .env file (load_local_env above) or env vars.
    GOOGLE_SAFE_BROWSING_KEY = os.environ.get('GOOGLE_SAFE_BROWSING_KEY', '')
    ABUSEIPDB_KEY = os.environ.get('ABUSEIPDB_KEY', '')
    URLHAUS_KEY = os.environ.get('URLHAUS_KEY', '')