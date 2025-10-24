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
    # Introspect existing indexes and unique constraints
    indexes = session.execute(text("PRAGMA index_list('users')")).fetchall()
    index_sqls = []
    for idx in indexes:
        idx_name = idx[1]
        # Skip sqlite_autoindex (implicit PK/unique)
        if idx_name.startswith('sqlite_autoindex'):
            continue
        idx_info = session.execute(text(f"PRAGMA index_info('{idx_name}')")).fetchall()
        columns = [row[2] for row in idx_info]
        # Check if unique
        unique = idx[2]
        # Get index SQL if available
        idx_sql_row = session.execute(text(f"SELECT sql FROM sqlite_master WHERE type='index' AND name='{idx_name}'")).fetchone()
        if idx_sql_row and idx_sql_row[0]:
            index_sqls.append(idx_sql_row[0])
        else:
            # Fallback: reconstruct index SQL
            col_str = ', '.join(columns)
            if unique:
                index_sqls.append(f"CREATE UNIQUE INDEX IF NOT EXISTS {idx_name} ON users({col_str})")
            else:
                index_sqls.append(f"CREATE INDEX IF NOT EXISTS {idx_name} ON users({col_str})")

    # Rebuild table
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
    # Recreate all indexes and unique constraints
    for sql in index_sqls:
        session.execute(text(sql))
    session.execute(text('DROP TABLE users_legacy_tmp'))
    print('✅ SQLite users.password_hash is now nullable and all indexes/constraints are preserved.')


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
