# Advanced Security Monitoring

## Overview

The application implements a comprehensive security monitoring system to protect against various types of attacks and abuse. This system includes brute-force detection, anomaly detection, per-user and per-IP rate limiting, and automated threat response.

## Architecture

### SecurityMonitor Class

The `SecurityMonitor` class (located in `src/utils/security_utils.py`) is the core component that tracks and analyzes security threats in real-time.

**Key Features:**

- **Failed Login Tracking**: Records failed authentication attempts per IP address
- **Successful Login Reset**: Clears failed attempt counters on successful authentication
- **Suspicious IP Flagging**: Automatically flags IPs after threshold violations
- **Request Pattern Analysis**: Detects anomalous request patterns per user/endpoint
- **Memory Management**: Background cleanup task prevents memory leaks

**Configuration:**

```python
max_failed_attempts = 5          # Max failed logins before IP suspension
failed_attempt_window = 300      # Time window in seconds (5 minutes)
anomaly_threshold = 50           # Max requests per minute to same endpoint
```

### Multi-Layer Protection

The security system operates at multiple layers:

1. **Infrastructure Layer**: Rate limiting via Flask-Limiter with Redis backend
2. **Application Layer**: SecurityMonitor tracks behavioral patterns
3. **Endpoint Layer**: Individual security checks at sensitive operations
4. **Monitoring Layer**: Audit logging and background cleanup

## Rate Limiting Strategy

### Tiered Rate Limits

Endpoints are organized into four sensitivity categories with appropriate limits:

#### CRITICAL Endpoints (Highest Protection)

- **delete_trip**: 5 requests/hour - Destructive data operation
- **delete_item**: 10 requests/hour - Item deletion
- **regenerate_suggestions**: 3 requests/hour - Expensive AI operation

#### SENSITIVE Endpoints

- **login**: 10 requests/hour - Prevents credential stuffing
- **register**: 5 requests/hour - Prevents account spam
- **logout**: 20 requests/hour - Normal usage pattern

#### MODERATE Endpoints

- **new_trip**: 20 requests/hour - Trip creation
- **add_item**: 50 requests/hour - Item addition
- **save_template**: 10 requests/hour - Template creation

#### STANDARD Endpoints

- **toggle_item**: 100 requests/hour - High-frequency interaction

### Per-User + Per-IP Tracking

Rate limits are tracked using a composite key: `user:<user_id>:<ip_address>` for authenticated users, `ip:<ip_address>` for anonymous users.

**Benefits:**

- Authenticated users get separate limits per device/location
- Anonymous users share IP-based limits
- Prevents abuse from both authenticated and unauthenticated sources

**Implementation:**

```python
def rate_limit_key_func():
    """Generate rate limit key combining user ID and IP"""
    from flask_login import current_user
    ip = get_ip_address()

    if current_user and current_user.is_authenticated:
        return f"user:{current_user.id}:{ip}"
    return f"ip:{ip}"
```

## Brute-Force Protection

### Login Protection

The authentication endpoint (`/login/google/callback`) implements multi-stage brute-force protection:

#### Stage 1: Pre-Authentication Check

```python
from src.utils.security_utils import is_ip_suspicious

if is_ip_suspicious(ip):
    return jsonify({'error': 'Too many failed login attempts'}), 429
```

#### Stage 2: Post-Authentication Tracking

```python
# On authentication failure
track_authentication_attempt(ip, success=False)

# On authentication success
track_authentication_attempt(ip, success=True)
```

**Behavior:**

- After 5 failed attempts within 5 minutes, IP is flagged as suspicious
- Suspicious IPs are blocked for the duration of the window
- Successful login clears failed attempt counter
- Security events logged to AuditLogger when available

### Protection Flow

```text
User Login Attempt
    ↓
Check if IP is flagged suspicious → YES → Return 429 (Too Many Attempts)
    ↓ NO
Proceed with OAuth validation
    ↓
Authentication Successful? → YES → Clear failed attempts, log success
    ↓ NO
Record failed attempt → Check threshold → Exceeded? → Flag IP as suspicious
```

## Anomaly Detection

### Request Pattern Analysis

The system tracks request patterns per user and endpoint to detect abnormal behavior:

**Tracked Metrics:**

- Request frequency per endpoint
- Request distribution across endpoints
- Time-based patterns

**Detection Logic:**

```python
def check_anomaly(user_identifier: str, endpoint: str) -> bool:
    """Check if request pattern indicates anomaly"""
    recent_requests = security_monitor.recent_requests.get(user_identifier, deque())

    # Count requests to same endpoint in last 60 seconds
    endpoint_count = sum(1 for r in recent_requests
                        if r['endpoint'] == endpoint
                        and time.time() - r['timestamp'] < 60)

    return endpoint_count > ANOMALY_THRESHOLD  # 50 requests/minute
```

