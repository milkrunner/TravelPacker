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
    
    print(f"🚀 Initializing NikNotes application (environment: {config_name or 'development'})")
    
    # Initialize database
    if config.USE_DATABASE:
        init_db()
        print("✅ Database initialized")
    
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
    
    print("✅ Application factory setup complete")
    
    return app


def _apply_rate_limits(app, config):
    """Apply rate limits to specific endpoints after registration"""
    if not config.RATELIMIT_ENABLED:
        return
    
    from src.extensions import limiter
    
    # Define rate limits for specific endpoints
    rate_limits = {
        'trips.new_trip': '20 per hour',
        'trips.delete_trip': '20 per hour',
        'api.toggle_item': '100 per hour',
        'api.add_item': '50 per hour',
        'api.delete_item': '100 per hour',
    }
    
    for endpoint, limit in rate_limits.items():
        try:
            limiter.limit(limit)(app.view_functions[endpoint])
            print(f"  Applied rate limit '{limit}' to {endpoint}")
        except KeyError:
            # Endpoint not found, skip
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
    
    print("✅ Services initialized")
    
    return service_container


def _init_blueprints(service_container):
    """Initialize blueprints with service dependencies"""
    from src.blueprints import main, trips, api, auth
    
    # Inject services into blueprints
    main.init_services(service_container)
    trips.init_services(service_container)
    api.init_services(service_container)
    auth.init_services(service_container)
