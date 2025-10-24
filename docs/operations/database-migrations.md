# Database Migrations with Alembic

This document describes how to manage database schema changes using Alembic migrations.

## Overview

The NikNotes application now uses **Alembic** for database migrations instead of ad-hoc `Base.metadata.create_all()` calls. This provides:

- ✅ **Version-controlled schema changes** - All schema changes are tracked in version control
- ✅ **Reliable upgrades and rollbacks** - Apply or revert changes safely
- ✅ **Team collaboration** - Multiple developers can manage schema changes
- ✅ **Production-safe** - Test migrations before deploying
- ✅ **Auto-generation** - Alembic detects model changes automatically

## Quick Start

### Check Current Database Version

```bash
python scripts/db_migrate.py current
```

### Apply All Pending Migrations

```bash
python scripts/db_migrate.py upgrade
```

### Create a New Migration

When you modify models in `src/database/models.py`:

```bash
python scripts/db_migrate.py create "Add user profile fields"
```

This will auto-generate a migration file in `alembic/versions/`.

### Rollback Last Migration

```bash
python scripts/db_migrate.py downgrade
```

### View Migration History

```bash
python scripts/db_migrate.py history
```

## Migration Workflow

### 1. Making Schema Changes

1. **Edit models** in `src/database/models.py` or `src/database/audit_models.py`
2. **Create migration** with descriptive message:

   ```bash
   python scripts/db_migrate.py create "Add email_verified column to users"
   ```

3. **Review generated migration** in `alembic/versions/XXXXX_description.py`
4. **Test migration** locally:

   ```bash
   python scripts/db_migrate.py upgrade
   ```

5. **Verify database** - Check that changes are correct
6. **Commit migration file** to version control

### 2. Applying Migrations (Development/Production)

**Local Development:**

```bash
python scripts/db_migrate.py upgrade
```

**Docker:**
Migrations run automatically on container startup via `init_db()` in `src/database/__init__.py`

**Manual (if needed):**

```bash
# Inside container
docker exec niknotes-web python scripts/db_migrate.py upgrade

# Or via docker-compose
docker-compose exec web python scripts/db_migrate.py upgrade
```

### 3. Rolling Back Changes

**Rollback one migration:**

```bash
python scripts/db_migrate.py downgrade
```

**Rollback to specific version:**

```bash
python scripts/db_migrate.py downgrade abc123def456
```

**Rollback all migrations:**

```bash
python scripts/db_migrate.py downgrade base
```

## Migration Commands Reference

### `upgrade [revision]`

Apply migrations up to specified revision (default: `head` = latest)

```bash
python scripts/db_migrate.py upgrade          # Apply all pending
python scripts/db_migrate.py upgrade +1       # Apply next one
python scripts/db_migrate.py upgrade abc123   # Upgrade to specific version
```

### `downgrade [revision]`

Rollback migrations to specified revision (default: `-1` = one step back)

```bash
python scripts/db_migrate.py downgrade        # Rollback one
python scripts/db_migrate.py downgrade -2     # Rollback two
python scripts/db_migrate.py downgrade abc123 # Rollback to specific version
python scripts/db_migrate.py downgrade base   # Rollback all
```

### `create "message"`

Create a new migration with auto-detected model changes

```bash
python scripts/db_migrate.py create "Add OAuth fields to User model"
```

### `current`

Show the current database migration version

```bash
python scripts/db_migrate.py current
```

### `history`

Show all migrations in chronological order

```bash
python scripts/db_migrate.py history
```

### `stamp [revision]`

Mark database as being at a specific revision without running migrations

```bash
python scripts/db_migrate.py stamp head       # Mark as latest
python scripts/db_migrate.py stamp abc123     # Mark as specific version
```

**Use case:** Existing database with tables already created - stamp to mark as migrated.

## Directory Structure

```file
TravelPacker/
├── alembic/                    # Alembic configuration
│   ├── versions/               # Migration files (version controlled)
│   │   └── 36a04cd7adbc_initial_schema.py
│   ├── env.py                  # Alembic environment configuration
│   ├── script.py.mako         # Migration template
│   └── README
├── alembic.ini                 # Alembic configuration file
├── scripts/
│   └── db_migrate.py          # Migration management script
└── src/
    └── database/
        ├── __init__.py         # Database initialization (runs migrations)
        ├── models.py           # SQLAlchemy models
        └── audit_models.py     # Audit log models
```

## How It Works

### Automatic Migration on Startup

The `init_db()` function in `src/database/__init__.py` automatically runs `alembic upgrade head` when the application starts. This ensures the database is always up-to-date.

```python
def init_db():
    """Initialize the database using Alembic migrations"""
    from alembic.config import Config
    from alembic import command

    # ... configuration ...
    command.upgrade(alembic_cfg, "head")
```

### Alembic Configuration

**`alembic.ini`** - Main configuration file

- Script location: `alembic/`
- Version files: `alembic/versions/`
- Database URL: Loaded from `DATABASE_URL` environment variable

**`alembic/env.py`** - Environment configuration

- Loads `DATABASE_URL` from `.env` file
- Imports all models for autogenerate
- Configures logging and connection

### Migration Files

Generated in `alembic/versions/` with format: `{revision}_{slug}.py`

Example migration:

```python
"""Add email_verified column to users

Revision ID: def456ghi789
Revises: abc123def456
Create Date: 2025-10-24 12:00:00

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users',
        sa.Column('email_verified', sa.Boolean(), nullable=True))

def downgrade():
    op.drop_column('users', 'email_verified')
```