### Threat Response

When anomalies are detected, the system returns a standardized threat response:

```python
def check_security_threats():
    """Pre-request security validation"""
    user_identifier = get_user_identifier()
    endpoint = request.endpoint or 'unknown'

    if security_monitor.check_anomaly(user_identifier, endpoint):
        return jsonify({
            'error': 'Anomalous request pattern detected',
            'status': 'blocked'
        }), 429

    return None  # No threat detected
```

## Endpoint Protection Pattern

### Securing Sensitive Endpoints

All CRITICAL and SENSITIVE endpoints should follow this pattern:

```python
@blueprint.route('/sensitive-operation', methods=['POST'])
@login_required
def sensitive_operation():
    """Example sensitive endpoint"""
    from src.utils.security_utils import check_security_threats, get_ip_address
    from flask_login import current_user

    # 1. Check for security threats
    threat_response = check_security_threats()
    if threat_response:
        return threat_response

    # 2. Log operation details
    ip = get_ip_address()
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'
    print(f"🔐 SENSITIVE_OP: operation_id=... by user={user_id} from {ip}")

    # 3. Continue with actual operation
    # ... your code here ...
```

### Protected Endpoints

Currently protected endpoints:

**API Blueprint (`src/blueprints/api.py`):**

- ✅ `delete_item()` - Item deletion with threat checking
- ✅ `regenerate_suggestions()` - Expensive AI regeneration

**Trips Blueprint (`src/blueprints/trips.py`):**

- ✅ `delete_trip()` - Trip deletion with threat checking

**Auth Blueprint (`src/blueprints/auth.py`):**

- ✅ `google_signin()` - Brute-force protection active

## Background Cleanup

### Memory Management

A background thread runs every 60 seconds to clean up stale security data:

```python
def _cleanup_old_data():
    """Remove data older than failed_attempt_window"""
    cutoff_time = time.time() - failed_attempt_window

    # Clean failed login attempts
    for ip, attempts in list(security_monitor.failed_login_attempts.items()):
        attempts = [t for t in attempts if t > cutoff_time]
        if attempts:
            security_monitor.failed_login_attempts[ip] = attempts
        else:
            del security_monitor.failed_login_attempts[ip]

    # Clean suspicious IPs
    for ip, flagged_time in list(security_monitor.suspicious_ips.items()):
        if flagged_time < cutoff_time:
            del security_monitor.suspicious_ips[ip]
```

**Cleanup Task Lifecycle:**

- Started automatically when rate limiter is initialized (see `src/extensions.py`)
- Runs as daemon thread (terminates when app closes)
- Prevents unbounded memory growth

## Integration with Audit Logging

Security events are logged to the AuditLogger when available:

```python
if audit_logger and audit_logger.enabled:
    audit_logger.log_security_event(
        event_type='failed_login',
        severity='medium',
        user_id=None,
        ip_address=ip,
        details={'attempts': attempt_count}
    )
```

**Logged Events:**

- Failed login attempts
- IP suspension events
- Successful logins after failures
- Anomalous request patterns

## Monitoring and Alerting

### Health Indicators

Monitor these metrics to detect security issues:

1. **Failed Login Rate**: High rate indicates credential stuffing attack
2. **Suspicious IP Count**: Sudden increase suggests coordinated attack
3. **429 Response Rate**: High rate indicates abuse or misconfigured client
4. **Anomaly Detection Triggers**: Repeated anomalies from same user/IP

### Recommended Alerting Thresholds

- **Critical**: >50 failed logins/minute
- **Warning**: >20 suspicious IPs
- **Info**: >100 anomaly detections/hour

## Testing Security Features

### Manual Testing

**Test Brute-Force Protection:**

```bash
# Attempt 6 failed logins from same IP
for i in {1..6}; do
    curl -X POST http://localhost:5000/login/google/callback \
         -d "invalid_token=test"
done

# Expected: 6th request returns 429 status
```

**Test Anomaly Detection:**

```bash
# Rapid requests to same endpoint (>50/minute)
for i in {1..51}; do
    curl -X POST http://localhost:5000/api/trip/test/regenerate
done

# Expected: Requests after 50 return 429 status
```

**Test Rate Limiting:**

```bash
# Exceed delete rate limit (5/hour)
for i in {1..6}; do
    curl -X POST http://localhost:5000/trip/test_$i/delete
done

# Expected: 6th request returns 429 with rate limit message
```

### Automated Testing

Create test cases in `tests/security/test_security_monitoring.py`:

