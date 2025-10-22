# Google Sign-In Authentication

## Overview

NikNotes uses **Google Identity Services** for authentication - the modern, simple way to let users sign in with their Google accounts. No OAuth client secrets needed, no redirect flows - just a simple "Sign in with Google" button!

## Why Google Identity Services (not OAuth)?

- **Simpler Setup**: Only need a Client ID, no client secret
- **Better UX**: Users click one button and are immediately signed in
- **More Secure**: Token verification happens entirely server-side via Google's JWT validation
- **Modern**: Google's latest authentication solution (replaces legacy OAuth flows)
- **No Maintenance**: No OAuth libraries to update, no callback URLs to manage

## Quick Setup (5 Minutes)

### 1. Get Your Google Client ID

Visit <https://console.cloud.google.com/apis/credentials>

1. Create a new project or select an existing one
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Application type: **Web application**
4. Name: "NikNotes" (or whatever you prefer)
5. **Authorized JavaScript origins**:
   - Development: `http://localhost:5000`
   - Production: `https://your-domain.com`
6. Click "Create"
7. **Copy the Client ID** (you don't need the Client Secret!)

### 2. Add Client ID to `.env`

```bash
GOOGLE_CLIENT_ID=834288809-xxxxxxx.apps.googleusercontent.com
```

That's it! Restart your app and the "Sign in with Google" button will appear.

### 3. Test It

1. Open <http://localhost:5000>
2. Click "Sign in with Google"
3. Choose your Google account
4. You're logged in! 🎉

## How It Works

### Client Side (JavaScript)

1. Google's library loads on the login page
2. User clicks "Sign in with Google" button
3. Google shows account picker popup
4. User selects account
5. Google generates a signed JWT token
6. Token is sent to our backend via AJAX

### Server Side (Python)

1. Backend receives JWT token from client
2. **Token verification** using `google-auth` library:
   - Validates signature with Google's public keys
   - Checks issuer is accounts.google.com
   - Verifies token not expired
   - Extracts user info (email, name, picture)
3. **Find or create user** in database:
   - Check if user exists by Google ID
   - If not, check by email (link existing accounts)
   - If not, create new user
4. **Flask-Login session** established
5. User redirected to dashboard

## Architecture

```text
┌─────────────┐
│   Client    │ (Browser)
│  Login Page │
└──────┬──────┘
       │ 1. Load page
       ↓
┌─────────────────────┐
│ Google Identity     │
│ Services (GSI)      │
│ accounts.google.com │
└──────┬──────────────┘
       │ 2. Show account picker
       │ 3. Return JWT token
       ↓
┌─────────────┐
│  AJAX POST  │ /auth/google
│ {credential}│
└──────┬──────┘
       ↓
┌────────────────────┐
│ GoogleSignInService│ (oauth_service.py)
│ verify_google_token│ ←── google.oauth2.id_token
└──────┬─────────────┘
       │ 4. Token valid?
       ↓
┌────────────────┐
│  User Database │
│ find_or_create │
└──────┬─────────┘
       │ 5. User object
       ↓
┌────────────┐
│ Flask-Login│
│ login_user │
└──────┬─────┘
       │ 6. Session created
       ↓
┌─────────────┐
│ Dashboard   │
│ (Home Page) │
└─────────────┘
```

## Security Features

### Token Verification

Every Google Sign-In token is cryptographically verified:

```python
idinfo = id_token.verify_oauth2_token(
    credential,
    google_requests.Request(),
    self.client_id  # Ensures token is for OUR app
)
```

This validates:

- **Signature**: Token signed by Google's private key
- **Audience**: Token issued for our Client ID
- **Issuer**: Token from accounts.google.com
- **Expiration**: Token not expired (typically 1 hour)

### Email Verification

Only accepts tokens with verified emails:

```python
if not user_info.get('email_verified', False):
    return error('Email not verified with Google')
```

### Account Linking

Smart account management:

- Existing Google users → immediate login
- Existing email users → link Google to account
- New users → create account with Google

### Content Security Policy

CSP allows Google's domains:

```python
'script-src': ['https://accounts.google.com/gsi/client'],
'frame-src': ['https://accounts.google.com'],
'connect-src': ['https://accounts.google.com'],
```

### CSRF Protection

CSRF exempt for Google Sign-In endpoint (tokens are cryptographically secure):

```python
@csrf.exempt  # Token verification provides security
```

## User Experience Flow

### First-Time User

1. Click "Sign in with Google"
2. Select Google account
3. **Auto-created account** with:
   - Username from name or email
   - Email from Google
   - Profile picture from Google
   - OAuth provider: 'google'
4. Logged in immediately

### Returning User

1. Click "Sign in with Google"
2. Recognized by Google ID
3. Profile picture updated if changed
4. Logged in (< 1 second)

### Existing Email User

If user previously registered with email/password:

1. Signs in with Google for first time
2. System matches by email address
3. **Links Google account** to existing account
4. Future logins use either method

## Code Reference

### Service Layer

**`src/services/oauth_service.py`** - `GoogleSignInService`

- `verify_google_token()` - Validates JWT with Google
- `find_or_create_user()` - User management
- `_generate_username()` - Unique username creation

### Web Routes

**`web_app.py`**

- `GET /login` - Shows login page with Google button
- `POST /auth/google` - Verifies token, logs user in
- `GET /logout` - Logs user out

### Templates

**`templates/login.html`**

- Google Identity Services script include
- Sign-in button (auto-rendered by Google)
- JavaScript callback handler

### Database Models

**`src/database/models.py`** - User model

```python
oauth_provider: str  # 'google'
oauth_id: str        # Google user ID (sub claim)
profile_picture: str # Google profile picture URL
```

## Dependencies

```requirements.txt
google-auth==2.23.4  # JWT token verification
flask-login==0.6.3   # Session management
```

**No OAuth libraries needed!** (authlib, cachelib removed)

## Configuration

### Minimal `.env`

```bash
# Only need Client ID (no secret!)
GOOGLE_CLIENT_ID=your_client_id_here

# Flask secret for sessions
FLASK_SECRET_KEY=your_32_char_hex_key
```

### Production Checklist

- [ ] Add production domain to authorized JavaScript origins
- [ ] Use HTTPS (required for Google Sign-In in production)
- [ ] Set `FORCE_HTTPS=True` in environment
- [ ] Generate strong FLASK_SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] Consider adding brand/logo in Google Cloud Console

