import os
import sys
import webbrowser
from flask import Flask
from threading import Timer
from extensions import login_manager, csrf
from routes import register_routes
from config import Config
from services import firebase_service

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

def create_app():
    template_dir = resource_path('templates')
    static_dir = resource_path('static')
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)

    # Firestore is the single source of truth - the desktop app works online.
    firebase_service.init_firebase()

    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(email):
        return firebase_service.get_user(email)

    register_routes(app)

    firebase_service.seed_default_channels()

    return app

if __name__ == '__main__':
    app = create_app()
    
    def open_browser():
        webbrowser.open('http://127.0.0.1:5000')
    
    Timer(1.5, open_browser).start()
    
    # Production-safe defaults: debug OFF, bound to localhost only.
    # Override with FLASK_DEBUG=1 and FLASK_HOST env vars when needed.
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    app.run(debug=debug, host=host, port=5000)