```python
def test_brute_force_protection():
    """Test IP suspension after failed login attempts"""
    for _ in range(5):
        response = client.post('/login/google/callback',
                              data={'token': 'invalid'})

    # 6th attempt should be blocked
    response = client.post('/login/google/callback',
                          data={'token': 'invalid'})
    assert response.status_code == 429

def test_anomaly_detection():
    """Test anomaly detection for rapid requests"""
    trip_id = create_test_trip()

    # Make 51 rapid requests
    for _ in range(51):
        response = client.post(f'/api/trip/{trip_id}/regenerate')

    # Should be blocked after threshold
    assert response.status_code == 429
```

## Performance Considerations

### Redis Backend

The system uses Redis for rate limiting state when available:

**Benefits:**

- Distributed rate limiting across multiple app instances
- Persistent rate limit counters
- Low latency lookups (<1ms)

**Fallback:**

- Falls back to in-memory storage if Redis unavailable
- In-memory limits are per-process (not shared)

### Memory Usage

**SecurityMonitor Memory Footprint:**

- Failed login attempts: ~100 bytes per IP
- Suspicious IPs: ~50 bytes per IP
- Recent requests: ~200 bytes per user
- **Total**: <1MB for typical workload (<1000 active users)

**Cleanup Impact:**

- Runs every 60 seconds
- Processing time: <10ms for 1000 tracked IPs
- No impact on request handling

## Configuration

### Environment Variables

Security settings can be tuned via environment variables:

```bash
# Rate limiting backend
RATELIMIT_STORAGE_URL=redis://localhost:6379

# Security thresholds (optional)
MAX_FAILED_LOGIN_ATTEMPTS=5
FAILED_ATTEMPT_WINDOW=300
ANOMALY_THRESHOLD=50
```

### Code Configuration

Modify constants in `src/utils/security_utils.py`:

```python
# Brute-force protection
MAX_FAILED_ATTEMPTS = 5
FAILED_ATTEMPT_WINDOW = 300  # 5 minutes

# Anomaly detection
ANOMALY_THRESHOLD = 50  # requests per minute
```

## Best Practices

### For Developers

1. **Always call check_security_threats()** at the start of sensitive operations
2. **Log operations** with user ID and IP address for audit trail
3. **Return standardized error responses** (429 status with JSON)
4. **Test security features** with simulated attacks before deployment
5. **Monitor security metrics** in production

### For Operators

1. **Monitor 429 response rates** - High rates indicate misconfigured clients or attacks
2. **Review audit logs regularly** - Look for patterns in failed attempts
3. **Tune thresholds based on usage** - Adjust limits for your traffic patterns
4. **Enable Redis for production** - Ensures consistent rate limiting across instances
5. **Set up alerting** - Get notified of suspicious activity

## Troubleshooting

### Common Issues

**Issue**: Legitimate users getting 429 errors

- **Cause**: Rate limits too aggressive for usage pattern
- **Solution**: Increase limits for affected endpoints in `src/factory.py`

**Issue**: Brute-force protection not triggering

- **Cause**: Background cleanup running too frequently
- **Solution**: Increase cleanup interval or failed attempt window

**Issue**: Memory usage growing over time

- **Cause**: Cleanup task not running or data not expiring
- **Solution**: Check cleanup task is started, verify cutoff time logic

### Debug Logging

Enable detailed security logging:

```python
import logging
logging.getLogger('security_utils').setLevel(logging.DEBUG)
```

Logs will show:

- Failed attempt tracking
- IP suspension events
- Anomaly detection triggers
- Cleanup operations

## Security Considerations

### Attack Vectors Mitigated

✅ **Brute-Force Attacks**: IP-based blocking after threshold  
✅ **Credential Stuffing**: Per-account rate limiting  
✅ **API Abuse**: Anomaly detection for unusual patterns  
✅ **Resource Exhaustion**: Strict limits on expensive operations (AI, deletions)  
✅ **Distributed Attacks**: Per-user + per-IP tracking catches both

### Known Limitations

⚠️ **VPN/Proxy Evasion**: Attackers can rotate IPs to bypass IP-based limits  
⚠️ **False Positives**: Legitimate users on shared IPs may hit limits  
⚠️ **Memory-Based Fallback**: Without Redis, limits are per-process only

### Future Enhancements

- CAPTCHA integration after repeated failures
- Behavioral analysis (time-of-day patterns, typical endpoints)
- IP reputation scoring via external services
- Admin dashboard for security metrics
- Automated IP blocklist updates

## References

- [OWASP Rate Limiting](https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html#rate-limiting)
- [OWASP Brute Force](https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks)
- [Flask-Limiter Documentation](https://flask-limiter.readthedocs.io/)
- `SECURITY_AUDIT.md` - Complete security audit report

---

**Last Updated**: December 2024  
**Maintainer**: Security Team  
**Review Status**: ✅ Approved for Production
