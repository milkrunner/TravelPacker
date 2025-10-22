# Development Setup Guide

## Quick Start (No External Dependencies)

NikNotes is designed to run without external services for development. The application automatically falls back to simpler alternatives:

### Prerequisites

- Python 3.9+
- pip (Python package manager)

### Installation

1. Clone the repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

```bash
python web_app.py
```

The application will start on `http://127.0.0.1:5000`

## Configuration

The `.env` file contains all configuration settings:

### Essential Settings

```env
# Flask Secret Key (REQUIRED)
FLASK_SECRET_KEY=your_secret_key_here

# Use Redis (Optional)
USE_REDIS=False
```

### Development Mode (Default)

When external services are unavailable, the application automatically uses:

- **Database**: SQLite (automatic fallback from PostgreSQL)
- **Cache**: In-memory (no Redis required)
- **Rate Limiting**: In-memory (no Redis required)

### Production Mode (Optional)

For production deployments with external services:

```env
# Enable Redis for distributed rate limiting and caching
USE_REDIS=True
REDIS_URL=redis://localhost:6379/0

# Use PostgreSQL for better performance
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

## Application Startup

### Successful Startup Messages

You should see:

```text
✅ SQLite database ready: niknotes.db
✅ Rate limiter initialized with in-memory backend (development mode)
✅ Security headers enabled (HTTPS redirect: False)
⚠️  Redis unavailable, caching disabled: ConnectionError
✅ AI Service initialized (Cache: OFF)
 * Running on http://127.0.0.1:5000
```

### What the Messages Mean

- **SQLite database ready**: Using local database file (no PostgreSQL needed)
- **In-memory backend**: Rate limiting works without Redis
- **Redis unavailable**: Caching disabled, AI responses will be slower but still work
- **Cache: OFF**: Application works normally without cache

## Common Issues

### Issue: "FLASK_SECRET_KEY must be set to a secure value"

**Solution**: Update `.env` file:

```env
FLASK_SECRET_KEY=dev_secret_key_7f8e9d6c5b4a3e2d1c0b9a8f7e6d5c4b3a2e1d0c9b8a7f6e5d4c3b2a1
```

For production, generate a secure random key:

```python
import secrets
print(secrets.token_hex(32))
```

### Issue: "Error 10061 connecting to Redis"

**Solution**: Disable Redis in `.env`:

```env
USE_REDIS=False
```

The application will use in-memory alternatives.

### Issue: "PostgreSQL connection refused"

**Solution**: The application automatically falls back to SQLite. No action needed.

To use PostgreSQL, install and start it, then verify connection settings in `.env`.

## Features Available Without External Services

### ✅ Works Without Redis/PostgreSQL

- User authentication and registration
- Trip creation and management
- Packing list management
- Template system
- PDF export
- All security features (CSRF, rate limiting, content sanitization)
- Audit logging

### ⚡ Faster With Redis/PostgreSQL

- AI suggestions (cached responses)
- Database queries (PostgreSQL is faster than SQLite)
- Rate limiting (distributed across multiple instances)

## Optional Services

### Redis (Optional)

**Purpose**: Caching and distributed rate limiting

**Installation**:

- Windows: Download from <https://github.com/microsoftarchive/redis/releases>
- Linux/Mac: `brew install redis` or `apt-get install redis`

**Enable**: Set `USE_REDIS=True` in `.env`

### PostgreSQL (Optional)

**Purpose**: Better database performance

**Installation**:

- Windows: Download from <https://www.postgresql.org/download/>
- Linux: `apt-get install postgresql`
- Mac: `brew install postgresql`

**Configure**: Update `DATABASE_URL` in `.env`

## Docker Deployment

For production with all services:

```bash
docker-compose up -d
```

See [Docker Deployment](docker-deployment.md) for details.

## Development Workflow

1. Start the application: `python web_app.py`
2. Access the web interface: `http://127.0.0.1:5000`
3. Make changes to code
4. Restart the application to see changes

For hot reloading, set `DEBUG=True` in `.env` (already default).

## Security Notes

### Development

- HTTPS redirect is disabled by default
- Secret key can be simple (not for production)
- Rate limits are permissive

### Production

- Enable `FORCE_HTTPS=True`
- Use strong random secret key
- Configure stricter rate limits
- Use PostgreSQL and Redis for better performance
- Review [Security Overview](../security/overview.md)

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ -v --cov=src --cov-report=html:reports/coverage/htmlcov
```

## Next Steps

- [Quick Start Guide](../getting-started/quick-start.md)
- [Authentication Setup](../getting-started/authentication.md)
- [Docker Deployment](docker-deployment.md)
- [Security Overview](../security/overview.md)
