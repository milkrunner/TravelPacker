# NikNotes AI Coding Agent Instructions

## Project Overview
**NikNotes** is an AI-powered travel packing assistant built with Flask, PostgreSQL, Redis, and Google Gemini. The app helps users create intelligent packing lists based on trip details, with weather integration and AI suggestions cached for blazing-fast responses (10-50ms).

**Key architectural principle**: Performance-first design with PostgreSQL required, fallback strategies for Redis → no cache, Gemini → mock data.

## Architecture Quick Reference

### Service Layer Pattern
All business logic lives in `src/services/`. Services are stateless and injected where needed:

- **AIService** - Gemini AI integration with Redis caching (24h TTL)
- **CacheService** - Redis wrapper with connection pooling, graceful failure
- **TripService** - Trip CRUD via Repository pattern (supports database on/off)
- **PackingListService** - Item management + AI suggestion coordination
- **WeatherService** - OpenWeatherMap integration (optional)
- **PDFService** - ReportLab-based PDF generation
- **SanitizationService** - Bleach-based XSS protection
- **AuditLogger** - Security event logging (not for debugging)

**Pattern**: Services inject dependencies via constructor. Check `use_database` flags to support both DB and in-memory modes.

### Repository Pattern
Database access isolated in `src/database/repository.py`:
- **TripRepository** - Trip/Traveler persistence with eager loading (`lazy='selectin'`)
- **PackingItemRepository** - Item persistence with category filtering
- **UserRepository** - Authentication (currently disabled, see SECURITY_AUDIT.md)

**Connection management**: Call `get_session()` → operations → `close_session()` in finally block.

### Data Models (Dual System)
1. **Domain Models** (`src/models/`) - Pydantic models for business logic
   - `Trip`, `Traveler`, `PackingItem` - validation, serialization, business rules
2. **Database Models** (`src/database/models.py`) - SQLAlchemy ORM
   - Indexed columns: `destination`, `start_date`, `created_at`, `user_id`, `is_template`
   - Composite index: `idx_trip_destination_date`

**Why two?** Separation of concerns - domain logic vs. persistence. Repositories handle translation.

## Critical Development Workflows

### Running Tests
```powershell
# Full test suite with coverage
pytest

# Coverage report at: reports/coverage/htmlcov/index.html
# Security tests at: tests/security/
# Integration tests at: tests/integration/
```

**Test database**: Auto-created/dropped per test via `setup_database` fixture in `conftest.py`.

### Security Scanning
```powershell
# CodeQL security analysis runs automatically:
# - Weekly: Every Monday at 6:00 AM UTC
# - On push to: main, security, develop branches
# - On pull requests to main
# - On demand: GitHub Actions → CodeQL Security Analysis → Run workflow

# Secret scanning runs automatically:
# - Daily: Every day at 2:00 AM UTC
# - On push to: main, security, develop branches
# - On pull requests to main
# - On demand: GitHub Actions → Secret Scanning → Run workflow

# Dependabot dependency updates:
# - Weekly: Every Monday at 6:00 AM UTC
# - Auto-creates PRs for: Python (pip), Docker, GitHub Actions
# - Groups non-security updates, prioritizes security patches
# - Max 5 Python PRs, 3 Docker PRs, 3 GitHub Actions PRs

# Dependency review on PRs:
# - Runs on all pull requests to: main, security, develop
# - Scans for: CVEs, license issues, malicious packages
# - Fails on: High/critical vulnerabilities, copyleft licenses
# - Comments: Automated security summary on PR

# View results: GitHub → Security → Code scanning alerts / Dependabot alerts
```

**CodeQL Config**: `.github/workflows/codeql-analysis.yml` scans Python & JavaScript with `security-extended` queries.
**Secret Scanning**: `.github/workflows/secret-scanning.yml` uses TruffleHog + Gitleaks for exposed credentials detection.
**Dependabot**: `.github/dependabot.yml` monitors pip, Docker, and GitHub Actions for vulnerabilities and updates.
**Dependency Review**: `.github/workflows/dependency-review.yml` analyzes all dependency changes in PRs with pip-audit + GitHub's dependency graph.

### Docker Development
```powershell
# Start full stack (PostgreSQL + Redis + Web)
docker compose up -d

# View logs
docker compose logs -f web

# Rebuild after code changes
docker compose up -d --build

# Health check: http://localhost:5000/health
```

**Database migrations**: Auto-run on container start via `scripts/migrate.py`. Manual: `python scripts/migrate.py create`.

