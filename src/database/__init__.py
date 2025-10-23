"""
Database configuration and session management
"""

import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///niknotes.db')
USE_POSTGRES = os.getenv('USE_POSTGRES', 'auto').lower()  # values: 'true','false','auto'

# Performance optimization settings
is_postgresql = 'postgresql' in DATABASE_URL and USE_POSTGRES != 'false'

# Engine configuration for blazing fast performance
engine_config = {
    'echo': False,  # Set to True for SQL query logging
    'pool_pre_ping': True,  # Verify connections before using
    'pool_recycle': 3600,  # Recycle connections after 1 hour
}

if is_postgresql:
    # PostgreSQL-specific optimizations (shorter initial connect timeout for fast fallback)
    engine_config.update({
        'poolclass': QueuePool,
        'pool_size': 20,
        'max_overflow': 40,
        'pool_timeout': 15,
        'connect_args': {
            'connect_timeout': int(os.getenv('POSTGRES_CONNECT_TIMEOUT', '3')),  # fail fast
            'options': '-c statement_timeout=30000',
            'application_name': 'niknotes_app',
        },
        'execution_options': {
            'isolation_level': 'READ COMMITTED',
        }
    })
else:
    # SQLite-specific settings
    engine_config['connect_args'] = {'check_same_thread': False}

# Try to create engine with fallback to SQLite
engine = None
if is_postgresql and USE_POSTGRES != 'false':
    try:
        engine = create_engine(DATABASE_URL, **engine_config)
        # Lightweight connectivity check (no stack trace on failure)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print(f"✅ PostgreSQL connected: {DATABASE_URL}")
    except Exception as e:
        # Auto fallback only if USE_POSTGRES == 'auto'; if 'true', surface error
        if USE_POSTGRES == 'true':
            print(f"❌ PostgreSQL connection failed (USE_POSTGRES=true): {e}")
            raise
        print(f"⚠️ PostgreSQL unavailable ({type(e).__name__}: {e}). Fallback → SQLite.\n"
              f"   Please check your DATABASE_URL and POSTGRES_PASSWORD environment variables.")
        DATABASE_URL = 'sqlite:///niknotes.db'
        is_postgresql = False
        engine_config = {
            'echo': False,
            'pool_pre_ping': True,
            'connect_args': {'check_same_thread': False}
        }
        engine = create_engine(DATABASE_URL, **engine_config)
        print("✅ SQLite database ready: niknotes.db")
else:
    # Directly use SQLite
    if 'sqlite' not in DATABASE_URL:
        DATABASE_URL = 'sqlite:///niknotes.db'
    engine = create_engine(DATABASE_URL, **engine_config)
    print("✅ SQLite database initialized")

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
db_session = Session  # Alias for compatibility

# Base class for models
Base = declarative_base()


def init_db():
    """Initialize the database - create all tables"""
    from src.database.models import Trip, PackingItem, Traveler, User
    from src.database.audit_models import AuditLog
    Base.metadata.create_all(bind=engine)

    # --- Automatic SQLite schema patch for newly added columns (OAuth/Google Sign-In) ---
    # Problem: Existing local niknotes.db created before adding oauth columns -> OperationalError.
    # Strategy: For SQLite only, detect missing columns in 'users' table and ALTER TABLE to add them.
    # Safe because ALTER TABLE ADD COLUMN in SQLite does not rewrite existing data and new columns are nullable.
    if not is_postgresql and engine is not None:
        try:
            with engine.connect() as conn:
                # Get existing column names
                result = conn.execute(text("PRAGMA table_info(users)"))
                existing_cols = {row[1] for row in result.fetchall()}
                required_cols = {
                    'oauth_provider': "ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50)",
                    'oauth_id': "ALTER TABLE users ADD COLUMN oauth_id VARCHAR(255)",
                    'profile_picture': "ALTER TABLE users ADD COLUMN profile_picture VARCHAR(500)"
                }
                added = []
                for col, stmt in required_cols.items():
                    if col not in existing_cols:
                        conn.execute(text(stmt))
                        added.append(col)
                # Create composite index if missing (check sqlite_master)
                if 'oauth_provider' in existing_cols or 'oauth_provider' in added:
                    idx_check = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_user_oauth'"))
                    if not idx_check.fetchone():
                        conn.execute(text("CREATE INDEX idx_user_oauth ON users(oauth_provider, oauth_id)"))
                        added.append('idx_user_oauth')
                if added:
                    print(f"🔧 SQLite schema auto-patch applied: {', '.join(added)}")
        except Exception as e:
            # Non-fatal: continue without patch (login will still fail, but we surface message)
            print(f"⚠️ SQLite schema patch failed: {e}")


def get_session():
    """Get a database session"""
    return Session()


def close_session():
    """Close the current session"""
    Session.remove()
