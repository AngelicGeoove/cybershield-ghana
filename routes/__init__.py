from flask import Blueprint

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.report import report_bp
from routes.cyberlog import cyberlog_bp
from routes.channels import channels_bp
from routes.awareness import awareness_bp
from routes.profile import profile_bp
from routes.settings import settings_bp
from routes.admin import admin_bp
from routes.investigator import investigator_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(cyberlog_bp)
    app.register_blueprint(channels_bp)
    app.register_blueprint(awareness_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(investigator_bp)