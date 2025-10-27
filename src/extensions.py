"""
Flask extensions initialization
"""

from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_login import LoginManager
from src.utils.security_utils import rate_limit_key_func


# Initialize extensions without app binding
csrf = CSRFProtect()
limiter = None  # Will be initialized in init_extensions with proper storage
talisman = Talisman()
login_manager = LoginManager()


def init_extensions(app):
    """Initialize Flask extensions with app instance"""
    from src.database.models import User as DBUser
    from src.database import get_session, close_session
    
    # CSRF Protection
    csrf.init_app(app)
    
    # Rate Limiter with per-user and per-IP support
    global limiter
    if app.config.get('RATELIMIT_ENABLED', True):
        storage_url = app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
        limiter = Limiter(
            key_func=rate_limit_key_func,  # Use custom key function for user+IP
            app=app,
            default_limits=["200 per day", "50 per hour"],
            storage_uri=storage_url,
            storage_options={"socket_connect_timeout": 30} if "redis://" in storage_url else {},
            strategy="fixed-window",
        )
        backend_type = "Redis" if "redis://" in storage_url else "in-memory"
        print(f"✅ Rate limiter initialized with {backend_type} backend (per-user + per-IP)")
        
        # Start security monitor cleanup task
        from src.utils.security_utils import start_cleanup_task
        start_cleanup_task()
    else:
        limiter = Limiter(
            key_func=get_remote_address,
            app=app,
            default_limits=[],
            storage_uri="memory://",
            strategy="fixed-window",
        )
        print("✅ Rate limiter initialized (disabled)")
    
    # Security Headers (Talisman)
    csp = {
        'default-src': ["'self'"],
        'script-src': ["'self'", 'https://accounts.google.com/gsi/client'],
        'style-src': ["'self'", "'unsafe-inline'", 'https://accounts.google.com/gsi/style'],  # unsafe-inline required for Google Sign-In
        'img-src': ["'self'", 'data:', 'https:', 'https://lh3.googleusercontent.com'],
        'font-src': ["'self'"],
        'connect-src': ["'self'", 'https://accounts.google.com'],
        'frame-src': ['https://accounts.google.com'],
        'frame-ancestors': ["'none'"],
        'report-uri': ['/csp-report'],
    }
    
    force_https = app.config.get('FORCE_HTTPS', False)
    talisman.init_app(
        app,
        force_https=force_https,
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src'],  # Only nonce for scripts, not styles (Google Sign-In needs unsafe-inline)
        frame_options='DENY',
        referrer_policy='strict-origin-when-cross-origin',
    )
    print(f"✅ Security headers enabled (HTTPS redirect: {force_https})")
    
    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # type: ignore
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login"""
        db_session = get_session()
        try:
            return db_session.query(DBUser).filter(DBUser.id == user_id).first()
        finally:
            close_session()
    
    print("✅ Flask extensions initialized")
