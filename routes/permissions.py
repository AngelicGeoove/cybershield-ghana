from functools import wraps
from flask import abort
from flask_login import current_user

def require_roles(*roles):
    """Route decorator that restricts access to users with one of the given roles.
    Usage: @require_roles('admin') or @require_roles('investigator', 'admin')
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator
