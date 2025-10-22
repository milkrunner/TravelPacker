# 🐳 Docker Quick Reference

## Essential Commands

### Start/Stop

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a service
docker-compose restart web
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f web
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Database

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U niknotes_user -d niknotes_db

# Run migrations
docker-compose exec web python scripts/migrate.py create

# Backup database
docker-compose exec postgres pg_dump -U niknotes_user niknotes_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U niknotes_user niknotes_db < backup.sql
```

### Cache

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Clear cache
docker-compose exec redis redis-cli FLUSHDB

# Check stats
docker-compose exec redis redis-cli INFO stats
```

### Status

```bash
# Check container status
docker-compose ps

# Check resource usage
docker stats

# Check health
docker inspect niknotes-web | jq '.[0].State.Health'
```

### Rebuild

```bash
# Rebuild and restart
docker-compose up -d --build

# Force rebuild (no cache)
docker-compose build --no-cache
```

## Troubleshooting

```bash
# View container logs
docker-compose logs web --tail=100

# Access container shell
docker-compose exec web bash

# Test database connection
docker-compose exec web python -c "from src.database import get_db; next(get_db()); print('OK')"

# Test Redis connection
docker-compose exec web python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"

# Remove everything and start fresh
docker-compose down -v
docker-compose up -d
```

## URLs

- **Web App**: <http://localhost:5000>
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Environment Variables

Set in `.env` file:

```bash
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://niknotes_user:niknotes_pass@postgres:5432/niknotes_db
REDIS_URL=redis://redis:6379/0
```

See [../docs/DOCKER_DEPLOYMENT.md](../docs/DOCKER_DEPLOYMENT.md) for full documentation.
