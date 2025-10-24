# Security Quick Reference Card

---

## �️ Content Security Policy (CSP)

### Overview

**Strict CSP with nonce-based inline scripts and styles** - NO `unsafe-inline` directives.

### CSP Configuration

Located in `src/extensions.py`:

```python
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", 'https://accounts.google.com/gsi/client'],
    'style-src': ["'self'", 'https://accounts.google.com/gsi/style'],
    'img-src': ["'self'", 'data:', 'https:', 'https://lh3.googleusercontent.com'],
    'font-src': ["'self'"],
    'connect-src': ["'self'", 'https://accounts.google.com'],
    'frame-src': ['https://accounts.google.com'],
    'frame-ancestors': ["'none'"],
    'report-uri': ['/csp-report'],
}
```

**Key Features:**

- ✅ **No `unsafe-inline`** - All inline scripts/styles use nonces
- ✅ **Nonce-based execution** - Only scripts/styles with valid nonces execute
- ✅ **Frame protection** - `frame-ancestors: 'none'` prevents clickjacking
- ✅ **External integrations** - Google Sign-In whitelisted

### Using Nonces in Templates

**Always use `csp_nonce()` for inline scripts and styles:**

```html
<!-- Inline script with nonce -->
<script nonce="{{ csp_nonce() }}">
  document.addEventListener("DOMContentLoaded", function () {
    // Your code here
  });
</script>

<!-- Inline style with nonce -->
<style nonce="{{ csp_nonce() }}">
  .custom-class {
    color: blue;
  }
</style>
```

### ❌ NEVER Do This (CSP Violation)

```html
<!-- NO NONCE - Will be blocked! -->
<script>
  alert("This will not work");
</script>

<!-- Inline event handlers - Will be blocked! -->
<button onclick="doSomething()">Click</button>
```

### ✅ Do This Instead

```html
<!-- With nonce -->
<script nonce="{{ csp_nonce() }}">
  document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("myBtn");
    btn.addEventListener("click", function () {
      doSomething();
    });
  });
</script>

<button id="myBtn">Click</button>
```

### CSP Compliance Checklist

- [ ] All inline `<script>` tags have `nonce="{{ csp_nonce() }}"`
- [ ] All inline `<style>` tags have `nonce="{{ csp_nonce() }}"`
- [ ] No `onclick`, `onload`, `onerror` or other inline event handlers
- [ ] All event handlers use `addEventListener()` in nonce-protected scripts
- [ ] External scripts are loaded from whitelisted domains only

### Testing CSP

1. **Open browser console** when loading pages
2. **Check for CSP violations** - Look for errors like:

   ```text
   Refused to execute inline script because it violates CSP directive
   ```

3. **Fix violations** by adding nonces or moving code to external files

---

## �🚨 Before You Code

**Ask yourself:**

1. Does this endpoint modify data? (CREATE/UPDATE/DELETE)
2. Does this endpoint cost money? (AI calls, external APIs)
3. Does this endpoint expose sensitive data?

**If YES to any** → Follow the security pattern below

---

## 🔒 Security Pattern (Copy & Paste)

```python
@blueprint.route('/your-endpoint', methods=['POST'])
@login_required  # If authentication required
def your_sensitive_operation():
    """Your endpoint description (SECURITY: Explain why sensitive)"""
    from src.utils.security_utils import check_security_threats, get_ip_address
    from flask_login import current_user

    # 1. CHECK FOR THREATS (Required for all sensitive endpoints)
    threat_response = check_security_threats()
    if threat_response:
        return threat_response

    # 2. LOG THE OPERATION (Required for audit trail)
    ip = get_ip_address()
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'
    print(f"🔐 YOUR_OPERATION: details=... by user={user_id} from {ip}")

    # 3. YOUR ACTUAL CODE HERE
    # ... your implementation ...

    return jsonify({'success': True})
```

---

## 📊 Choose Your Rate Limit Tier

Add your endpoint to `src/factory.py` → `_apply_rate_limits()`:

### CRITICAL (Most Restrictive)

**Use for:** Data deletion, expensive AI operations, destructive actions

```python
critical_limits = {
    'your_blueprint.your_endpoint': '5 per hour',  # Very strict
}
```

### SENSITIVE

**Use for:** Authentication, registration, account operations

```python
sensitive_limits = {
    'your_blueprint.your_endpoint': '10 per hour',  # Strict
}
```

### MODERATE

**Use for:** Creating resources, uploading files, batch operations

```python
moderate_limits = {
    'your_blueprint.your_endpoint': '20 per hour',  # Normal
}
```

### STANDARD

**Use for:** High-frequency read operations, toggles, status checks

```python
standard_limits = {
    'your_blueprint.your_endpoint': '100 per hour',  # Permissive
}
```

---

## 🎯 Real Examples

