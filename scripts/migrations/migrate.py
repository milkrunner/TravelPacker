"""
Database migration script
Initialize or upgrade the database schema
"""

from src.database import init_db, engine, Base
from src.database.models import Trip, PackingItem, Traveler


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    init_db()
    print("✓ Database tables created successfully!")
    
    # Print table information
    print("\nCreated tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")


def drop_tables():
    """Drop all database tables (WARNING: destructive!)"""
    response = input("⚠️  This will DELETE ALL DATA. Type 'yes' to continue: ")
    if response.lower() == 'yes':
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("✓ All tables dropped.")
    else:
        print("Operation cancelled.")


def reset_database():
    """Drop and recreate all tables (WARNING: destructive!)"""
    response = input("⚠️  This will DELETE ALL DATA and recreate tables. Type 'yes' to continue: ")
    if response.lower() == 'yes':
        print("Resetting database...")
        Base.metadata.drop_all(bind=engine)
        print("✓ Tables dropped.")
        init_db()
        print("✓ Tables recreated.")
        print("\nDatabase reset complete!")
    else:
        print("Operation cancelled.")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [create|drop|reset]")
        print("  create - Create all tables")
        print("  drop   - Drop all tables")
        print("  reset  - Drop and recreate all tables")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        create_tables()
    elif command == 'drop':
        drop_tables()
    elif command == 'reset':
        reset_database()
    else:
        print(f"Unknown command: {command}")
        print("Use: create, drop, or reset")
        sys.exit(1)
