# Authentication & Authorization System

## Overview

NikNotes now includes a complete authentication and authorization system to ensure users can only access their own trips and data. This implements **CRITICAL security feature #2** from the security audit.

## Features

### Authentication

- **User Registration**: New users can create accounts with username, email, and password
- **Secure Login**: Session-based authentication with remember-me functionality
- **Password Security**:
  - Passwords hashed using Werkzeug's `generate_password_hash()` with PBKDF2-SHA256
  - Minimum 8 characters required
  - Never stored in plaintext
- **Session Management**: Flask-Login handles secure session cookies
- **Auto-redirect**: Unauthenticated users redirected to login page

### Authorization

- **Trip Ownership**: Each trip belongs to a specific user
- **Access Control**: Users can only view, edit, and delete their own trips
- **Protected Routes**: All application routes require authentication
- **API Security**: All API endpoints verify trip ownership before operations

## Implementation Details

### Technology Stack

- **Flask-Login 0.6.3**: Session management and user loading
- **Werkzeug Security**: Password hashing with PBKDF2-SHA256
- **SQLAlchemy**: User model with relationship to trips
- **Flask-WTF**: CSRF protection on authentication forms

### Database Schema

#### Users Table

```python
class User(UserMixin, db.Model):
    id: str (Primary Key)
    username: str (Unique, Indexed)
    email: str (Unique, Indexed)
    password_hash: str
    is_active: bool
    created_at: datetime
    last_login: datetime
    trips: relationship -> Trip[]
```

#### Updated Trips Table

```python
class Trip(db.Model):
    # ... existing fields
    user_id: str (Foreign Key -> users.id, Indexed)
    user: relationship -> User
```

### Code Architecture

#### 1. Models (`src/database/models.py`)

- `User` model with password hashing methods
- `Trip` model updated with `user_id` foreign key
- Relationships between users and trips

#### 2. Repository Layer (`src/database/repository.py`, `src/database/user_repository.py`)

- `UserRepository`: CRUD operations for users

  - `create(username, email, password)` - Create user with hashed password
  - `get(user_id)` - Get user by ID (for Flask-Login)
  - `get_by_username(username)` - Login lookup
  - `get_by_email(email)` - Email validation
  - `update_last_login(user_id)` - Track login times

- `TripRepository`: Updated for multi-user support
  - `create(trip, user_id)` - Create trip for specific user
  - `get(trip_id, user_id=None)` - Get trip with optional ownership verification
  - `list_all(user_id=None)` - List trips filtered by user

#### 3. Service Layer (`src/services/trip_service.py`)

- `TripService.create_trip()` - Accepts `user_id` parameter
- `TripService.get_trip()` - Supports ownership verification
- `TripService.list_trips()` - Filters by user

#### 4. Web Layer (`web_app.py`)

- **LoginManager Configuration**: Loads users from database
- **Authentication Routes**:
  - `GET/POST /register` - User registration
  - `GET/POST /login` - User login
  - `POST /logout` - User logout
- **Protected Routes**: All trip routes use `@login_required` decorator

  - `/` - Home (trips list)
  - `/trip/new` - Create trip
  - `/trip/<trip_id>` - View trip
  - `/trip/<trip_id>/export-pdf` - Export PDF
  - `/trip/<trip_id>/save-as-template` - Save template
  - `/trip/from-template/<template_id>` - Create from template
  - `/trip/<trip_id>/delete` - Delete trip
  - `/api/item/<item_id>/toggle` - Toggle item
  - `/api/trip/<trip_id>/item` - Add item
  - `/api/item/<item_id>` - Delete item
  - `/api/trip/<trip_id>/reorder-items` - Reorder items
  - `/api/trip/<trip_id>/regenerate` - Regenerate AI suggestions

- **Authorization Checks**: Routes verify `trip.user_id == current_user.id` before allowing access

#### 5. Templates

- `templates/login.html` - Login form with CSRF protection
- `templates/register.html` - Registration form with validation
- `templates/base.html` - Updated navigation with login/logout

## Security Features

### Password Security

```python
# Password hashing (never store plaintext)
user.set_password(password)  # Uses generate_password_hash()

# Password verification
user.check_password(password)  # Uses check_password_hash()
```

### Session Security

- Secure session cookies via Flask-Login
- Remember-me functionality (optional)
- Session invalidation on logout
- Auto-logout on inactivity (browser dependent)

### Authorization Pattern

```python
@app.route('/trip/<trip_id>')
@login_required
def view_trip(trip_id):
    # Get trip with ownership verification
    trip = trip_service.get_trip(trip_id, user_id=current_user.id)

    if not trip:
        # User doesn't own this trip or it doesn't exist
        flash('Trip not found or access denied', 'error')
        return redirect(url_for('index'))

    # Proceed with authorized operation
    # ...
```

### CSRF Protection

All forms include CSRF tokens:

```html
<form method="POST">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
  <!-- form fields -->
</form>
```

## Migration Guide

### For New Installations

1. Install dependencies: `pip install -r requirements.txt`
2. Set Flask secret key: `export FLASK_SECRET_KEY="your-secure-random-key"`
3. Initialize database: `python -c "from src.database import init_db; init_db()"`
4. Start app: `python web_app.py`
5. Register first user account

### For Existing Installations

1. **Backup your database**: `cp niknotes.db niknotes.db.backup`
2. Install new dependencies: `pip install -r requirements.txt`
3. Run migration script: `python scripts/migrate_auth.py`
4. Review migration output:
   - Default admin user created (if no users exist)
   - Existing trips assigned to admin user
5. **Change default admin password immediately** if created
6. Test login with admin credentials or register new user
7. Verify existing trips are accessible

## User Management

### Creating First User

