# Database Migration Quick Reference

Quick commands for common migration tasks.

## Most Used Commands

### Apply Migrations

```bash
python scripts/db_migrate.py upgrade
```

### Create New Migration

```bash
python scripts/db_migrate.py create "Your description"
```

### Check Status

```bash
python scripts/db_migrate.py current
```

## Workflow Example

### Adding a New Column

1. **Edit the model** (`src/database/models.py`):

   ```python
   class User(Base):
       # ... existing fields ...
       phone_number = Column(String(20), nullable=True)
   ```

2. **Generate migration**:

   ```bash
   python scripts/db_migrate.py create "Add phone_number to users"
   ```

3. **Review** the generated file in `alembic/versions/`

4. **Apply migration**:

   ```bash
   python scripts/db_migrate.py upgrade
   ```

5. **Commit** the migration file to git

## Emergency Procedures

### Rollback Last Migration

```bash
python scripts/db_migrate.py downgrade
```

### Check What Will Be Applied

```bash
python scripts/db_migrate.py history
python scripts/db_migrate.py current
```

### Database Backup (Before Risky Migration)

```bash
# PostgreSQL
pg_dump -U username -d database_name > backup.sql

# Restore if needed
psql -U username -d database_name < backup.sql
```

## Common Issues

### "Can't locate revision"

**Solution:** Check history and stamp to correct version

```bash
python scripts/db_migrate.py history
python scripts/db_migrate.py stamp abc123
```

### Migration Failed Halfway

**Solution:** Rollback and fix

```bash
python scripts/db_migrate.py downgrade
# Fix issue
python scripts/db_migrate.py upgrade
```

### New Team Member / Fresh Database

**Solution:** Just run upgrade

```bash
python scripts/db_migrate.py upgrade
```

## Best Practices Checklist

- [ ] Review auto-generated migrations before applying
- [ ] Test migrations on development database first
- [ ] Write descriptive migration messages
- [ ] Implement both `upgrade()` and `downgrade()` functions
- [ ] Commit migration files to version control
- [ ] Backup database before risky migrations
- [ ] Document data migrations in migration file comments

## See Full Documentation

For complete details: `docs/operations/database-migrations.md`
