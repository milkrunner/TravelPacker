"""
Blueprints package
"""

from flask import Flask

from .api import api_bp
from .auth import auth_bp
from .main import main_bp
from .trips import trips_bp


def register_blueprints(app: Flask):
    """Register all blueprints with the application"""
    app.register_blueprint(main_bp)
    app.register_blueprint(trips_bp, url_prefix="/trip")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/auth")
