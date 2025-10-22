import os
import sqlite3
import uuid
from datetime import datetime

import pytest

from src.services.oauth_service import GoogleSignInService
from src.database import init_db, get_session, close_session, engine
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
def setup_db(tmp_path, monkeypatch):
    """Use an isolated SQLite file per test module to avoid clobbering real db.
    We intentionally recreate a legacy NOT NULL constraint scenario by creating users table without nullable password_hash.
    Then run init_db() which triggers auto-patch logic without altering NOT NULL (simulating pre-migration)."""
    test_db = tmp_path / 'legacy.db'
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{test_db}')
    # Reinitialize engine indirectly by importing/reloading database module would be complex; direct connect instead.
    # Create legacy schema manually:
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            username VARCHAR(80) NOT NULL,
            email VARCHAR(120) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN,
            created_at DATETIME,
            last_login DATETIME
        )
    """)
    conn.commit()
    conn.close()

    # Now run init_db() to add new tables + attempt auto-patch for oauth columns
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
        assert db_user.oauth_provider == 'google'
        assert db_user.oauth_id == user_info['oauth_id']
        # password_hash should have dummy value, not None and not empty
        assert db_user.password_hash, 'Dummy password hash should be set'
        # Ensure new oauth columns exist (auto-patched)
        # PRAGMA table_info to confirm columns
        raw_conn = session.connection().connection
        cur = raw_conn.cursor()
        cur.execute('PRAGMA table_info(users)')
        cols = {r[1] for r in cur.fetchall()}
        for required in ['oauth_provider', 'oauth_id', 'profile_picture']:
            assert required in cols, f'Missing auto-patched column: {required}'
        cur.close()
    finally:
        close_session()
