# Rate Limiting Implementation Guide

**Implementation Date:** January 2025  
**Library:** Flask-Limiter 3.5.0  
**Status:** ✅ COMPLETE

## Overview

Rate limiting has been implemented to protect the NikNotes application from abuse, including:

- **Brute force attacks** on authentication endpoints
- **Spam account creation** via registration
- **API abuse** through excessive requests
- **Resource exhaustion** from expensive operations (PDF generation, AI calls)
- **Denial of Service (DoS)** attacks

## Architecture

### Storage Backend

Flask-Limiter uses a **dual-backend approach** with automatic fallback:

1. **Primary: Redis** (Distributed, Production)

   - Shared rate limits across multiple app instances
   - Persistent storage across restarts
   - Recommended for production deployments

2. **Fallback: In-Memory** (Development, Single Instance)
   - No external dependencies
   - Automatic fallback if Redis unavailable
   - Per-instance limits only
   - Resets on application restart

### Configuration

```python
# Try Redis first, fall back to in-memory
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
try:
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=redis_url,
        storage_options={"socket_connect_timeout": 30},
        strategy="fixed-window",
    )
except Exception as e:
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
        strategy="fixed-window",
    )
```

## Rate Limit Strategy

### Global Defaults

Applied to all routes unless overridden:

- **200 requests per day** per IP address
- **50 requests per hour** per IP address

### Endpoint-Specific Limits

#### Authentication Endpoints (STRICT)

**Registration:**

```python
@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
```

- **Limit:** 5 registrations per hour per IP
- **Reason:** Prevent spam account creation
- **Attack Vector:** Mass account registration for abuse

**Login:**

```python
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
```

- **Limit:** 10 login attempts per hour per IP
- **Reason:** Prevent brute force password attacks
- **Attack Vector:** Credential stuffing, password guessing

#### Resource-Intensive Endpoints (MODERATE)

**Trip Creation:**

```python
@app.route('/trip/new', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")
```

- **Limit:** 20 new trips per hour
- **Reason:** AI service calls are expensive
- **Resource Impact:** Each trip creation may call Gemini API

**PDF Export:**

```python
@app.route('/trip/<trip_id>/export-pdf')
@login_required
@limiter.limit("30 per hour")
```

- **Limit:** 30 PDF exports per hour
- **Reason:** CPU-intensive PDF generation
- **Resource Impact:** ReportLab processing, file I/O

**Save as Template:**

```python
@app.route('/trip/<trip_id>/save-as-template', methods=['POST'])
@login_required
@limiter.limit("20 per hour")
```

- **Limit:** 20 templates per hour
- **Reason:** Prevent database spam
- **Resource Impact:** Database write operations

**Delete Trip:**

```python
@app.route('/trip/<trip_id>/delete', methods=['POST'])
@login_required
@limiter.limit("20 per hour")
```

- **Limit:** 20 deletions per hour
- **Reason:** Prevent accidental mass deletion
- **Resource Impact:** Database cascading deletes

#### API Endpoints (GENEROUS)

**Add Item:**

```python
@app.route('/api/trip/<trip_id>/item', methods=['POST'])
@login_required
@limiter.limit("50 per hour")
```

- **Limit:** 50 items per hour
- **Reason:** Normal packing list building
- **Use Case:** Users adding items to trips

**Toggle Item:**

```python
@app.route('/api/item/<item_id>/toggle', methods=['POST'])
@login_required
@limiter.limit("100 per hour")
```

- **Limit:** 100 toggles per hour
- **Reason:** Frequent legitimate use (checking off items)
- **Use Case:** Users packing/unpacking items

**Delete Item:**

```python
@app.route('/api/item/<item_id>', methods=['DELETE'])
@login_required
@limiter.limit("100 per hour")
```

- **Limit:** 100 deletions per hour
- **Reason:** Normal list management
- **Use Case:** Users removing items from lists

#### View Endpoints (DEFAULT LIMITS)

Routes without explicit decorators use global defaults:

- `/` (index)
- `/trip/<trip_id>` (view trip)
- `/trip/from-template/<template_id>` (create from template)
- `/logout`

**Default Limits:** 200/day, 50/hour

## Rate Limit Headers

Flask-Limiter automatically adds HTTP headers to responses:

```http
X-RateLimit-Limit: 10           # Maximum requests in window
X-RateLimit-Remaining: 7         # Remaining requests
X-RateLimit-Reset: 1642540800    # Unix timestamp when limit resets
Retry-After: 3600                # Seconds to wait (on 429 error)
```

### Example Response (Rate Limit Exceeded)

```http
HTTP/1.1 429 Too Many Requests
Content-Type: text/html
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642540800
Retry-After: 3600

429 Too Many Requests
```

## Configuration Options

### Environment Variables

```bash
# .env file
REDIS_URL=redis://localhost:6379
# Or for Redis with password:
REDIS_URL=redis://:password@localhost:6379
# Or for Redis Cloud/External:
REDIS_URL=redis://username:password@redis-host:6379/0
```

### Strategy Types