## Troubleshooting

### "Sign in with Google" button doesn't appear

1. Check `GOOGLE_CLIENT_ID` in `.env`
2. Restart application
3. Check browser console for CSP errors
4. Verify Client ID format: `xxx-xxx.apps.googleusercontent.com`

### "Invalid token" error

1. Check authorized JavaScript origins match your domain
2. Verify Client ID matches the one in Google Console
3. Ensure HTTPS in production (Google requires it)
4. Check token hasn't expired (1 hour lifetime)

### "Email not verified" error

User's Google account email is not verified. Ask user to verify their email with Google.

### CSP violations

If Content Security Policy blocks Google scripts:

```python
'script-src': ['https://accounts.google.com/gsi/client'],
'frame-src': ['https://accounts.google.com'],
```

## Comparison: OAuth vs. Google Sign-In

| Feature             | OAuth 2.0           | Google Identity Services |
| ------------------- | ------------------- | ------------------------ |
| **Setup**           | Client ID + Secret  | Client ID only           |
| **Flow**            | Redirect → Callback | Button → Token           |
| **User Steps**      | 2-3 clicks          | 1 click                  |
| **Code Complexity** | ~200 lines          | ~100 lines               |
| **Dependencies**    | authlib, cachelib   | google-auth              |
| **Security**        | OAuth tokens        | JWT verification         |
| **Maintenance**     | Manage secrets      | No secrets               |
| **UX**              | Good                | Excellent                |

## References

- [Google Identity Services Docs](https://developers.google.com/identity/gsi/web)
- [google-auth Library](https://google-auth.readthedocs.io/)
- [JWT Token Verification](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token)

## Migration from OAuth

If migrating from OAuth implementation:

1. ✅ Users keep their accounts (matched by email)
2. ✅ No data loss (Google ID stored in same field)
3. ✅ Automatic account linking
4. ✅ Simpler codebase (fewer dependencies)

---

**Status**: ✅ Implemented and Production-Ready

**Last Updated**: October 22, 2025