### Environment Variables
Required in `.env` or environment:
```bash
FLASK_SECRET_KEY=<32-char-hex>  # Generate: python -c "import secrets; print(secrets.token_hex(32))"
POSTGRES_PASSWORD=<secure-password>
GEMINI_API_KEY=<your-key>  # Optional - falls back to mock
WEATHER_API_KEY=<your-key>  # Optional - weather disabled without it
```

**Invalid keys**: App crashes on startup if `FLASK_SECRET_KEY` is default/empty (see `invalid_keys` in `web_app.py`).

**Secret Protection**: Automated secret scanning (TruffleHog + Gitleaks) runs daily and on every push/PR to prevent credential leaks.

**Dependency Security**: Dependabot automatically creates PRs for vulnerable dependencies (Python, Docker, GitHub Actions) every Monday.

**PR Dependency Review**: Every PR automatically scanned for vulnerable/malicious dependencies, license violations, and OpenSSF Scorecard ratings.

## Security Architecture (Production-Ready)

### Defense Layers
1. **CSRF Protection** (Flask-WTF) - All POST/DELETE routes, AJAX via `X-CSRFToken` header
2. **Content Security Policy** (Flask-Talisman) - Nonce-based inline scripts, `frame-ancestors: none`
3. **Rate Limiting** (Flask-Limiter) - Redis-backed (falls back to memory), per-endpoint limits
4. **Input Sanitization** (Bleach) - Strict for names/titles, rich for notes (limited tags)
5. **Input Validation** (Pydantic) - `src/validators.py` schemas for all user input

**Key file**: `SECURITY_AUDIT.md` tracks all 11 vulnerabilities fixed (100% resolved).

### Rate Limits (See `web_app.py`)
- `/trip/new`: 20/hour
- `/trip/<id>/delete`: 20/hour  
- `/api/item/<id>/toggle`: 100/hour
- `/api/trip/<id>/item`: 50/hour
- Default: 200/day, 50/hour

### Content Sanitization Pattern
```python
from src.services.sanitization_service import ContentSanitizer

# User-visible text (strict - no HTML)
clean_name = ContentSanitizer.sanitize_strict(user_input)

# Rich text/notes (limited HTML)
clean_notes = ContentSanitizer.sanitize_rich(user_notes)
```

**Never** render user content with `innerHTML` - use `textContent` or sanitize first.

## Performance Considerations

### Redis Caching Strategy
AI suggestions cached by MD5 hash of trip parameters (destination, duration, style, weather, etc.):
```python
# Cache key generation in AIService._trip_to_cache_data()
cache_key = f"ai_suggestions:{md5(sorted_json)}"
```

**Cache hit = 10-50ms**, miss = 2-5 seconds. Cache automatically disabled if Redis unavailable.

### Database Optimizations (PostgreSQL)
Tuned in `docker-compose.yml`:
- Connection pooling: 20 base + 40 overflow (SQLAlchemy)
- `shared_buffers=256MB`, `effective_cache_size=1GB`
- `max_parallel_workers_per_gather=4` for complex queries
- Indexes on: destination, start_date, created_at, user_id, is_template

**Query pattern**: Use `lazy='selectin'` for relationships (avoids N+1), eager load in repositories.

### Fallback Strategies
- **Database**: PostgreSQL (required - no fallback)
- **Cache**: Redis → disabled (direct API calls)
- **AI**: Gemini → mock suggestions (`_get_mock_suggestions()`)
- **Weather**: API → `None` (no weather in suggestions)

**Check availability**: Services have `.enabled` flag (e.g., `cache.enabled`, `weather.enabled`).

## Frontend Integration

### CSRF Tokens
All AJAX requests need CSRF token:
```javascript
fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken  // From meta tag
    },
    body: JSON.stringify(data)
})
```

**Get token**: `<meta name="csrf-token" content="{{ csrf_token() }}">` in base template.

### Dark Mode Toggle
Pure CSS implementation, preference stored in localStorage:
```javascript
// static/js/main.js
localStorage.setItem('theme', 'dark');
document.body.classList.add('dark-mode');
```

**No backend involvement** - client-side only.

## Project-Specific Conventions

### ID Generation
```python
import uuid
trip_id = f"trip_{uuid.uuid4().hex[:8]}"  # Short readable IDs
```

**Format**: `<entity>_<8-hex-chars>` (e.g., `trip_a1b2c3d4`, `item_9f8e7d6c`)

