"""
⚠️ NOTE: This test file uses the PostgreSQL test database from conftest.py.
   SQLite support has been removed from the application.
"""
import os
import uuid
from datetime import datetime, timezone

import pytest

from src.services.oauth_service import GoogleSignInService
from src.database import init_db, get_session, close_session
from src.database.models import User as DBUser


@pytest.fixture(scope="module")
def google_service():
    # Ensure GOOGLE_CLIENT_ID is set to a dummy (service enabled)
    os.environ['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID', 'dummy-client-id.apps.googleusercontent.com')
    svc = GoogleSignInService()
    svc.client_id = os.environ['GOOGLE_CLIENT_ID']
    svc.enabled = True  # Force enable for test without real token verification
    return svc


@pytest.fixture(autouse=True)
def setup_db():
    """Use the PostgreSQL test database configured in conftest.py"""
    # Ensure database is initialized
    init_db()
    yield
    # Cleanup sessions after each test
    close_session()


def test_google_user_creation_with_legacy_not_null(google_service):
    # Simulate verified user info returned from Google token
    user_info = {
        'oauth_id': uuid.uuid4().hex,
        'email': 'legacy_test@example.com',
        'name': 'Legacy Tester',
        'profile_picture': None
    }

    # Call creation
    user = google_service.find_or_create_user(user_info)
    assert user is not None, 'User should be created even with NOT NULL password_hash constraint'

    # Validate fields
    session = get_session()
    try:
        db_user = session.query(DBUser).filter(DBUser.email == user_info['email']).first()
        assert db_user is not None, 'User must exist in database'
        assert getattr(db_user, 'oauth_provider') == 'google'
        assert getattr(db_user, 'oauth_id') == user_info['oauth_id']
        # password_hash should be None for OAuth-only users (nullable per schema)
        assert getattr(db_user, 'password_hash') is None, 'OAuth users should have NULL password_hash'
        # Verify OAuth columns are accessible (confirms schema has them)
        assert hasattr(db_user, 'oauth_provider'), 'Missing oauth_provider column'
        assert hasattr(db_user, 'oauth_id'), 'Missing oauth_id column'
        assert hasattr(db_user, 'profile_picture'), 'Missing profile_picture column'
    finally:
        close_session()


def test_google_user_link_existing_email(google_service):
    """Test linking a Google account to an existing password-based user."""
    # Create a password-based user first
    session = get_session()
    try:
        from werkzeug.security import generate_password_hash
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        existing_user = DBUser(
            id=user_id,
            username='existing_user',
            email='existing@example.com'
        )
        existing_user.set_password('password123')
        session.add(existing_user)
        session.commit()
    finally:
        close_session()

    # Now link Google account to this existing user
    user_info = {
        'oauth_id': uuid.uuid4().hex,
        'email': 'existing@example.com',
        'name': 'Existing User',
        'profile_picture': 'https://example.com/pic.jpg'
    }

    linked_user = google_service.find_or_create_user(user_info)
    assert linked_user is not None, 'User should be linked to existing account'

    session = get_session()
    try:
        db_user = session.query(DBUser).filter(DBUser.id == user_id).first()
        assert db_user is not None, 'User must still exist'
        assert getattr(db_user, 'oauth_provider') == 'google'
        assert getattr(db_user, 'oauth_id') == user_info['oauth_id']
        assert getattr(db_user, 'profile_picture') == user_info['profile_picture']
        # password_hash should still exist (not overwritten)
        assert getattr(db_user, 'password_hash') is not None, 'Original password_hash should be preserved'
    finally:
        close_session()
