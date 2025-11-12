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
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


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
            logger.warning("Google Sign-In not configured - set GOOGLE_CLIENT_ID in .env")
            logger.info("Get a Client ID at: https://console.cloud.google.com/apis/credentials")
            self.enabled = False
            return
        
        self.enabled = True
        logger.info(f"Google Sign-In initialized (Client ID: {self.client_id[:20]}...)")
    
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
            logger.warning(f"Google token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying Google token: {e}")
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
            username = self._generate_username(db_session, user_info['email'], user_info.get('name'))
            
            # Password hash is nullable for OAuth-only users (per models.py schema)
            # No need for dummy hash - NULL is valid for OAuth accounts
            new_user = DBUser(
                id=f"user_{uuid.uuid4().hex[:8]}",
                username=username,
                email=user_info['email'],
                oauth_provider='google',
                oauth_id=user_info['oauth_id'],
                profile_picture=user_info.get('profile_picture'),
                last_login=datetime.datetime.now(datetime.timezone.utc)
            )
            
            db_session.add(new_user)
            db_session.commit()
            db_session.refresh(new_user)
            
            # Sanitize email for safe logging (prevent log injection)
            email = getattr(new_user, 'email', 'unknown')
            safe_email = email.replace('\n', '').replace('\r', '').replace('\t', ' ') if email and email != 'unknown' else 'unknown'
            logger.info(f"Created new user via Google Sign-In: {safe_email}")
            return new_user
            
        except Exception as e:
            # Rollback the transaction on any error (critical for PostgreSQL)
            try:
                db_session.rollback()
            except Exception as rollback_error:
                logger.warning(f"Rollback failed (session might be closed): {rollback_error}")
            logger.error(f"Error creating/finding Google user: {e}", exc_info=True)
            return None
        finally:
            close_session()
    
    def _generate_username(self, db_session, email, name=None):
        """Generate a unique username from email or name"""
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
