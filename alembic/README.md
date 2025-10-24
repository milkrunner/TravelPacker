# Alembic Database Migrations

This directory contains database migration files managed by Alembic.

## Structure

- `versions/` - Migration files (version controlled, DO NOT delete)
- `env.py` - Alembic environment configuration
- `script.py.mako` - Template for generating new migrations
- `README` - Alembic's default README

## Important Notes

### DO ✅

- **Commit all migration files** to version control
- **Review auto-generated migrations** before applying
- **Keep migrations in chronological order**
- **Test migrations** before deploying to production

### DON'T ❌

- **Don't edit applied migrations** - create a new one instead
- **Don't delete migration files** - they're part of the schema history
- **Don't skip migrations** - apply them in order
- **Don't modify `versions/` directly** - use Alembic commands

## Quick Commands

See `docs/operations/database-migrations.md` for full documentation.

```bash
# Apply all pending migrations
python scripts/db_migrate.py upgrade

# Create new migration
python scripts/db_migrate.py create "Your description here"

# Check current version
python scripts/db_migrate.py current

# View migration history
python scripts/db_migrate.py history
```

## Migration Files

Each migration file contains:

- **Revision ID** - Unique identifier for this migration
- **Revises** - Parent migration (previous version)
- **upgrade()** - Function to apply schema changes
- **downgrade()** - Function to rollback schema changes

Example:

```python
"""Add email_verified column to users

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2025-10-24 12:00:00
"""

def upgrade():
    # Apply changes
    op.add_column('users', sa.Column('email_verified', sa.Boolean()))

def downgrade():
    # Revert changes
    op.drop_column('users', 'email_verified')
```

## See Also

- Main documentation: `docs/operations/database-migrations.md`
- Migration script: `scripts/db_migrate.py`
- Database config: `src/database/__init__.py`
- Alembic config: `alembic.ini`
