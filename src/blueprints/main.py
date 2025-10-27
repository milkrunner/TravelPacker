"""
Main routes blueprint
"""

from typing import Optional
from flask import Blueprint, render_template, jsonify, request
from flask_login import current_user
from src.extensions import csrf
from src.services.trip_service import TripService


main_bp = Blueprint('main', __name__)

# Service will be initialized in factory
trip_service: Optional[TripService] = None


def init_services(service_container):
    """Initialize blueprint with services"""
    global trip_service
    trip_service = service_container['trip_service']


@main_bp.route('/')
def index():
    """Home page - list all trips and templates"""
    # If user is not logged in, show landing page
    if not current_user.is_authenticated:
        return render_template('index.html', trips=[], templates=[], show_landing=True)
    
    # Show user's trips and templates
    assert trip_service is not None, "TripService not initialized"
    all_trips = trip_service.list_trips(user_id=current_user.id)
    trips = [t for t in all_trips if not t.is_template]
    templates = [t for t in all_trips if t.is_template]
    return render_template('index.html', trips=trips, templates=templates, show_landing=False)


@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    from src.database import test_connection
    from src.services.cache_service import CacheService
    
    # Initialize cache service to check Redis
    cache = CacheService()
    
    health_status = {
        "status": "healthy",
        "database": "connected" if test_connection() else "disconnected",
        "redis": "connected" if cache.enabled else "disabled",
    }
    
    # Set overall status based on database (critical) and redis (optional)
    database_ok = health_status["database"] == "connected"
    
    if not database_ok:
        health_status["status"] = "degraded"
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200


@main_bp.route('/csp-report', methods=['POST'])
@csrf.exempt  # Browser-generated CSP reports don't include CSRF tokens
def csp_report():
    """Endpoint for receiving Content Security Policy violation reports"""
    try:
        report = request.get_json(force=True)
        
        if not report or 'csp-report' not in report:
            return '', 204
        
        violation = report['csp-report']
        
        # Sanitize CSP report fields to prevent log injection
        def sanitize_for_log(value):
            """Remove newlines and control characters from log values"""
            if not isinstance(value, str):
                return value
            return value.replace('\n', '').replace('\r', '').replace('\t', ' ').replace('\x00', '')
        
        # Extract and sanitize key violation details
        blocked_uri = sanitize_for_log(violation.get('blocked-uri', 'unknown'))
        violated_directive = sanitize_for_log(violation.get('violated-directive', 'unknown'))
        document_uri = sanitize_for_log(violation.get('document-uri', 'unknown'))
        
        # Log CSP violations for security monitoring
        print(f"⚠️  CSP Violation: blocked-uri={blocked_uri}, "
              f"violated-directive={violated_directive}, "
              f"document-uri={document_uri}")
        
        # Return 204 No Content (CSP reports don't need a response body)
        return '', 204
        
    except Exception as e:
        # Log parsing errors but don't expose them
        print(f"Error processing CSP report: {e}")
        return '', 204


@main_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with custom page"""
    print(f"Internal error: {error}")
    return render_template('errors/500.html'), 500


@main_bp.app_errorhandler(400)
def handle_csrf_error(error):
    """Handle CSRF token expiration with user-friendly page"""
    from flask_wtf.csrf import CSRFError
    
    # Check if this is a CSRF error
    if isinstance(error, CSRFError):
        print(f"⚠️  CSRF token expired or invalid: {error}")
        return render_template('errors/csrf_error.html'), 400
    
    # For other 400 errors, return generic bad request
    return jsonify({"status": "error", "message": "Bad request"}), 400


@main_bp.app_errorhandler(Exception)
def handle_exception(error):
    """Handle uncaught exceptions in production"""
    from flask import current_app
    from werkzeug.exceptions import HTTPException
    
    # HTTP exceptions (404, 405, etc.) should be returned as-is, not re-raised
    if isinstance(error, HTTPException):
        return error
    
    print(f"Unhandled exception: {error}")
    
    if current_app.debug:
        raise error
    else:
        return render_template('errors/500.html'), 500
