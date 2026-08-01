import os
import sys
import secrets

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

class Config:
    SECRET_KEY = get_secret_key()
    UPLOAD_FOLDER = get_upload_folder()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'csv', 'zip'}
    # Firebase Web API key - public by design (used for the Auth REST endpoint)
    FIREBASE_WEB_API_KEY = os.environ.get('FIREBASE_WEB_API_KEY', 'AIzaSyBefRp77pRx93GvbhUQ9AZ0a4oX9hlZ7Tc')