"""Pytest configuration for NikNotes tests."""

import os
import pytest

# Ensure a deterministic Flask secret key is present during tests
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key")

# Disable CSRF protection for testing
os.environ.setdefault("WTF_CSRF_ENABLED", "False")


@pytest.fixture
def app():
    """Create and configure a test application instance"""
    from src.factory import create_app
    
    app = create_app('testing')
    
    yield app


@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()
