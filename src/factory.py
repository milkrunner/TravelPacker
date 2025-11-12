"""
Application factory for Flask app
"""

from flask import Flask
from src.config import get_config
from src.extensions import init_extensions
from src.blueprints import register_blueprints
from src.database import init_db
from src.services.ai_service import AIService
from src.services.trip_service import TripService
from src.services.packing_list_service import PackingListService
from src.services.oauth_service import GoogleSignInService
from src.utils.logging_config import init_app_logging, get_logger

logger = get_logger(__name__)


def create_app(config_name=None):
    """
    Application factory pattern
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing')
        
    Returns:
        Configured Flask application instance
    """
    # Create Flask app
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize logging system
    init_app_logging(app)
    logger.info(f"Initializing NikNotes application (environment: {config_name or 'development'})")
    
    # Initialize database
    if config.USE_DATABASE:
        init_db()
        logger.info("Database initialized")
    
    # Initialize Flask extensions (CSRF, rate limiter, security headers, login manager)
    init_extensions(app)
    
    # Initialize services
    service_container = _init_services(app, config)
    
    # Initialize blueprints with services
    _init_blueprints(service_container)
    
    # Register blueprints with app
    register_blueprints(app)
    
    # Apply rate limits to specific endpoints
    _apply_rate_limits(app, config)
    
    logger.info("Application factory setup complete")
    
    return app


def _apply_rate_limits(app, config):
    """Apply rate limits to specific endpoints after registration"""
    if not config.RATELIMIT_ENABLED:
        return
    
    from src.extensions import limiter
    
    # Define rate limits for endpoints by sensitivity level
    
    # CRITICAL: Destructive operations (delete, regenerate)
    critical_limits = {
        'trips.delete_trip': '5 per hour',  # Very strict - deletes data
        'api.delete_item': '10 per hour',   # Strict - deletes items
        'api.regenerate_suggestions': '3 per hour',  # Strict - expensive AI operation
    }
    
    # SENSITIVE: Authentication and account operations
    sensitive_limits = {
        'auth.login': '10 per hour',  # Prevent brute-force
        'auth.register': '5 per hour',  # Prevent spam accounts
        'auth.logout': '20 per hour',
    }
    
    # MODERATE: Write operations
    moderate_limits = {
        'trips.new_trip': '20 per hour',
        'api.add_item': '50 per hour',
        'api.save_template': '10 per hour',
    }
    
    # STANDARD: Read operations
    standard_limits = {
        'api.toggle_item': '100 per hour',
    }
    
    # Apply all limits
    all_limits = {
        **critical_limits,
        **sensitive_limits,
        **moderate_limits,
        **standard_limits
    }
    
    # Exempt CSP reporting from rate limiting (browser generates reports)
    try:
        limiter.exempt(app.view_functions['main.csp_report'])
        logger.debug("[EXEMPT] CSP reporting endpoint exempt from rate limiting")
    except KeyError:
        pass
    
    for endpoint, limit in all_limits.items():
        try:
            limiter.limit(limit)(app.view_functions[endpoint])
            category = (
                'CRITICAL' if endpoint in critical_limits else
                'SENSITIVE' if endpoint in sensitive_limits else
                'MODERATE' if endpoint in moderate_limits else
                'STANDARD'
            )
            logger.debug(f"[{category}] Applied rate limit '{limit}' to {endpoint}")
        except KeyError:
            # Endpoint not found, skip silently
            pass


def _init_services(app, config):
    """Initialize application services"""
    # Initialize AI service
    ai_service = AIService()
    
    # Initialize trip service
    trip_service = TripService(use_database=config.USE_DATABASE)
    
    # Initialize packing list service
    packing_service = PackingListService(ai_service, use_database=config.USE_DATABASE)
    
    # Initialize OAuth service
    google_signin_service = GoogleSignInService(app)
    
    # Package services into container for blueprint initialization
    service_container = {
        'ai_service': ai_service,
        'trip_service': trip_service,
        'packing_service': packing_service,
        'google_signin_service': google_signin_service
    }
    
    logger.info("Services initialized")
    
    return service_container


def _init_blueprints(service_container):
    """Initialize blueprints with service dependencies"""
    from src.blueprints import main, trips, api, auth
    
    # Inject services into blueprints
    main.init_services(service_container)
    trips.init_services(service_container)
    api.init_services(service_container)
    auth.init_services(service_container)
