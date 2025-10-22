# Data Directory

This directory contains application data files including databases and user-generated content.

## Files

- `niknotes.db` - SQLite database (development/local)
- PostgreSQL is used in production (see `docker-compose.yml`)

## .gitignore

Data files are excluded from version control:

```text
data/*.db
data/*.sqlite
data/*.sqlite3
```

## Backups

For production backups, see:

- `scripts/ops/` - Backup/restore scripts
- `docs/operations/health-checks.md` - Monitoring guide
