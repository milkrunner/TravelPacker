"""
Database migration: Add Google OAuth support to User model

This migration adds OAuth fields to support Google authentication:
- oauth_provider: String field to store the OAuth provider name ('google', 'github', etc.)
- oauth_id: String field to store the provider's user ID
- profile_picture: String field to store the user's profile picture URL
- Makes password_hash nullable for OAuth-only users
- Adds composite index for OAuth lookups
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import text

from src.database import close_session, get_session


def run_migration():
    """Run the OAuth migration"""
    session = get_session()

    try:
        print("🔧 Running OAuth migration...")

        # Check if columns already exist
        result = session.execute(
            text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='users' AND column_name='oauth_provider'
        """)
        )

        if result.fetchone():
            print("✅ Migration already applied - OAuth columns exist")
            return

        # Add OAuth columns
        print("📝 Adding oauth_provider column...")
        session.execute(
            text("""
            ALTER TABLE users
            ADD COLUMN oauth_provider VARCHAR(50)
        """)
        )

        print("📝 Adding oauth_id column...")
        session.execute(
            text("""
            ALTER TABLE users
            ADD COLUMN oauth_id VARCHAR(255)
        """)
        )

        print("📝 Adding profile_picture column...")
        session.execute(
            text("""
            ALTER TABLE users
            ADD COLUMN profile_picture VARCHAR(500)
        """)
        )

        print("📝 Making password_hash nullable...")
        session.execute(
            text("""
            ALTER TABLE users
            ALTER COLUMN password_hash DROP NOT NULL
        """)
        )

        print("📝 Creating index for OAuth lookups...")
        session.execute(
            text("""
            CREATE INDEX idx_user_oauth ON users(oauth_provider, oauth_id)
        """)
        )

        session.commit()

        print("✅ OAuth migration completed successfully!")
        print("\n📋 Migration Summary:")
        print("  - Added oauth_provider column")
        print("  - Added oauth_id column")
        print("  - Added profile_picture column")
        print("  - Made password_hash nullable (for OAuth-only users)")
        print("  - Created composite index idx_user_oauth")

    except Exception as e:
        session.rollback()
        print(f"❌ Migration failed: {e}")
        print("\n💡 Troubleshooting:")
        print("  1. Ensure PostgreSQL is running")
        print("  2. Check DATABASE_URL in .env file")
        print("  3. Verify database user has ALTER TABLE permissions")
        raise

    finally:
        close_session()


if __name__ == "__main__":
    print("🚀 Starting OAuth migration for NikNotes...")
    print("=" * 60)
    run_migration()
    print("=" * 60)
    print("🎉 Migration process completed!")