```bash
# Option 1: Use migration script (creates admin user)
python scripts/migrate_auth.py

# Option 2: Register via web interface
# Start app and visit /register
```

### Default Admin Account (Migration Script)

- **Username**: `admin`
- **Password**: `changeme123`
- ⚠️ **CHANGE THIS PASSWORD IMMEDIATELY**

### Changing Password

Currently requires direct database access. Future enhancement: password reset feature.

```python
from src.database.repository import UserRepository
from src.database import get_session, close_session

session = get_session()
user = UserRepository.get_by_username('admin')
user.set_password('new_secure_password')
session.commit()
close_session()
```

## Configuration

### Environment Variables

```bash
# Required: Flask secret key
FLASK_SECRET_KEY="your-secure-random-key-here"

# Optional: Session lifetime (default 31 days for remember-me)
PERMANENT_SESSION_LIFETIME=2592000  # seconds
```

### Flask-Login Settings

```python
# In web_app.py
login_manager.login_view = 'login'  # Redirect target for @login_required
login_manager.login_message = 'Please log in to access this page.'
```

## Testing Authentication

### Manual Testing

1. **Register**: Visit `/register`, create account
2. **Login**: Visit `/login`, authenticate
3. **Create Trip**: Create trip as logged-in user
4. **Logout**: Use logout button in nav
5. **Access Control**: Try accessing `/` without login → redirected to login
6. **Multi-user**: Register second user, verify they can't see first user's trips

### Automated Testing

```bash
# Update test fixtures to include authentication
pytest tests/test_auth.py -v

# Test with coverage
pytest --cov=src --cov-report=html
```

## Common Issues & Troubleshooting

### Issue: "Please log in to access this page"

**Cause**: Route requires authentication but user not logged in  
**Solution**: Login at `/login` or register at `/register`

### Issue: "Trip not found or access denied"

**Cause**: Trying to access another user's trip  
**Solution**: This is expected behavior - users can only access their own trips

### Issue: Migration script fails

**Cause**: Database locked or schema mismatch  
**Solution**:

1. Close all database connections
2. Backup database: `cp niknotes.db niknotes.db.backup`
3. Delete database and recreate: `rm niknotes.db && python -c "from src.database import init_db; init_db()"`

### Issue: Existing trips not visible after migration

**Cause**: Trips assigned to wrong user or not filtered correctly  
**Solution**: Check trip.user_id in database matches current_user.id

### Issue: Can't login with admin account

**Cause**: Admin user not created or password incorrect  
**Solution**:

1. Run migration script: `python scripts/migrate_auth.py`
2. Use credentials: admin / changeme123
3. Change password immediately

## Future Enhancements

### Planned Features

- [ ] Password reset via email
- [ ] Email verification for new accounts
- [ ] Two-factor authentication (2FA)
- [ ] Account settings page (change password, email, delete account)
- [ ] Admin role for managing users
- [ ] Audit log for login attempts
- [ ] Rate limiting on authentication endpoints
- [ ] Social authentication (Google, GitHub, etc.)
- [ ] Remember me token rotation

### Security Improvements

- [ ] Account lockout after failed login attempts
- [ ] Password strength meter
- [ ] Password policy enforcement (complexity requirements)
- [ ] Session timeout configuration
- [ ] IP-based rate limiting
- [ ] Suspicious activity detection

## API Reference

### UserRepository Methods

```python
# Create new user
user = UserRepository.create(
    username="john_doe",
    email="john@example.com",
    password="secure_password"
)

# Get user by ID (Flask-Login loader)
user = UserRepository.get(user_id="user_abc123")

# Get user by username (login)
user = UserRepository.get_by_username(username="john_doe")

# Get user by email (validation)
user = UserRepository.get_by_email(email="john@example.com")

# Update last login timestamp
UserRepository.update_last_login(user_id="user_abc123")
```

### User Model Methods

```python
# Hash and set password
user.set_password("my_password")

# Verify password
is_valid = user.check_password("my_password")

# Flask-Login required properties
user.is_authenticated  # Always True for User objects
user.is_active         # From database
user.is_anonymous      # Always False
user.get_id()          # Returns user.id
```

### Trip Ownership

```python
# Create trip for specific user
trip = trip_service.create_trip(
    destination="Tokyo",
    start_date="2024-06-01",
    end_date="2024-06-10",
    travelers=["John", "Jane"],
    user_id=current_user.id  # Required
)

# Get trip with ownership verification
trip = trip_service.get_trip(
    trip_id="trip_abc123",
    user_id=current_user.id  # Optional, verifies ownership
)

# List trips for specific user
trips = trip_service.list_trips(user_id=current_user.id)
```

## Compliance

### OWASP Guidelines

- ✅ A02:2021 – Cryptographic Failures: Passwords properly hashed with PBKDF2
- ✅ A03:2021 – Injection: Parameterized queries via SQLAlchemy
- ✅ A05:2021 – Security Misconfiguration: Secure defaults, environment-based secrets
- ✅ A07:2021 – Identification and Authentication Failures: Session-based auth, secure password hashing

### Security Audit Status

- ✅ **CRITICAL #1**: Hard-coded Flask secret key → RESOLVED (environment variable)
- ✅ **CRITICAL #2**: No authentication/authorization → RESOLVED (Flask-Login implementation)
- ✅ **CRITICAL #3**: Missing CSRF protection → RESOLVED (Flask-WTF)
- 🔄 Remaining items: Database credentials, rate limiting, security headers, etc.

## References

- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
- [Werkzeug Security Utilities](https://werkzeug.palletsprojects.com/en/latest/utils/#module-werkzeug.security)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

---

**Implementation Date**: January 2025  
**Version**: 1.1.0  
**Status**: ✅ COMPLETE - Production Ready
