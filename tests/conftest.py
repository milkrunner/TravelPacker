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


@pytest.fixture(scope="function")
def test_user():
    """Create a test user in the database"""
    from src.database import get_session, close_session
    from src.database.models import User
    
    session = get_session()
    try:
        # Create test user
        user = User(
            id="test_user",
            username="testuser",
            email="test@example.com"
        )
        user.set_password("testpassword123")
        
        session.add(user)
        session.commit()
        
        # Store the ID before yielding (so it's accessible after session closes)
        user_id = user.id
        
        yield user
        
        # Cleanup - reattach user or query fresh
        try:
            user_to_delete = session.query(User).filter_by(id=user_id).first()
            if user_to_delete:
                session.delete(user_to_delete)
                session.commit()
        except Exception:
            # If cleanup fails, just pass (test database will be dropped anyway)
            pass
    finally:
        close_session()
