"""Maintenance script: Normalize password_hash nullability for legacy databases.

Purpose:
    Older SQLite/Postgres schemas may have `users.password_hash` defined as NOT NULL.
    For OAuth / Google Sign-In users we allow it to be NULL. This script adjusts the schema.

Behavior:
    - Detects if password_hash is NOT NULL.
    - For SQLite: Rebuilds table only if necessary (since ALTER COLUMN is limited).
      Simpler approach: If NOT NULL, but there exist rows with empty string, keep them; we just allow future NULLs.
      We emulate nullability by creating a new table and copying data.
    - For Postgres: Executes `ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL`.

Usage:
    python scripts/migrations/normalize_password_nullability.py

Idempotent: Safe to run multiple times.
"""

import os
import sys
from contextlib import contextmanager
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database import engine, get_session, close_session

@contextmanager
def session_scope():
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        close_session()


def is_sqlite():
    return engine.dialect.name == 'sqlite'


def detect_not_null(session):
    if is_sqlite():
        result = session.execute(text('PRAGMA table_info(users)'))
        for row in result.fetchall():
            # row[1] = name, row[3] = notnull flag (1 means NOT NULL)
            if row[1] == 'password_hash':
                return row[3] == 1
        return False
    else:  # Postgres path
        result = session.execute(text("""
            SELECT is_nullable FROM information_schema.columns
            WHERE table_name='users' AND column_name='password_hash'
        """))
        row = result.fetchone()
        if not row:
            return False
        return row[0] == 'NO'  # NO means NOT NULL


def normalize_sqlite(session):
    # SQLite cannot directly drop NOT NULL constraint; need table rebuild.
    print('🔧 Normalizing SQLite users.password_hash to be nullable...')
    # Fetch schema definition
    # Simplified approach: create new table with desired schema, copy data, drop old, rename.
    session.execute(text('ALTER TABLE users RENAME TO users_legacy_tmp'))
    session.execute(text('''
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            username VARCHAR(80) NOT NULL,
            email VARCHAR(120) NOT NULL,
            password_hash VARCHAR(255), -- now nullable
            is_active BOOLEAN,
            created_at DATETIME,
            last_login DATETIME,
            oauth_provider VARCHAR(50),
            oauth_id VARCHAR(255),
            profile_picture VARCHAR(500)
        )
    '''))
    # Copy data
    session.execute(text('''
        INSERT INTO users (id, username, email, password_hash, is_active, created_at, last_login, oauth_provider, oauth_id, profile_picture)
        SELECT id, username, email, password_hash, is_active, created_at, last_login, oauth_provider, oauth_id, profile_picture
        FROM users_legacy_tmp
    '''))
    # Create index recreated if existed
    session.execute(text('CREATE INDEX IF NOT EXISTS idx_user_oauth ON users(oauth_provider, oauth_id)'))
    session.execute(text('DROP TABLE users_legacy_tmp'))
    print('✅ SQLite users.password_hash is now nullable.')


def normalize_postgres(session):
    print('🔧 Normalizing Postgres users.password_hash to be nullable...')
    session.execute(text('ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL'))
    print('✅ Postgres users.password_hash is now nullable.')


def main():
    if engine is None:
        print('❌ No database engine available.')
        return
    with session_scope() as session:
        not_null = detect_not_null(session)
        if not not_null:
            print('ℹ️ password_hash already nullable – nothing to do.')
            return
        if is_sqlite():
            normalize_sqlite(session)
        else:
            normalize_postgres(session)

if __name__ == '__main__':
    main()