Current: **fixed-window** (simple, fast)

**Alternatives:**

- `moving-window`: More accurate, slightly slower
- `fixed-window-elastic-expiry`: Hybrid approach

```python
strategy="fixed-window"  # Current
# strategy="moving-window"  # Alternative
```

### Custom Error Handling

```python
# Add to web_app.py for custom error page
@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template('errors/429.html',
                         reset_time=e.description), 429
```

## Testing Rate Limits

### Manual Testing

**Test Login Rate Limit (10/hour):**

```bash
# Make 11 requests quickly
for i in {1..11}; do
  curl -X POST http://localhost:5000/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test&password=test"
  echo "Request $i"
done

# 11th request should return 429
```

**Test API Rate Limit (50/hour):**

```bash
# Make 51 requests
for i in {1..51}; do
  curl -X POST http://localhost:5000/api/trip/123/item \
    -H "Content-Type: application/json" \
    -H "Cookie: session=YOUR_SESSION" \
    -d '{"name":"Test Item"}'
  echo "Request $i"
done
```

### Check Current Limits

```bash
# Check rate limit headers
curl -I http://localhost:5000/
# Look for X-RateLimit-* headers
```

### Reset Rate Limits

**Redis Backend:**

```bash
# Clear all rate limit data
redis-cli FLUSHDB

# Or clear specific key pattern
redis-cli --scan --pattern "LIMITER/*" | xargs redis-cli DEL
```

**In-Memory Backend:**

```bash
# Restart application
docker-compose restart web
```

## Monitoring Rate Limits

### Log Rate Limit Hits

```python
# Add to web_app.py
import logging

@app.after_request
def log_rate_limit(response):
    if response.status_code == 429:
        logging.warning(f"Rate limit exceeded: {request.remote_addr} "
                       f"on {request.path}")
    return response
```

### Check Redis Keys

```bash
# Connect to Redis
redis-cli

# List all rate limit keys
KEYS LIMITER/*

# Check specific limit
GET "LIMITER/127.0.0.1/login/10 per hour"

# Check TTL (time to live)
TTL "LIMITER/127.0.0.1/login/10 per hour"
```

### Prometheus Metrics (Optional)

```python
# Add prometheus_flask_exporter
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
# Automatically exposes /metrics endpoint
```

## Bypassing Rate Limits

### Whitelist IPs (Production)

```python
# Whitelist internal IPs or trusted services
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=redis_url,
    key_func=lambda: request.headers.get('X-Forwarded-For', request.remote_addr)
)

@limiter.request_filter
def whitelist():
    # Whitelist local IPs
    return request.remote_addr in ['127.0.0.1', '::1']
```

### Disable for Testing

```python
# .env file
RATELIMIT_ENABLED=False

# web_app.py
limiter = Limiter(
    get_remote_address,
    app=app,
    enabled=os.getenv('RATELIMIT_ENABLED', 'True').lower() == 'true'
)
```

### Exempt Specific Routes

```python
@app.route('/health')
@limiter.exempt
def health_check():
    return jsonify({'status': 'healthy'})
```

## Production Deployment

### Redis Configuration

**docker-compose.yml:**

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  web:
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

volumes:
  redis_data:
```

### Reverse Proxy (Nginx)

```nginx
# Get real client IP
location / {
    proxy_pass http://localhost:5000;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP $remote_addr;
}
```

**Update Flask-Limiter:**

```python
# Use X-Forwarded-For header
from flask_limiter.util import get_ipaddr

limiter = Limiter(
    get_ipaddr,  # Reads X-Forwarded-For
    app=app,
    # ... rest of config
)
```

### Health Checks

```python
# Exempt health check from rate limits
@app.route('/health')
@limiter.exempt
def health_check():
    return jsonify({
        'status': 'healthy',
        'rate_limiter': 'active'
    })
```

## Tuning Rate Limits

### Adjusting Limits

**Too Restrictive:** Users hitting limits during normal use

```python
# Increase limits
@limiter.limit("20 per hour")  # Was 10
```

**Too Lenient:** Observing abuse patterns

```python
# Decrease limits
@limiter.limit("5 per hour")  # Was 10
```

**Time Windows:**

```python
# Multiple windows (OR logic)
@limiter.limit("100 per day;20 per hour")

# Compound limits (AND logic)
@limiter.limit("100 per day")
@limiter.limit("20 per hour")
```

### Performance Considerations

**Redis Connection Pooling:**

```python
storage_options={
    "socket_connect_timeout": 30,
    "socket_timeout": 30,
    "max_connections": 50
}
```

**Async Redis (Future):**

```python
# Flask-Limiter supports async with Redis
# Requires async Flask application
```

## Security Considerations

### Rate Limit Bypass Techniques

**1. IP Rotation:**

- Attacker uses multiple IPs (VPN, proxies, botnets)
- **Mitigation:** Add user-based rate limiting for authenticated routes

**2. Cookie/Session Manipulation:**

- Attacker rotates sessions
- **Mitigation:** Combine IP + user-based limiting

**3. Distributed Attacks:**

- Slow, distributed requests under limits
- **Mitigation:** Monitor aggregate patterns, add application-level logic

### Enhanced Protection

**User-Based Rate Limiting:**

```python
def get_user_id():
    if current_user.is_authenticated:
        return f"user:{current_user.id}"
    return get_remote_address()

