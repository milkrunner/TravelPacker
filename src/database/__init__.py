"""
Database configuration and session management
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///niknotes.db')

# Performance optimization settings
is_postgresql = 'postgresql' in DATABASE_URL

# Engine configuration for blazing fast performance
engine_config = {
    'echo': False,  # Set to True for SQL query logging
    'pool_pre_ping': True,  # Verify connections before using
    'pool_recycle': 3600,  # Recycle connections after 1 hour
}

if is_postgresql:
    # PostgreSQL-specific optimizations
    engine_config.update({
        'poolclass': QueuePool,
        'pool_size': 20,  # Number of connections to maintain
        'max_overflow': 40,  # Max additional connections beyond pool_size
        'pool_timeout': 30,  # Timeout for getting connection from pool
        'connect_args': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30s query timeout
            'application_name': 'niknotes_app',
        },
        'execution_options': {
            'isolation_level': 'READ COMMITTED',  # Better concurrency
        }
    })
else:
    # SQLite-specific settings
    engine_config['connect_args'] = {'check_same_thread': False}

# Try to create engine with fallback to SQLite
try:
    engine = create_engine(DATABASE_URL, **engine_config)
    # Test the connection
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print(f"✅ Database connected: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'SQLite'}")
except Exception as e:
    if is_postgresql:
        print(f"⚠️  PostgreSQL connection failed: {e}")
        print("🔄 Falling back to SQLite database...")
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
        print(f"❌ Database connection failed: {e}")
        raise

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


def get_session():
    """Get a database session"""
    return Session()


def close_session():
    """Close the current session"""
    Session.remove()
