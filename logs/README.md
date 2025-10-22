# Logs Directory

Application logs are stored here during runtime.

## Log Types

- `app.log` - Application logs
- `error.log` - Error logs
- `audit.log` - Security audit logs (if file-based logging enabled)

## .gitignore

Log files are excluded from version control:
```
logs/*.log
logs/*.txt
```

## Log Rotation

For production log rotation, see:
- `docs/operations/health-checks.md`
- Docker logging configuration in `docker-compose.yml`