## Common Scenarios

### Starting Fresh Database

1. Ensure PostgreSQL is running
2. Set `DATABASE_URL` in `.env`
3. Run migrations:

```bash
python scripts/db_migrate.py upgrade
```

### Existing Database (First Time Setup)

If your database already has tables:

1. Create initial migration:

   ```bash
   python scripts/db_migrate.py create "Initial schema"
   ```

2. **Empty the generated migration** (tables already exist)

3. Stamp database as current:

   ```bash
   python scripts/db_migrate.py stamp head
   ```

```bash
python scripts/db_migrate.py create "Initial schema"
```

**Empty the generated migration** (tables already exist)
Stamp database as current:

```bash
python scripts/db_migrate.py stamp head
```

### Adding a New Column

1. Edit model in `src/database/models.py`:

```python
class User(Base):
    # ... existing fields ...
    phone_number = Column(String(20), nullable=True)
```

Generate migration:

```bash
python scripts/db_migrate.py create "Add phone_number to users"
```

Review migration in `alembic/versions/`
Apply migration:

```bash
python scripts/db_migrate.py upgrade
```

### Renaming a Column

**Manual edit required** - Alembic can't detect renames automatically.

1. Create migration:

```bash
python scripts/db_migrate.py create "Rename email to email_address"
```

Edit generated migration:

   ```python
   def upgrade():
       op.alter_column('users', 'email', new_column_name='email_address')

   def downgrade():
       op.alter_column('users', 'email_address', new_column_name='email')
   ```

### Complex Schema Changes

For complex changes (e.g., splitting tables, data migrations):

1. Create empty migration:

```bash
python scripts/db_migrate.py create "Split user profile data"
```

Manually write `upgrade()` and `downgrade()` functions
Test thoroughly before applying to production

## Best Practices

### ✅ DO

- **Always review** auto-generated migrations before applying
- **Test migrations** on development database first
- **Write reversible migrations** - always implement `downgrade()`
- **Use descriptive messages** for migration names
- **Commit migration files** to version control
- **Keep migrations small** - one logical change per migration
- **Test rollback** - ensure `downgrade()` works correctly

### ❌ DON'T

- **Don't edit applied migrations** - create a new migration instead
- **Don't skip migrations** - apply them in order
- **Don't modify production directly** - use migrations
- **Don't delete migration files** - they're part of history
- **Don't use `--sql` mode in production** - apply migrations programmatically

## Troubleshooting

### Migration Out of Sync

**Symptom:** "Can't locate revision 'abc123'"

**Solution:**

```bash
# Check current version
python scripts/db_migrate.py current

# View migration history
python scripts/db_migrate.py history

# Stamp to correct version
python scripts/db_migrate.py stamp abc123
```

### Migration Failed

**Symptom:** Error during `upgrade`

**Solution:**

1. Check error message for SQL/constraint issues
2. Fix the issue (manual SQL or update migration)
3. If partial migration applied, rollback:

```bash
python scripts/db_migrate.py downgrade
```

Fix migration file and try again

### Merge Conflicts in Migrations

**Symptom:** Two branches created migrations with same parent

**Solution:**

```bash
# Merge branches in Alembic
alembic merge -m "Merge migrations" head1 head2
```

### Reset to Clean State

**⚠️ WARNING: This deletes all data!**

```bash
# Drop all tables
python scripts/db_migrate.py downgrade base

# Reapply all migrations
python scripts/db_migrate.py upgrade head
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] All migrations tested locally
- [ ] Migration files committed to version control
- [ ] Database backup created
- [ ] Downtime plan (if schema changes are breaking)
- [ ] Rollback plan tested

### Deployment Process

1. **Backup database:**

   ```bash
   pg_dump -U username -d database_name > backup_$(date +%Y%m%d).sql
   ```

2. **Apply migrations:**

   ```bash
   # Via script
   python scripts/db_migrate.py upgrade

   # Or via Docker
   docker-compose exec web python scripts/db_migrate.py upgrade
   ```

3. **Verify:**

   ```bash
   python scripts/db_migrate.py current
   ```

4. **Monitor application** for errors

### Rollback in Production

If deployment fails:

1. **Rollback migration:**

   ```bash
   python scripts/db_migrate.py downgrade
   ```

2. **Deploy previous application version**

3. **Restore database backup if needed:**

   ```bash
   psql -U username -d database_name < backup_20251024.sql
   ```

## Advanced Topics

### Data Migrations

For migrations that modify data (not just schema):

```python
def upgrade():
    # Get connection
    connection = op.get_bind()

    # Run data transformation
    connection.execute(
        "UPDATE users SET status = 'active' WHERE status IS NULL"
    )

def downgrade():
    connection = op.get_bind()
    connection.execute(
        "UPDATE users SET status = NULL WHERE status = 'active'"
    )
```

### Conditional Migrations

Check if column/table exists before altering:

```python
from alembic import op
from sqlalchemy import inspect

def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    if 'old_column' in [c['name'] for c in inspector.get_columns('users')]:
        op.drop_column('users', 'old_column')
```

### Multiple Databases

For separate read/write databases, configure multiple Alembic environments.

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Migration History

| Revision     | Description                                                           | Date       |
| ------------ | --------------------------------------------------------------------- | ---------- |
| 36a04cd7adbc | Initial schema with users, trips, travelers, packing_items, audit_log | 2025-10-24 |

---

**Next Steps:**

1. Familiarize yourself with migration commands
2. Test creating a simple migration (e.g., add a column)
3. Practice rollback procedures
4. Document team migration workflow
