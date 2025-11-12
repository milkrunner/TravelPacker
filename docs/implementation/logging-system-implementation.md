# Logging System Migration Guide

## Overview

The NikNotes application has been upgraded from `print()` statements to a professional structured logging system using Python's built-in `logging` module.

## Features

### 🎯 **Key Improvements**

1. **Structured Logging**: Consistent format across all modules
2. **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
3. **File Rotation**: Automatic log file rotation (10 MB max, 5 backups)
4. **Security Audit Trail**: Separate security event log (no rotation for compliance)
5. **Error Tracking**: Dedicated error log file
6. **Colored Console Output**: Emoji prefixes and color-coded levels
7. **Performance Monitoring**: Context manager for operation timing

### 📂 **Log Files**

All logs are stored in the `logs/` directory:

- **`niknotes.log`**: Main application log (all levels)
- **`niknotes_security.log`**: Security events only (authentication, authorization, threats)
- **`niknotes_error.log`**: Errors and critical issues only

### 🎨 **Console Output**

Console logs include:

- **Emoji prefixes**: ✅ INFO, ⚠️ WARNING, ❌ ERROR, 🚨 CRITICAL, 🔐 SECURITY
- **Color coding**: Green (INFO), Yellow (WARNING), Red (ERROR), Magenta (CRITICAL)
- **Timestamps**: Human-readable format

## Usage

### Basic Logging

```python
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Log messages at different levels
logger.debug("Detailed debugging information")
logger.info("General informational message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical failure")
```

### Security Event Logging

```python
from src.utils.logging_config import get_logger, log_security_event
import logging

logger = get_logger(__name__)

# Log security-related events
log_security_event(
    logger,
    "User login attempt",
    level=logging.INFO,
    user_id="user_abc123",
    ip_address="192.168.1.100",
    action="login"
)
```

### Performance Monitoring

```python
from src.utils.logging_config import get_logger, PerformanceLogger

logger = get_logger(__name__)

# Monitor slow operations
with PerformanceLogger(logger, "Database query", threshold_ms=100):
    # Your code here
    result = perform_database_query()
```

## Configuration

### Environment Variables

- **`LOG_LEVEL`**: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Default: `INFO`
  - Development: `DEBUG`
  - Production: `WARNING` or `ERROR`

```bash
# In .env file
LOG_LEVEL=INFO
```

### Disable File Logging (Testing)

File logging is automatically disabled when `FLASK_ENV=testing` to avoid cluttering test environments.

## Migration Summary

### Files Modified

1. **`src/utils/logging_config.py`** (NEW)

   - Centralized logging configuration
   - Custom formatters with colors and emojis
   - Security filter for audit trail
   - Performance monitoring context manager

2. **`src/factory.py`**

   - Replaced `print()` with `logger.info()`
   - Added logging initialization

3. **`src/extensions.py`**

   - Replaced `print()` with `logger.info()`
   - Integrated structured logging

4. **`src/services/ai_service.py`**

   - Replaced `print()` with appropriate log levels
   - Cache hits: `logger.info()`
   - Errors: `logger.error()`

5. **`src/services/oauth_service.py`**

   - Replaced `print()` with `logger.info()`, `logger.warning()`, `logger.error()`
   - Removed `traceback.print_exc()` in favor of `exc_info=True`

6. **`src/utils/security_utils.py`**
   - Security alerts now use `log_security_event()`
   - Separate security audit trail

### Before vs. After

**Before (print statements):**

```python
print(f"✅ AI Service initialized (Cache: {'ON' if self.cache.enabled else 'OFF'})")
print(f"⚡ Cache HIT for trip {trip.id}")
print(f"❌ Error: {e}")
```

**After (structured logging):**

```python
logger.info(f"AI Service initialized (Cache: {'ON' if self.cache.enabled else 'OFF'})")
logger.info(f"Cache HIT for trip {trip.id}")
logger.error(f"Error: {e}", exc_info=True)
```

## Best Practices

### 1. **Use Appropriate Log Levels**

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General informational messages (startup, shutdown, state changes)
- **WARNING**: Unexpected situations that don't stop execution
- **ERROR**: Errors that prevented an operation from completing
- **CRITICAL**: System failures requiring immediate attention

### 2. **Include Context**

```python
# Good
logger.info(f"User {user_id} logged in from {ip_address}")

# Better
logger.info("User login successful", extra={
    'user_id': user_id,
    'ip_address': ip_address,
    'session_id': session_id
})
```

### 3. **Use `exc_info=True` for Exceptions**

```python
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    # Automatically includes full traceback
```

### 4. **Avoid Logging Sensitive Data**

```python
# BAD - logs password
logger.debug(f"Login attempt with password: {password}")

# GOOD - sanitized
logger.debug(f"Login attempt for user: {username}")
```

### 5. **Use Security Logging for Audit Trail**

```python
# For authentication, authorization, data access
log_security_event(
    logger,
    "Sensitive data accessed",
    level=logging.WARNING,
    user_id=user.id,
    resource="trip_data",
    action="read"
)
```

## Testing

Logs are automatically disabled for file output during tests (`FLASK_ENV=testing`). Console output remains active for debugging.

## Production Deployment

### Docker

Logs are automatically persisted to the `logs/` volume in Docker:

```yaml
volumes:
  - app_logs:/app/logs
```

### Log Rotation

- **Automatic**: Files rotate at 10 MB
- **Backup Count**: 5 previous logs kept
- **Security Log**: No rotation (for compliance/audit trail)

### Monitoring

Monitor error logs for production issues:

```bash
# View last 100 lines of error log
tail -n 100 logs/niknotes_error.log

# Follow error log in real-time
tail -f logs/niknotes_error.log

# Search for specific errors
grep "CRITICAL" logs/niknotes_error.log
```

## Troubleshooting

### Issue: No log files created

**Solution**: Check that the `logs/` directory exists and is writable:

```bash
mkdir -p logs
chmod 755 logs
```

### Issue: Logs too verbose in production

**Solution**: Set `LOG_LEVEL=WARNING` in production `.env`:

```bash
LOG_LEVEL=WARNING
```

### Issue: Security log not working

**Solution**: Ensure you're using `log_security_event()` for security events:

```python
from src.utils.logging_config import log_security_event
log_security_event(logger, "Security event", level=logging.WARNING)
```

## Future Enhancements

Potential improvements for the logging system:

1. **External Log Aggregation**: Send logs to ELK Stack, Splunk, or CloudWatch
2. **JSON Logging**: Machine-readable JSON format for log parsing
3. **Async Logging**: Non-blocking log writes for high-performance scenarios
4. **User Activity Logging**: Track all user actions for compliance
5. **Alert Integration**: Send critical errors to Slack/PagerDuty

## References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Logging Best Practices](https://docs.python-guide.org/writing/logging/)
- [Security Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

---

**Status**: ✅ Implemented (November 2025)
