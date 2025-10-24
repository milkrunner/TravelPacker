"""
Database configuration and session management
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment (PostgreSQL only)
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Please set it to your PostgreSQL connection string."
    )

if 'postgresql' not in DATABASE_URL:
    raise ValueError(
        f"Only PostgreSQL is supported. Invalid DATABASE_URL: {DATABASE_URL}"
    )

# Engine configuration for PostgreSQL performance
engine_config = {
    'echo': False,  # Set to True for SQL query logging
    'pool_pre_ping': True,  # Verify connections before using
    'pool_recycle': 3600,  # Recycle connections after 1 hour
    'poolclass': QueuePool,
    'pool_size': 20,
    'max_overflow': 40,
    'pool_timeout': 15,
    'connect_args': {
        'connect_timeout': int(os.getenv('POSTGRES_CONNECT_TIMEOUT', '5')),
        'options': '-c statement_timeout=30000',
        'application_name': 'niknotes_app',
    },
    'execution_options': {
        'isolation_level': 'READ COMMITTED',
    }
}

# Create PostgreSQL engine
try:
    engine = create_engine(DATABASE_URL, **engine_config)
    # Test connectivity
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print(f"✅ PostgreSQL connected: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}")
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")
    print("Please check your DATABASE_URL and ensure PostgreSQL is running.")
    raise

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
db_session = Session  # Alias for compatibility

# Base class for models
Base = declarative_base()


def init_db():
    """Initialize the database using Alembic migrations
    
    This function runs pending migrations to ensure the database schema is up to date.
    Use 'alembic upgrade head' manually for more control, or this will run automatically.
    """
    from alembic.config import Config
    from alembic import command
    import os
    from pathlib import Path
    
    # Import models to ensure they're registered with Base.metadata
    from src.database.models import Trip, PackingItem, Traveler, User
    from src.database.audit_models import AuditLog
    
    try:
        # Get the alembic.ini file path
        alembic_ini = Path(__file__).parent.parent.parent / 'alembic.ini'
        
        if not alembic_ini.exists():
            print("⚠️  alembic.ini not found. Falling back to create_all() for development.")
            Base.metadata.create_all(bind=engine)
            return
        
        # Configure Alembic
        alembic_cfg = Config(str(alembic_ini))
        
        # Run migrations to head (latest version)
        command.upgrade(alembic_cfg, "head")
        
    except Exception as e:
        print(f"⚠️  Migration error: {e}")
        print("   Falling back to create_all() for development.")
        Base.metadata.create_all(bind=engine)


def get_session():
    """Get a database session"""
    return Session()


def close_session():
    """Close the current session"""
    Session.remove()


def test_connection():
    """Test database connectivity
    
    Returns:
        bool: True if database connection is healthy, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False
