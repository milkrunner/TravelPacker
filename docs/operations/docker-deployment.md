# 🐳 Docker Deployment Guide

Deploy NikNotes as a containerized application with PostgreSQL and Redis for blazing fast performance!

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ ([Download](https://www.docker.com/get-started))
- **Docker Compose** 2.0+ (included with Docker Desktop)
- **Gemini API Key** ([Get one free](https://makersuite.google.com/app/apikey))

### One-Command Deployment

```bash
# 1. Clone the repository (if needed)
git clone <your-repo-url>
cd NikNotes

# 2. Set your Gemini API key
export GEMINI_API_KEY=your_actual_api_key_here

# 3. Start all services
docker-compose up -d

# 4. Open browser
# http://localhost:5000
```

**That's it!** 🎉 Your app is running with:

- ✅ PostgreSQL database (port 5432)
- ✅ Redis cache (port 6379)
- ✅ NikNotes web app (port 5000)

---

## 📋 What Gets Deployed

### Container Architecture

```output
┌─────────────────────────────────────────┐
│         Docker Network                  │
│                                         │
│  ┌──────────────┐   ┌──────────────┐  │
│  │  PostgreSQL  │   │    Redis     │  │
│  │   (port      │   │   (port      │  │
│  │    5432)     │   │    6379)     │  │
│  └──────────────┘   └──────────────┘  │
│         ▲                  ▲           │
│         │                  │           │
│         └────────┬─────────┘           │
│                  │                     │
│         ┌────────▼─────────┐          │
│         │   NikNotes Web   │          │
│         │   Flask App      │          │
│         │   (port 5000)    │          │
│         └──────────────────┘          │
│                  │                     │
└──────────────────┼─────────────────────┘
                   │
            ┌──────▼──────┐
            │  localhost  │
            │  :5000      │
            └─────────────┘
```

### Services

1. **niknotes-postgres**

   - Image: `postgres:16-alpine`
   - Port: 5432
   - Volume: Persistent database storage
   - Performance: Optimized with connection pooling, parallel workers

2. **niknotes-redis**

   - Image: `redis:7-alpine`
   - Port: 6379
   - Volume: Persistent cache data (optional)
   - Config: 256MB memory, LRU eviction

3. **niknotes-web**
   - Build: From local Dockerfile
   - Port: 5000
   - Depends on: PostgreSQL, Redis
   - Auto-runs: Database migrations on startup

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.docker .env

# Edit with your values
nano .env
```

**Required:**

```bash
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

**Optional:**

```bash
# Database (defaults are fine for Docker)
DATABASE_URL=postgresql://niknotes_user:niknotes_pass@postgres:5432/niknotes_db

# Redis (defaults are fine for Docker)
REDIS_URL=redis://redis:6379/0

# Flask
FLASK_ENV=production
FLASK_DEBUG=0

# Custom database credentials
POSTGRES_DB=niknotes_db
POSTGRES_USER=niknotes_user
POSTGRES_PASSWORD=niknotes_pass
```

### Docker Compose Override

For development or custom configurations, create `docker-compose.override.yml`:

```yaml
version: "3.8"

services:
  web:
    volumes:
      # Live reload during development
      - .:/app
    environment:
      FLASK_DEBUG: 1
    ports:
      # Custom port mapping
      - "8080:5000"
```

---

## 📦 Docker Commands

### Starting Services

```bash
# Start all services in background
docker-compose up -d

# Start and view logs
docker-compose up

# Start specific service
docker-compose up -d web
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes data!)
docker-compose down -v

# Stop specific service
docker-compose stop web
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f postgres
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100 web
```

### Service Management

```bash
# Check service status
docker-compose ps

# Restart a service
docker-compose restart web

# Rebuild and restart
docker-compose up -d --build web

# Execute command in container
docker-compose exec web bash
docker-compose exec postgres psql -U niknotes_user -d niknotes_db
docker-compose exec redis redis-cli
```

### Database Operations

```bash
# Run migrations
docker-compose exec web python migrate.py create

# Reset database
docker-compose exec web python migrate.py drop
docker-compose exec web python migrate.py create

# Access PostgreSQL
docker-compose exec postgres psql -U niknotes_user -d niknotes_db

# Backup database
docker-compose exec postgres pg_dump -U niknotes_user niknotes_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U niknotes_user niknotes_db < backup.sql
```

### Cache Operations

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Clear cache
docker-compose exec redis redis-cli FLUSHDB

# Monitor Redis
docker-compose exec redis redis-cli MONITOR

# Check cache stats
docker-compose exec redis redis-cli INFO stats
```

---

## 🔍 Monitoring & Health Checks

### Health Check Status

```bash
# Check all containers health
docker-compose ps

# Detailed health status
docker inspect niknotes-web | jq '.[0].State.Health'
docker inspect niknotes-postgres | jq '.[0].State.Health'
docker inspect niknotes-redis | jq '.[0].State.Health'
```

### Resource Usage

```bash
# Container resource usage
docker stats

# Specific container
docker stats niknotes-web

# Once-off snapshot
docker stats --no-stream
```

### Application Logs

```bash
# Flask application logs
docker-compose logs -f web

# Database query logs (if enabled)
docker-compose logs -f postgres | grep "duration:"

# Redis operations
docker-compose logs -f redis
```

---

## 🚀 Production Deployment

### Security Hardening

1. **Change Default Passwords**

   ```yaml
   # docker-compose.yml
   environment:
     POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
   ```

   ```bash
   # .env
   POSTGRES_PASSWORD=strong_random_password_here
   ```

2. **Enable Redis Authentication**

   ```bash
   # docker/redis.conf
   requirepass your_redis_password_here
   ```

   ```bash
   # .env
   REDIS_URL=redis://:your_redis_password_here@redis:6379/0
   ```

3. **Use Secrets for Sensitive Data**

   ```yaml
   # docker-compose.yml
   services:
     postgres:
       secrets:
         - postgres_password

   secrets:
     postgres_password:
       file: ./secrets/postgres_password.txt
   ```

### Reverse Proxy (Nginx)

Add to `docker-compose.yml`:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    networks:
      - niknotes-network
```

Create `docker/nginx.conf`:

```nginx
upstream niknotes {
    server web:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://niknotes;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/TLS with Let's Encrypt

```bash
# Install certbot
docker run -it --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly \
  --standalone \
  -d your-domain.com

# Mount certificates
volumes:
  - /etc/letsencrypt:/etc/nginx/ssl:ro
```

### Scaling

```bash
# Scale web service to 3 instances
docker-compose up -d --scale web=3

# Requires load balancer (Nginx) configuration
```

---

## Troubleshooting

### shared_buffers Error

If you see an error like:

```text
parameter "shared_buffers" cannot be changed without restarting the server
```

**Solution:**

- PostgreSQL performance parameters are set in `docker-compose.yml` via command-line arguments
- The `docker/postgres-init.sql` file should NOT contain `ALTER SYSTEM SET` commands
- Rebuild the containers: `docker compose down && docker compose build --no-cache && docker compose up -d`
- Clear Python cache: Remove `__pycache__` directories and `.pyc` files

### Container Won't Start

```bash
# Check logs
docker-compose logs web

# Check if ports are in use
netstat -tulpn | grep 5000
netstat -tulpn | grep 5432

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Database Connection Issues

```bash
# Check if PostgreSQL is healthy
docker-compose ps postgres

# Test connection from web container
docker-compose exec web psql postgresql://niknotes_user:niknotes_pass@postgres:5432/niknotes_db -c "SELECT 1;"

# Check PostgreSQL logs
docker-compose logs postgres | tail -50
```

### Redis Not Connecting

```bash
# Check if Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# Check from web container
docker-compose exec web python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

### Application Errors

```bash
# View application logs
docker-compose logs -f web

# Access container shell
docker-compose exec web bash

# Check Python environment
docker-compose exec web python --version
docker-compose exec web pip list

# Test imports
docker-compose exec web python -c "from src.services.cache_service import get_cache_service; print('OK')"
```

### Out of Memory

```bash
# Check container memory usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings -> Resources -> Memory

# Limit container memory in docker-compose.yml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 512M
```

### Rebuilding After Code Changes

```bash
# Rebuild image
docker-compose build web

# Rebuild and restart
docker-compose up -d --build web

# Force rebuild (no cache)
docker-compose build --no-cache web
```

---

## 📊 Performance Optimization

### Database Tuning

The PostgreSQL container is pre-configured with optimal settings:

- `shared_buffers=256MB`
- `effective_cache_size=1GB`
- `max_parallel_workers=8`
- `random_page_cost=1.1` (SSD optimized)

### Redis Tuning

The Redis container uses:

- `maxmemory=256mb`
- `maxmemory-policy=allkeys-lru`
- Persistence disabled for speed

### Docker Build Optimization

Multi-stage build is used to:

- ✅ Reduce image size (~200MB vs ~1GB)
- ✅ Exclude build dependencies from final image
- ✅ Cache Python dependencies separately
- ✅ Faster rebuilds

---

## 🌐 Cloud Deployment

### AWS ECS

```bash
# Build and push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.region.amazonaws.com
docker build -t niknotes .
docker tag niknotes:latest <account>.dkr.ecr.region.amazonaws.com/niknotes:latest
docker push <account>.dkr.ecr.region.amazonaws.com/niknotes:latest
```

### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/niknotes
gcloud run deploy niknotes --image gcr.io/PROJECT-ID/niknotes --platform managed
```

### Azure Container Instances

```bash
# Create container instance
az container create \
  --resource-group niknotes-rg \
  --name niknotes \
  --image niknotes:latest \
  --ports 5000
```

### DigitalOcean App Platform

Use `docker-compose.yml` directly or convert to App Spec:

```yaml
name: niknotes
services:
  - name: web
    dockerfile_path: Dockerfile
    github:
      repo: your-username/niknotes
      branch: main
    http_port: 5000
databases:
  - name: postgres
    engine: PG
    version: "16"
```

---

## 📚 Best Practices

### Development Workflow

1. **Use docker-compose.override.yml** for local settings
2. **Mount source code** for live reload during development
3. **Use .env file** for environment-specific configuration
4. **Run tests** before building production images

### Production Checklist

- [ ] Change all default passwords
- [ ] Enable Redis authentication
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up automated backups
- [ ] Enable monitoring and logging
- [ ] Implement health checks
- [ ] Use Docker secrets for sensitive data
- [ ] Set resource limits
- [ ] Configure automatic restarts

### Backup Strategy

```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U niknotes_user niknotes_db | gzip > backup_$DATE.sql.gz

# Keep last 7 days
find . -name "backup_*.sql.gz" -mtime +7 -delete
```

---

## 🎯 Next Steps

1. **Start containers**: `docker-compose up -d`
2. **Check logs**: `docker-compose logs -f`
3. **Open browser**: <http://localhost:5000>
4. **Create a trip** and test the cache:
   - First AI request: ~2-5 seconds
   - Cached requests: **10-50ms** ⚡

## 📖 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Redis Docker Image](https://hub.docker.com/_/redis)
- [Flask Production Deployment](https://flask.palletsprojects.com/en/latest/deploying/)

---

**🐳 Happy Dockerizing!** Your NikNotes app is now production-ready in containers! 🚀