### Enum Usage
Enums defined in domain models, stored as strings in DB:
```python
from src.models.trip import TravelStyle, TransportMethod
# Values: TravelStyle.LEISURE, TransportMethod.FLIGHT
```

**SQLAlchemy mapping**: `SQLEnum(TravelStyle)` in `models.py`

### Error Handling Pattern
```python
try:
    result = operation()
    return jsonify({"status": "success", "data": result})
except ValidationError as e:
    return jsonify({"status": "error", "message": str(e)}), 400
except Exception as e:
    print(f"Error: {e}")  # Console logging
    return jsonify({"status": "error", "message": "Internal error"}), 500
```

**Never expose raw exceptions** to frontend - sanitize error messages.

### Database Session Management
```python
from src.database import get_session, close_session

session = get_session()
try:
    # Operations
    session.commit()
finally:
    close_session()
```

**Always** use try-finally to ensure session cleanup.

### Database Migrations (Alembic)

**All schema changes** must go through Alembic migrations:

```bash
# Create migration after modifying models
python scripts/db_migrate.py create "Add email_verified column"

# Apply migrations
python scripts/db_migrate.py upgrade

# Check current version
python scripts/db_migrate.py current
```

**Never** use `Base.metadata.create_all()` except in tests. Migrations run automatically on app startup via `init_db()`.

See `docs/operations/database-migrations.md` for complete migration guide.

## Documentation Structure
See `docs/INDEX.md` for full reference:
- **getting-started/**: Quick setup guides
- **features/**: User-facing features (AI, weather, PDF, templates, dark mode)
- **architecture/**: System design (database, performance, web interface)
- **security/**: Security implementations (CSRF, CSP, rate limiting, sanitization)
- **operations/**: Docker deployment, health checks

**Update docs when**: Adding features, changing security, modifying API, tuning performance.

## Common Pitfalls to Avoid

1. **Don't bypass validation** - Always use Pydantic schemas from `src/validators.py`
2. **Don't commit secrets** - Use environment variables, check `.gitignore`
3. **Don't skip CSRF tokens** - Required on all POST/DELETE routes
4. **Don't use raw SQL** - Use SQLAlchemy ORM (Repository pattern)
5. **Don't assume services are available** - Check `.enabled` flags before using
6. **Don't ignore rate limits** - Test endpoint limits before deployment
7. **Don't trust user input** - Sanitize and validate everything

## Testing Philosophy
- **Unit tests** (`tests/unit/`) - Service logic, no database required
- **Integration tests** (`tests/integration/`) - Full stack, database interactions
- **Security tests** (`tests/security/`) - Verify CSRF, sanitization, validation

**Coverage target**: Core services >80%, full app ~70% (see `reports/coverage/`).

## Quick Commands Reference
```powershell
# Development
pytest                              # Run tests
docker compose up -d                # Start services
docker compose logs -f web          # View logs
python scripts/migrate.py create    # Database migration

# Security
# GitHub Actions → CodeQL Security Analysis → Run workflow  # Manual security scan
pip-audit                           # Check dependencies for vulnerabilities

# Production
docker compose up -d --build        # Deploy with rebuild
python -c "import secrets; print(secrets.token_hex(32))"  # Generate secret
```

## Google OAuth Authentication

The app uses **Google OAuth 2.0** for user authentication (no passwords stored):

### Setup Required
```bash
# Get credentials at: https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### OAuth Flow
1. User clicks "Continue with Google" on `/login`
2. Redirects to Google OAuth consent screen
3. Google redirects back to `/login/google/callback`
4. `OAuthService` validates token and fetches user info
5. User created/linked via `find_or_create_user()`
6. Flask-Login session established

### Key Components
- **OAuthService** (`src/services/oauth_service.py`) - Authlib integration
- **User Model** - OAuth fields: `oauth_provider`, `oauth_id`, `profile_picture`
- **Password Optional** - `password_hash` nullable for OAuth-only users
- **Account Linking** - Email match links OAuth to existing accounts

### Route Protection
```python
@app.route('/trip/new')
@login_required  # Flask-Login decorator
def new_trip():
    # current_user.id available here
    trip_service.create_trip(..., user_id=current_user.id)
```

### Migration
Run `python scripts/migrations/add_oauth_support.py` to add OAuth columns to existing database.

---

**Project Status**: Production-ready with 11/11 security issues resolved. Google OAuth authentication enabled.
