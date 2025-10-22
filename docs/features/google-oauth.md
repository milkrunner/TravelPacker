# Google OAuth Authentication Implementation

## Overview
NikNotes now supports **Google OAuth 2.0 authentication**, allowing users to sign in with their Google account. No passwords are stored - authentication is handled entirely through Google's secure OAuth flow.

## Features Implemented

### ✅ **1. Google OAuth Integration**
- **Authlib** library for OAuth 2.0 flow
- Secure token validation
- Automatic user creation/linking
- Profile picture support

### ✅ **2. Database Changes**
Added OAuth support to User model:
- `oauth_provider` - Provider name ('google')
- `oauth_id` - Google's unique user ID
- `profile_picture` - User's Google profile image URL
- `password_hash` - Now nullable (OAuth users don't need passwords)
- Composite index on `(oauth_provider, oauth_id)` for fast lookups

### ✅ **3. Flask-Login Integration**
- Session-based authentication
- `@login_required` decorator on protected routes
- `current_user` available in all route handlers
- Automatic login/logout flow

### ✅ **4. User Experience**
- Beautiful login page with Google sign-in button
- Profile picture display in navigation
- Username generation from Google profile
- Account linking if email already exists

### ✅ **5. Security**
- CSRF protection on all routes
- Secure OAuth state validation
- Audit logging for login/logout events
- Rate limiting on authentication endpoints

## Setup Instructions

### 1. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable "Google+ API"
4. Create OAuth 2.0 credentials:
   - Application type: **Web application**
   - Authorized redirect URIs:
     - `http://localhost:5000/login/google/callback` (development)
     - `https://yourdomain.com/login/google/callback` (production)
5. Copy **Client ID** and **Client Secret**

### 2. Configure Environment Variables

Add to `.env` file:
```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies:
- `flask-login==0.6.3` - Session management
- `authlib==1.3.0` - OAuth 2.0 client
- `cachelib==0.10.2` - Session storage

### 4. Run Database Migration

```bash
python scripts/migrations/add_oauth_support.py
```

This adds OAuth columns to the `users` table.

### 5. Start the Application

```bash
# Development
python web_app.py

# Docker
docker compose up -d --build
```

## Usage Flow

### First-Time User
1. Visit `http://localhost:5000`
2. Click "🔐 Login" button
3. Click "Continue with Google"
4. Google OAuth consent screen appears
5. User grants permissions
6. Redirected back to app
7. New account created automatically
8. Logged in and redirected to trips page

### Returning User
1. Click "Continue with Google"
2. Google recognizes user
3. Instant redirect back to app
4. Logged in immediately

### Account Linking
If user already has an account with the same email:
- OAuth info added to existing account
- No duplicate accounts created
- User can log in with Google OR password (if set)

## Technical Architecture

### OAuthService (`src/services/oauth_service.py`)

```python
class OAuthService:
    def init_app(app):
        # Initialize Authlib OAuth client
    
    def get_authorization_url(redirect_uri):
        # Generate Google OAuth URL
    
    def handle_callback(redirect_uri):
        # Validate token and get user info
    
    def find_or_create_user(provider, user_info):
        # Create new user or link to existing
```

### Routes (`web_app.py`)

- `GET /login` - Login page with Google button
- `GET /login/google` - Initiates OAuth flow
- `GET /login/google/callback` - Handles OAuth callback
- `GET /logout` - Logs out current user

### User Model Updates

```python
class User(Base, UserMixin):
    # Existing fields
    id = Column(String, primary_key=True)
    username = Column(String(80), unique=True, index=True)
    email = Column(String(120), unique=True, index=True)
    password_hash = Column(String(255), nullable=True)  # Now nullable
    
    # New OAuth fields
    oauth_provider = Column(String(50))
    oauth_id = Column(String(255), index=True)
    profile_picture = Column(String(500))
```

## Security Considerations

### ✅ **OAuth Security**
- State parameter prevents CSRF attacks
- Token validation with Google's keys
- Secure redirect URI validation
- HTTPS required in production

### ✅ **Session Security**
- Flask-Login secure session cookies
- Secret key required (crashes if default)
- Session timeout support
- CSRF protection on all forms

### ✅ **Account Security**
- Email-based account linking
- No password storage for OAuth users
- Audit logging for all auth events
- Rate limiting on auth endpoints

## Configuration Options

### Required
```bash
GOOGLE_CLIENT_ID=xxx           # From Google Cloud Console
GOOGLE_CLIENT_SECRET=xxx       # From Google Cloud Console
FLASK_SECRET_KEY=xxx           # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
```

### Optional
```bash
GOOGLE_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration
FORCE_HTTPS=True               # Enable in production
```

## Troubleshooting

### OAuth Not Working
1. Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
2. Verify redirect URI matches Google Cloud Console exactly
3. Ensure "Google+ API" is enabled in Google Cloud
4. Check app logs for OAuth errors

### Database Migration Failed
1. Ensure PostgreSQL is running
2. Check `DATABASE_URL` in `.env`
3. Verify database user has ALTER TABLE permissions
4. Run migration script with verbose output

### Users Not Logging In
1. Check Flask secret key is set correctly
2. Verify session cookies are enabled in browser
3. Check `login_manager.login_view` is set
4. Ensure `@login_required` decorator is used

## Testing

### Manual Testing
1. **Fresh User**: Sign in with new Google account → Verify account created
2. **Returning User**: Sign in again → Verify instant login
3. **Account Linking**: Create account, then sign in with same email → Verify OAuth linked
4. **Logout**: Click logout → Verify session cleared
5. **Protected Routes**: Try accessing `/trip/new` without login → Verify redirect to login

### Security Testing
1. Verify CSRF protection on all auth routes
2. Test OAuth state validation
3. Verify audit logs for all auth events
4. Test rate limiting on auth endpoints

## Future Enhancements

### Potential Additions
- GitHub OAuth support
- Microsoft OAuth support
- Two-factor authentication (2FA)
- Email verification for password users
- Password reset flow
- Account deletion

### OAuth Provider Pattern
The `OAuthService` is designed to support multiple providers:

```python
# Add GitHub OAuth
github = oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    ...
)
```

## References

- [Authlib Documentation](https://docs.authlib.org/)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
- [Google OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)

## Support

For issues or questions:
1. Check application logs for errors
2. Verify environment variables are set
3. Ensure database migration completed
4. Review Google Cloud Console settings