### Example 1: Delete Operation

```python
@trips_bp.route('/<trip_id>/delete', methods=['POST'])
@login_required
def delete_trip(trip_id):
    """Delete a trip (destructive operation)"""
    from src.utils.security_utils import check_security_threats, get_ip_address

    threat_response = check_security_threats()
    if threat_response:
        return threat_response

    ip = get_ip_address()
    print(f"🗑️  DELETE TRIP: trip={trip_id} by user={current_user.id} from {ip}")

    # Continue with deletion...
```

**Rate limit:** CRITICAL → `'trips.delete_trip': '5 per hour'`

### Example 2: AI Operation

```python
@api_bp.route('/trip/<trip_id>/regenerate', methods=['POST'])
def regenerate_suggestions(trip_id):
    """Regenerate AI suggestions (expensive AI operation)"""
    from src.utils.security_utils import check_security_threats, get_ip_address

    threat_response = check_security_threats()
    if threat_response:
        return threat_response

    ip = get_ip_address()
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'
    print(f"🤖 REGENERATE AI: trip={trip_id} by user={user_id} from {ip}")

    # Generate suggestions...
```

**Rate limit:** CRITICAL → `'api.regenerate_suggestions': '3 per hour'`

### Example 3: High-Frequency Operation

```python
@api_bp.route('/item/<item_id>/toggle', methods=['POST'])
def toggle_item(item_id):
    """Toggle item packed status (frequent operation)"""
    # No security check needed - just rate limiting

    # Toggle logic...
    return jsonify({'success': True})
```

**Rate limit:** STANDARD → `'api.toggle_item': '100 per hour'`

---

## 🚫 Common Mistakes

### ❌ DON'T DO THIS

```python
@app.route('/delete', methods=['POST'])
def delete_something():
    # No security check!
    # No rate limiting!
    # No logging!
    delete_data()
    return 'OK'
```

### ✅ DO THIS INSTEAD

```python
@app.route('/delete', methods=['POST'])
@login_required
def delete_something():
    threat_response = check_security_threats()
    if threat_response:
        return threat_response

    ip = get_ip_address()
    print(f"🗑️  DELETE: user={current_user.id} from {ip}")

    delete_data()
    return jsonify({'success': True})
```

---

## 🧪 Testing Your Endpoint

### Manual Test: Rate Limiting

```bash
# Windows PowerShell
for ($i=1; $i -le 10; $i++) {
    curl http://localhost:5000/your-endpoint -Method POST
}
# Expected: 429 after limit
```

### Manual Test: Security Threats

```bash
# Rapid requests (>50/minute) should trigger anomaly detection
for ($i=1; $i -le 51; $i++) {
    curl http://localhost:5000/your-endpoint -Method POST
}
# Expected: 429 after 50 requests
```

---

## 📋 Security Checklist

Before merging your PR:

- [ ] Added `check_security_threats()` call for sensitive operations
- [ ] Added operation logging with user ID and IP
- [ ] Configured appropriate rate limit in `src/factory.py`
- [ ] Tested rate limit enforcement manually
- [ ] Added `@login_required` if authentication needed
- [ ] Documented why endpoint is sensitive (in docstring)
- [ ] Returned proper error responses (JSON with 429 status)

---

## 🆘 Need Help?

**Common Questions:**

**Q: What counts as "sensitive"?**  
A: DELETE operations, AI calls, authentication, registration, bulk operations

**Q: What rate limit should I use?**  
A: Start with MODERATE (20/hr), increase if needed based on usage

**Q: Do I always need security checks?**  
A: YES for CRITICAL/SENSITIVE endpoints, NO for read-only operations

**Q: What if legitimate users hit the limit?**  
A: Increase the limit, but log why and monitor usage

**Q: Can I skip logging?**  
A: NO - Logging is required for audit trail and incident response

---

## 📚 Full Documentation

**Comprehensive Guide:**  
`docs/security/advanced-security-monitoring.md`

**Security Audit Report:**  
`SECURITY_AUDIT.md`

**Implementation Summary:**  
`docs/security/SECURITY_ENHANCEMENT_SUMMARY.md`

---

## 🎨 Log Emoji Guide

Use these emojis for consistent logging:

- 🔐 General security operation
- 🗑️ Delete operation
- 🤖 AI operation
- ✅ Successful authentication
- ❌ Failed authentication
- ⚠️ Warning/anomaly detected
- 🚨 Security threat blocked

**Example:**

```python
print(f"🗑️  DELETE: item={item_id} by user={user_id} from {ip}")
print(f"🤖 AI_CALL: cost_estimate=${cost} trip={trip_id}")
print(f"✅ LOGIN: user={username} from {ip}")
```

---

**Last Updated:** December 2024  
**Questions?** Ask in #security Slack channel