limiter = Limiter(
    get_user_id,
    app=app,
    # ... config
)
```

**Composite Keys:**

```python
def composite_key():
    # Rate limit by IP + User
    ip = get_remote_address()
    user = f":{current_user.id}" if current_user.is_authenticated else ""
    return f"{ip}{user}"
```

## Troubleshooting

### Issue: Rate limits not working

#### Check 1: Limiter initialized?

```python
# Verify in web_app.py
print(f"Limiter enabled: {limiter.enabled}")
```

#### Check 2: Redis connection

```bash
# Test Redis connectivity
redis-cli ping
# Expected: PONG
```

**Check 3: Headers present?**

```bash
curl -I http://localhost:5000/
# Look for X-RateLimit-* headers
```

### Issue: 429 errors for legitimate users

#### Solution 1: Increase limits

```python
@limiter.limit("20 per hour")  # Increase from 10
```

#### Solution 2: Add multiple windows

```python
@limiter.limit("100 per day;20 per hour")
```

#### Solution 3: Whitelist IPs

```python
@limiter.request_filter
def whitelist():
    return request.remote_addr in WHITELIST_IPS
```

### Issue: Rate limits reset on restart

**Cause:** Using in-memory storage

**Solution:** Configure Redis

```bash
# .env
REDIS_URL=redis://localhost:6379

# Start Redis
docker-compose up -d redis
```

### Issue: Different limits across servers

**Cause:** In-memory storage with multiple instances

**Solution:** Use Redis for distributed limits

```yaml
# docker-compose.yml
services:
  web:
    replicas: 3
    environment:
      - REDIS_URL=redis://redis:6379
  redis:
    image: redis:7-alpine
```

## Metrics & Analytics

### Track Rate Limit Usage

```python
from flask import g
import time

@app.before_request
def start_timer():
    g.start = time.time()

@app.after_request
def log_request(response):
    if hasattr(g, 'start'):
        elapsed = time.time() - g.start
        if response.status_code == 429:
            logging.info(f"RATE_LIMIT_HIT: {request.path} "
                        f"IP={request.remote_addr} "
                        f"User={current_user.id if current_user.is_authenticated else 'anon'}")
    return response
```

### Dashboard Query (Redis)

```python
import redis

def get_rate_limit_stats():
    r = redis.from_url(redis_url)
    keys = r.keys("LIMITER/*")

    stats = {}
    for key in keys:
        value = r.get(key)
        ttl = r.ttl(key)
        stats[key.decode()] = {
            'value': value.decode() if value else 0,
            'ttl': ttl
        }
    return stats
```

## Best Practices

### ✅ DO

1. **Use Redis in production** for distributed rate limiting
2. **Set strict limits on authentication** endpoints (registration, login)
3. **Add Retry-After headers** to help clients
4. **Monitor rate limit hits** for abuse patterns
5. **Whitelist health checks** and monitoring endpoints
6. **Use appropriate limits** for each endpoint type
7. **Test rate limits** before deployment

### ❌ DON'T

1. **Don't use in-memory storage** with multiple app instances
2. **Don't set limits too low** for legitimate use cases
3. **Don't forget to configure Redis** connection timeouts
4. **Don't rate limit health checks** (use @limiter.exempt)
5. **Don't ignore 429 errors** in logs (indicates attacks)
6. **Don't use only IP-based limiting** for authenticated routes
7. **Don't hardcode limits** - use configuration

## Summary

### What's Protected

✅ **Authentication:** Brute force protection (5-10 req/hour)  
✅ **Registration:** Spam prevention (5 req/hour)  
✅ **API Endpoints:** Abuse prevention (50-100 req/hour)  
✅ **Resource-Intensive:** DoS prevention (20-30 req/hour)  
✅ **Default Routes:** General protection (200/day, 50/hour)

### Storage Configuration

✅ **Redis:** Primary storage for production  
✅ **In-Memory:** Automatic fallback for development  
✅ **Graceful Degradation:** App works with or without Redis

### Implementation Summary

✅ **Fixed-Window:** Simple, fast, effective  
✅ **Per-IP:** Tracks by client IP address  
✅ **Configurable:** Easy to adjust limits  
✅ **Automatic Headers:** X-RateLimit-\* in responses

## Related Documentation

- [SECURITY_AUDIT.md](SECURITY_AUDIT.md) - Issue #7 (MEDIUM)
- [AUTHENTICATION.md](AUTHENTICATION.md) - Login/Register protection
- [PERFORMANCE_SETUP.md](PERFORMANCE_SETUP.md) - Redis configuration

---

**Status:** ✅ COMPLETE  
**Security Impact:** MEDIUM → LOW  
**Version:** NikNotes v1.2.0
