import os

class ProductionConfig():
    """Production configuration for Chefs & Kitchen app."""
    DEBUG = False
    SESSION_COOKIE_SECURE = False  # OK for now, but true in real prod
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'session'
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_DOMAIN = None
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "test-secret-key")  # Match your .env
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', "sqlite:///instance/app.db")  # Default local database

class TestConfig():
    """Testing configuration for Chefs & Kitchen app."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory DB for pytest
