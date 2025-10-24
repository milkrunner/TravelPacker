"""
Database migration script to add users table and user_id to trips
Run this script to update existing database schema for authentication support
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_session, close_session
from src.database.models import User, Trip as DBTrip
from sqlalchemy import text


def run_migration():
    """Run the migration to add users table"""
    session = get_session()
    
    try:
        print("Starting database migration for authentication...")
        
        # Check if users table already exists
        result = session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ))
        
        if result.fetchone():
            print("✓ Users table already exists")
        else:
            print("✗ Users table doesn't exist - creating schema...")
            # The table will be created by init_db() when we import it
            from src.database import init_db
            init_db()
            print("✓ Created users table")
        
        # Check if trips table has user_id column
        result = session.execute(text("PRAGMA table_info(trips)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'user_id' in columns:
            print("✓ Trips table already has user_id column")
        else:
            print("✗ Adding user_id column to trips table...")
            
            # Create a default admin user for existing trips
            default_user = session.query(User).filter_by(username='admin').first()
            if not default_user:
                print("Creating default admin user...")
                default_user = User(
                    id='user_default_admin',
                    username='admin',
                    email='admin@niknotes.local',
                    created_at=datetime.utcnow()
                )
                default_user.set_password('changeme123')  # Change this!
                session.add(default_user)
                session.commit()
                print("✓ Created admin user (username: admin, password: changeme123)")
                print("  ⚠️  IMPORTANT: Change the admin password after first login!")
            
            # Add user_id column with default value
            session.execute(text(
                f"ALTER TABLE trips ADD COLUMN user_id TEXT DEFAULT '{default_user.id}'"
            ))
            session.commit()
            print("✓ Added user_id column to trips table")
            
            # Add foreign key constraint (SQLite doesn't support adding FK after creation)
            # We'll enforce this in the application layer
            print("Note: Foreign key constraint enforced in application layer")
        
        # Count trips and users
        trip_count = session.query(DBTrip).count()
        user_count = session.query(User).count()
        
        print("\nMigration completed successfully!")
        print(f"Database status:")
        print(f"  - {user_count} user(s)")
        print(f"  - {trip_count} trip(s)")
        
        if user_count == 0:
            print("\n⚠️  No users found. Creating default admin user...")
            admin_user = User(
                id='user_admin_' + datetime.utcnow().strftime('%Y%m%d_%H%M%S'),
                username='admin',
                email='admin@niknotes.local',
                created_at=datetime.utcnow()
            )
            admin_user.set_password('changeme123')
            session.add(admin_user)
            session.commit()
            print("✓ Created admin user")
            print("  Username: admin")
            print("  Password: changeme123")
            print("  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False
    
    finally:
        close_session()


if __name__ == '__main__':
    print("=" * 60)
    print("NikNotes Database Migration - Authentication Support")
    print("=" * 60)
    print()
    
    success = run_migration()
    
    print()
    print("=" * 60)
    if success:
        print("Migration completed successfully!")
        print("\nNext steps:")
        print("1. Start the application: python web_app.py")
        print("2. Login with admin credentials or register a new account")
        print("3. If you used the default admin user, CHANGE THE PASSWORD!")
    else:
        print("Migration failed. Please check the errors above.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
