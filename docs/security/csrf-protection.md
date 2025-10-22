# CSRF Protection - NikNotes

## Overview

NikNotes implements **Cross-Site Request Forgery (CSRF)** protection using Flask-WTF to prevent malicious websites from performing unauthorized actions on behalf of authenticated users.

## What is CSRF?

CSRF is an attack that tricks a user's browser into making unwanted requests to a web application where they're authenticated. For example:

```html
<!-- Attacker's malicious website -->
<img src="https://niknotes.com/trip/user_trip_id/delete" style="display:none" />
```

Without CSRF protection, if the user is logged into NikNotes, this image tag would delete their trip without their knowledge.

## Implementation

### Backend Protection (Flask-WTF)

**Installed:** `flask-wtf==1.2.1`

```python
# web_app.py
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
```

This automatically:

- Validates CSRF tokens on all POST, PUT, PATCH, DELETE requests
- Returns 400 Bad Request if token is missing or invalid
- Exempts GET, HEAD, OPTIONS requests

### Frontend Implementation

#### 1. Form-Based Submissions

All HTML forms include a hidden CSRF token:

```html
<form method="POST" action="/trip/new">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
  <!-- form fields -->
</form>
```

**Example:** `templates/new_trip.html`, `templates/view_trip.html`

#### 2. AJAX/Fetch Requests

JavaScript makes the CSRF token available globally:

```html
<!-- base.html -->
<script>
  window.csrfToken = "{{ csrf_token() }}";
</script>
```

All fetch requests include the token in headers:

```javascript
fetch("/api/trip/123/item", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": window.csrfToken,
  },
  body: JSON.stringify(data),
});
```

**Protected Endpoints:**

- `/api/item/<item_id>/toggle` (POST)
- `/api/trip/<trip_id>/item` (POST)
- `/api/item/<item_id>` (DELETE)
- `/api/trip/<trip_id>/reorder-items` (POST)
- `/api/trip/<trip_id>/regenerate` (POST)
- `/trip/<trip_id>/delete` (POST)
- `/trip/<trip_id>/save-as-template` (POST)

## Testing with CSRF Protection

### Disabling CSRF in Tests

The test suite disables CSRF validation for easier testing:

```python
# tests/conftest.py
os.environ.setdefault("WTF_CSRF_ENABLED", "False")
```

### Testing CSRF Protection

To test that CSRF protection is working:

```bash
# This should fail with 400 Bad Request
curl -X POST http://localhost:5000/trip/test_id/delete

# This should succeed with valid CSRF token
curl -X POST http://localhost:5000/trip/test_id/delete \
  -H "X-CSRFToken: <valid_token>" \
  -H "Content-Type: application/json"
```

## Configuration

### Environment Variables

```bash
# .env
FLASK_SECRET_KEY=your-secret-key-here  # Required for CSRF tokens
WTF_CSRF_ENABLED=True                  # Default: True (enabled)
WTF_CSRF_TIME_LIMIT=3600               # Token expiry in seconds (optional)
```

### Flask Configuration

```python
# web_app.py
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')  # Required
app.config['WTF_CSRF_ENABLED'] = True  # Default
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour token expiry
```

## Token Lifecycle

1. **Generation:** Server generates unique CSRF token per session
2. **Storage:** Token stored in user's session (encrypted with SECRET_KEY)
3. **Transmission:** Sent to client in form or made available to JavaScript
4. **Validation:** Server validates token on state-changing requests
5. **Expiry:** Tokens expire after configurable time limit (default: 3600s)

## Error Handling

### 400 Bad Request - CSRF Token Missing

**Cause:** Request didn't include CSRF token

**Solution:** Ensure all forms include `{{ csrf_token() }}` and all fetch requests include `X-CSRFToken` header

### 400 Bad Request - CSRF Token Invalid

**Cause:** Token expired, mismatched, or tampered with

**Solutions:**

- Refresh the page to get a new token
- Check that SECRET_KEY hasn't changed
- Verify session cookies are working

### Debugging CSRF Issues

```python
# Temporarily log CSRF errors for debugging
from flask_wtf.csrf import CSRFError

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    print(f"CSRF Error: {e.description}")
    return jsonify({'error': 'CSRF validation failed'}), 400
```

## Security Best Practices

### ✅ DO

- Always include CSRF tokens in forms
- Use HTTPS in production (prevents token interception)
- Keep SECRET_KEY secure and rotate regularly
- Set appropriate token expiry times
- Validate tokens on ALL state-changing operations

### ❌ DON'T

- Disable CSRF protection in production
- Send CSRF tokens in URL parameters (use headers/body)
- Share SECRET_KEY between environments
- Store CSRF tokens in localStorage (session storage only)
- Expose CSRF tokens in logs or error messages

## Browser Compatibility

CSRF protection works on all modern browsers:

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

**Required:** JavaScript enabled (for AJAX requests)

## Common Issues & Solutions

### Issue: Forms Submitting Without Token

**Symptom:** 400 error on form submission

**Fix:** Add hidden input to form:

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
```

### Issue: AJAX Requests Failing

**Symptom:** 400 error on fetch/AJAX requests

**Fix:** Add header to request:

```javascript
headers: {
    'X-CSRFToken': window.csrfToken
}
```

### Issue: Token Expiring Too Quickly

**Symptom:** Users get CSRF errors after inactivity

**Fix:** Increase token lifetime:

```python
app.config['WTF_CSRF_TIME_LIMIT'] = 7200  # 2 hours
```

### Issue: CSRF Protection Breaking API

**Symptom:** External API clients can't make requests

**Fix:** Exempt specific routes (use with caution):

```python
from flask_wtf.csrf import csrf_exempt

@app.route('/api/public/endpoint', methods=['POST'])
@csrf_exempt
def public_endpoint():
    # ...
```

## Monitoring & Logging

Monitor CSRF protection effectiveness:

```python
import logging

@app.errorhandler(CSRFError)
def log_csrf_error(e):
    logging.warning(f'CSRF validation failed: {request.remote_addr} - {request.path}')
    return jsonify({'error': 'CSRF validation failed'}), 400
```

Track metrics:

- Number of CSRF errors per day
- Most common failing endpoints
- Geographic distribution of errors
- Pattern of legitimate vs. attack attempts

## References

- [Flask-WTF Documentation](https://flask-wtf.readthedocs.io/en/stable/csrf.html)
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)

## Version History

- **v1.0.0** (Oct 2025): Initial CSRF protection implementation
  - Installed Flask-WTF 1.2.1
  - Protected all state-changing endpoints
  - Added tokens to all forms and AJAX requests
  - Documented configuration and testing

---

**Status:** ✅ Fully Implemented  
**Last Updated:** October 20, 2025
