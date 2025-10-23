"""
Google Sign-In authentication service
Uses Google Identity Services for simple, secure authentication
No OAuth client secret needed - just a Google Client ID
"""

import os
import uuid
import datetime
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from src.database import get_session, close_session
from src.database.models import User as DBUser


class GoogleSignInService:
    """Service for Google Sign-In authentication"""
    
    def __init__(self, app=None):
        self.client_id = None
        self.enabled = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Google Sign-In with Flask app"""
        # Get Google Client ID from environment
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        
        if not self.client_id or self.client_id == 'your_google_client_id_here':
            print("⚠️  Google Sign-In not configured - set GOOGLE_CLIENT_ID in .env")
            print("    Get a Client ID at: https://console.cloud.google.com/apis/credentials")
            self.enabled = False
            return
        
        self.enabled = True
        print(f"✅ Google Sign-In initialized (Client ID: {self.client_id[:20]}...)")
    
    def verify_google_token(self, credential):
        """Verify Google ID token and return user info"""
        if not self.enabled:
            return None
        
        try:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                credential, 
                google_requests.Request(), 
                self.client_id
            )
            
            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            # Token is valid, extract user info
            return {
                'oauth_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name'),
                'profile_picture': idinfo.get('picture'),
                'email_verified': idinfo.get('email_verified', False)
            }
        except ValueError as e:
            print(f"Google token verification failed: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error verifying Google token: {e}")
            return None
    
    def find_or_create_user(self, user_info):
        """Find existing user or create new one from Google Sign-In data"""
        db_session = get_session()
        try:
            # Try to find existing user by Google ID
            user = db_session.query(DBUser).filter(
                DBUser.oauth_provider == 'google',
                DBUser.oauth_id == user_info['oauth_id']
            ).first()
            
            if user:
                # Update last login and profile picture
                setattr(user, 'last_login', datetime.datetime.now(datetime.timezone.utc))
                if user_info.get('profile_picture'):
                    setattr(user, 'profile_picture', user_info['profile_picture'])
                db_session.commit()
                return user
            
            # Try to find by email (user might have registered with password)
            user = db_session.query(DBUser).filter(
                DBUser.email == user_info['email']
            ).first()
            
            if user:
                # Link Google account to existing email account
                setattr(user, 'oauth_provider', 'google')
                setattr(user, 'oauth_id', user_info['oauth_id'])
                setattr(user, 'profile_picture', user_info.get('profile_picture'))
                setattr(user, 'last_login', datetime.datetime.now(datetime.timezone.utc))
                db_session.commit()
                return user
            
            # Create new user
            username = self._generate_username(user_info['email'], user_info.get('name'))
            
            # Some legacy SQLite databases may still have password_hash as NOT NULL (pre-migration)
            # If so, we provide a deterministic dummy hash value. It's impossible to log in with it
            # because we never expose password-based auth for Google-only users. Using a fixed UUID-derived
            # string ensures we don't leak semantics. We avoid leaving it completely empty to satisfy constraint.
            dummy_password_hash = None
            try:
                # Introspect table to see if password_hash is declared NOT NULL (SQLite only)
                from sqlalchemy import text as _text
                raw_conn = db_session.connection().connection  # DBAPI connection
                cursor = raw_conn.cursor()
                cursor.execute("PRAGMA table_info(users)")
                cols = cursor.fetchall()
                for c in cols:
                    if c[1] == 'password_hash' and c[3] == 1:  # c[3] == notnull flag
                        # Provide dummy hashed value (looks like a werkzeug hash but won't match any real password)
                        dummy_password_hash = 'pbkdf2:sha256:dummy$' + uuid.uuid4().hex
                        break
                cursor.close()
            except Exception:
                # Silently ignore introspection issues
                pass

            new_user = DBUser(
                id=f"user_{uuid.uuid4().hex[:8]}",
                username=username,
                email=user_info['email'],
                oauth_provider='google',
                oauth_id=user_info['oauth_id'],
                profile_picture=user_info.get('profile_picture'),
                is_active=True,
                last_login=datetime.datetime.now(datetime.timezone.utc)
            )

            # Apply dummy password hash only if needed
            if dummy_password_hash:
                new_user.password_hash = dummy_password_hash
            
            db_session.add(new_user)
            db_session.commit()
            db_session.refresh(new_user)
            
            print(f"✅ Created new user via Google Sign-In: {new_user.email}")
            return new_user
            
        except Exception as e:
            db_session.rollback()
            print(f"Error creating/finding Google user: {e}")
            return None
        finally:
            close_session()
    
    def _generate_username(self, email, name=None):
        """Generate a unique username from email or name"""
        db_session = get_session()
        try:
            # Try using name first
            if name:
                base_username = name.lower().replace(' ', '_')[:20]
            else:
                # Use email prefix
                base_username = email.split('@')[0][:20]
            
            # Remove special characters
            base_username = ''.join(c for c in base_username if c.isalnum() or c == '_')
            
            # Check if username exists
            username = base_username
            counter = 1
            while db_session.query(DBUser).filter(DBUser.username == username).first():
                username = f"{base_username}_{counter}"
                counter += 1
            
            return username
        finally:
            close_session()
