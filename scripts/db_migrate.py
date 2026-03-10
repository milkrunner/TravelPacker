#!/usr/bin/env python
"""
Database migration management script using Alembic

Usage:
    python scripts/db_migrate.py upgrade       # Apply all pending migrations
    python scripts/db_migrate.py downgrade     # Rollback one migration
    python scripts/db_migrate.py current       # Show current migration version
    python scripts/db_migrate.py history       # Show migration history
    python scripts/db_migrate.py create "description"  # Create new migration
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from dotenv import load_dotenv

from alembic import command

# Load environment variables
load_dotenv()


def get_alembic_config():
    """Get Alembic configuration"""
    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        print(f"❌ alembic.ini not found at {alembic_ini}")
        sys.exit(1)

    config = Config(str(alembic_ini))
    return config


def upgrade(revision="head"):
    """Apply migrations up to specified revision (default: head)"""
    print(f"🔄 Upgrading database to revision: {revision}")
    config = get_alembic_config()
    command.upgrade(config, revision)
    print("✅ Database upgraded successfully")


def downgrade(revision="-1"):
    """Rollback migrations to specified revision (default: -1 for one step back)"""
    print(f"🔄 Downgrading database to revision: {revision}")
    config = get_alembic_config()
    command.downgrade(config, revision)
    print("✅ Database downgraded successfully")


def current():
    """Show current migration version"""
    print("📊 Current database version:")
    config = get_alembic_config()
    command.current(config)


def history():
    """Show migration history"""
    print("📜 Migration history:")
    config = get_alembic_config()
    command.history(config)


def create(message):
    """Create a new migration"""
    if not message:
        print("❌ Please provide a migration message")
        print('   Usage: python scripts/db_migrate.py create "your message here"')
        sys.exit(1)

    print(f"📝 Creating new migration: {message}")
    config = get_alembic_config()
    command.revision(config, message=message, autogenerate=True)
    print("✅ Migration created successfully")


def stamp(revision="head"):
    """Mark the database as being at a specific revision without running migrations"""
    print(f"🏷️  Stamping database with revision: {revision}")
    config = get_alembic_config()
    command.stamp(config, revision)
    print("✅ Database stamped successfully")


def show_help():
    """Show help message"""
    print(__doc__)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    action = sys.argv[1].lower()

    # Check DATABASE_URL is set
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL environment variable is not set")
        print("   Please set it to your PostgreSQL connection string")
        sys.exit(1)

    try:
        if action == "upgrade":
            revision = sys.argv[2] if len(sys.argv) > 2 else "head"
            upgrade(revision)
        elif action == "downgrade":
            revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
            downgrade(revision)
        elif action == "current":
            current()
        elif action == "history":
            history()
        elif action == "create":
            message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
            create(message)
        elif action == "stamp":
            revision = sys.argv[2] if len(sys.argv) > 2 else "head"
            stamp(revision)
        elif action in ["help", "--help", "-h"]:
            show_help()
        else:
            print(f"❌ Unknown action: {action}")
            show_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
