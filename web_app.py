"""
Web application for NikNotes
Flask-based web interface for the trip packing assistant
"""

import os

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from datetime import datetime
from dotenv import load_dotenv
from pydantic import ValidationError
from src.services.trip_service import TripService
from src.services.ai_service import AIService
from src.services.packing_list_service import PackingListService
from src.services.pdf_service import PDFService
from src.models.trip import TravelStyle, TransportMethod
from src.database import init_db
from src.validators import (
    TripCreateRequest, ItemCreateRequest, ItemToggleRequest,
    UserRegistrationRequest, UserLoginRequest
)
from src.services.audit_service import AuditLogger
from src.services.sanitization_service import ContentSanitizer

load_dotenv()

app = Flask(__name__)

secret_key = os.getenv('FLASK_SECRET_KEY')
invalid_keys = {
    '',
    'your-secret-key-change-in-production',
    'change_me',
    'changeme',
    'change_me_to_a_secure_random_value',
}
if not secret_key or secret_key.strip().lower() in invalid_keys:
    raise RuntimeError('FLASK_SECRET_KEY environment variable must be set to a secure value')

app.config['SECRET_KEY'] = secret_key

# Enable CSRF protection
csrf = CSRFProtect(app)

# Setup rate limiting
# Try to use Redis for distributed rate limiting, fall back to in-memory
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Check if Redis is available before trying to use it
use_redis = os.getenv('USE_REDIS', 'False').lower() == 'true'

if use_redis:
    try:
        limiter = Limiter(
            get_remote_address,
            app=app,
            default_limits=["200 per day", "50 per hour"],
            storage_uri=redis_url,
            storage_options={"socket_connect_timeout": 30},
            strategy="fixed-window",
        )
        print(f"✅ Rate limiter initialized with Redis backend: {redis_url}")
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to Redis ({e}), using in-memory rate limiting")
        limiter = Limiter(
            get_remote_address,
            app=app,
            default_limits=["200 per day", "50 per hour"],
            storage_uri="memory://",
            strategy="fixed-window",
        )
else:
    # Use in-memory storage by default for development
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
        strategy="fixed-window",
    )
    print("✅ Rate limiter initialized with in-memory backend (development mode)")

# Setup security headers
# Configure Talisman for production-ready security headers
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'"],  # Allow inline scripts for dynamic UI
    'style-src': ["'self'", "'unsafe-inline'"],   # Allow inline styles for themes
    'img-src': ["'self'", 'data:', 'https:'],     # Allow data URIs and HTTPS images
    'font-src': ["'self'"],
    'connect-src': ["'self'"],
    'frame-ancestors': ["'none'"],                 # Prevent clickjacking
    'report-uri': ['/csp-report'],                 # CSP violation reporting endpoint
}

# Initialize Talisman with flexible settings for development/production
force_https = os.getenv('FORCE_HTTPS', 'False').lower() == 'true'
Talisman(
    app,
    force_https=force_https,  # Enable HTTPS redirect in production
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,  # 1 year
    content_security_policy=csp,
    content_security_policy_nonce_in=['script-src'],
    frame_options='DENY',  # Prevent clickjacking
    referrer_policy='strict-origin-when-cross-origin',
)
print(f"✅ Security headers enabled (HTTPS redirect: {force_https})")

# Setup login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize database
init_db()

# Initialize services with database enabled
ai_service = AIService()
trip_service = TripService(use_database=True)
packing_service = PackingListService(ai_service, use_database=True)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    from src.database.repository import UserRepository
    return UserRepository.get(user_id)


@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    """User registration with input validation"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        from src.database.repository import UserRepository
        
        try:
            # Sanitize and validate input
            raw_username = ContentSanitizer.sanitize_strict(request.form.get('username', ''))
            raw_email = ContentSanitizer.sanitize_email(request.form.get('email', ''))
            
            # Validate input using Pydantic
            validated_data = UserRegistrationRequest(
                username=raw_username,
                email=raw_email,
                password=request.form.get('password', '')
            )
            
            confirm_password = request.form.get('confirm_password', '')
            
            # Check password confirmation
            if validated_data.password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('register.html')
            
            # Check if username exists
            if UserRepository.get_by_username(validated_data.username):
                flash('Username already taken', 'error')
                return render_template('register.html')
            
            # Check if email exists
            if UserRepository.get_by_email(validated_data.email):
                flash('Email already registered', 'error')
                return render_template('register.html')
            
            # Create user with validated data
            user = UserRepository.create(
                validated_data.username,
                validated_data.email,
                validated_data.password
            )
            if user:
                # Audit log registration
                AuditLogger.log_register(
                    user_id=user.id,
                    username=user.username,
                    email=user.email
                )
                login_user(user)
                flash('Account created successfully! Welcome to NikNotes!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Error creating account. Please try again.', 'error')
                
        except ValidationError as e:
            # Extract and display validation errors
            for error in e.errors():
                field = error['loc'][0] if error['loc'] else 'input'
                message = error['msg']
                flash(f'{field.capitalize()}: {message}', 'error')
            return render_template('register.html')
            return redirect(url_for('index'))
        else:
            flash('Error creating account. Please try again.', 'error')
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        from src.database.repository import UserRepository
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        # Get user
        user = UserRepository.get_by_username(username)
        
        if user and user.check_password(password):
            # Update last login
            UserRepository.update_last_login(user.id)
            # Audit log successful login
            AuditLogger.log_login_success(
                user_id=user.id,
                username=user.username,
                remember=remember
            )
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to next page or index
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            # Audit log failed login
            AuditLogger.log_login_failed(
                username=username,
                reason='Invalid username or password'
            )
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout"""
    # Audit log logout
    AuditLogger.log_logout(
        user_id=current_user.id,
        username=current_user.username
    )
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Home page - list all trips and templates"""
    all_trips = trip_service.list_trips(user_id=current_user.id)
    trips = [t for t in all_trips if not t.is_template]
    templates = [t for t in all_trips if t.is_template]
    return render_template('index.html', trips=trips, templates=templates)


@app.route('/trip/new', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")
def new_trip():
    """Create a new trip"""
    if request.method == 'POST':
        data = request.form
        
        # Sanitize trip data
        sanitized_destination = ContentSanitizer.sanitize_strict(data.get('destination', ''))
        sanitized_notes = ContentSanitizer.sanitize_rich(data.get('special_notes', ''))
        
        # Sanitize travelers list
        raw_travelers = request.form.getlist('travelers')
        sanitized_travelers = [
            ContentSanitizer.sanitize_strict(traveler)
            for traveler in raw_travelers if traveler
        ]
        
        # Sanitize activities
        raw_activities = data.get('activities', '').split(',') if data.get('activities') else []
        sanitized_activities = [
            ContentSanitizer.sanitize_standard(activity.strip())
            for activity in raw_activities if activity.strip()
        ]
        
        trip = trip_service.create_trip(
            destination=sanitized_destination,
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            travelers=sanitized_travelers,
            user_id=current_user.id,
            travel_style=data.get('travel_style', 'leisure'),
            transportation=data.get('transportation', 'flight'),
            activities=sanitized_activities,
            special_notes=sanitized_notes
        )
        
        # Generate AI suggestions only if requested
        use_ai = data.get('use_ai_suggestions') == 'on'
        if use_ai:
            suggestions = packing_service.generate_suggestions(trip)
            
            # Persist weather data if it was fetched
            if trip.weather_conditions:
                trip_service.update_trip(trip.id, weather_conditions=trip.weather_conditions)
            
            # Create packing items from suggestions
            for suggestion in suggestions:
                # Parse quantity and item name
                quantity, item_name = _parse_quantity_and_name(suggestion)
                # Try to categorize the item
                category = _categorize_item(item_name)
                packing_service.create_item(
                    trip_id=trip.id,
                    name=item_name,
                    category=category,
                    quantity=quantity,
                    ai_suggested=True
                )
        
        # Audit log trip creation
        AuditLogger.log_trip_create(
            trip_id=trip.id,
            destination=trip.destination,
            user_id=current_user.id,
            username=current_user.username
        )
        
        return redirect(url_for('view_trip', trip_id=trip.id))
    
    # GET request - show form
    travel_styles = [style.value for style in TravelStyle]
    transport_methods = [method.value for method in TransportMethod]
    
    return render_template(
        'new_trip.html',
        travel_styles=travel_styles,
        transport_methods=transport_methods
    )


@app.route('/trip/<trip_id>')
@login_required
def view_trip(trip_id):
    """View trip details and packing list"""
    trip = trip_service.get_trip(trip_id, user_id=current_user.id)
    if not trip:
        flash('Trip not found or you do not have permission to view it', 'error')
        return redirect(url_for('index'))
    
    items = packing_service.get_items_for_trip(trip_id)
    progress = packing_service.get_packing_progress(trip_id)
    
    # Group items by category
    items_by_category = {}
    for item in items:
        category = item.category.value
        if category not in items_by_category:
            items_by_category[category] = []
        items_by_category[category].append(item)
    
    return render_template(
        'view_trip.html',
        trip=trip,
        items=items,
        items_by_category=items_by_category,
        progress=progress
    )


@app.route('/trip/<trip_id>/export-pdf')
@login_required
def export_trip_pdf(trip_id):
    """Export trip packing list as PDF"""
    trip = trip_service.get_trip(trip_id, user_id=current_user.id)
    if not trip:
        flash('Trip not found or access denied', 'error')
        return redirect(url_for('index'))
    
    items = packing_service.get_items_for_trip(trip_id)
    progress = packing_service.get_packing_progress(trip_id)
    
    # Generate PDF
    pdf_buffer = PDFService.generate_packing_list_pdf(trip, items, progress)
    
    # Audit log PDF export
    AuditLogger.log_pdf_export(
        trip_id=trip_id,
        destination=trip.destination,
        user_id=current_user.id,
        username=current_user.username
    )
    
    # Create safe filename
    safe_destination = "".join(c for c in trip.destination if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"PackingList_{safe_destination}_{trip.start_date}.pdf"
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@app.route('/trip/<trip_id>/save-as-template', methods=['POST'])
@login_required
def save_as_template(trip_id):
    """Save a trip as a template"""
    # Verify ownership
    trip = trip_service.get_trip(trip_id, user_id=current_user.id)
    if not trip:
        flash('Trip not found or access denied', 'error')
        return redirect(url_for('index'))
    
    template_name = request.form.get('template_name')
    if not template_name:
        flash('Template name required', 'error')
        return redirect(url_for('view_trip', trip_id=trip_id))
    
    # Sanitize template name
    sanitized_template_name = ContentSanitizer.sanitize_basic(template_name)
    
    try:
        trip_service.update_trip(trip_id, is_template=True, template_name=sanitized_template_name)
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error saving template: {e}")
        return f"Error saving template: {str(e)}", 500


@app.route('/trip/from-template/<template_id>', methods=['GET', 'POST'])
@login_required
def create_from_template(template_id):
    """Create a new trip from a template"""
    template = trip_service.get_trip(template_id, user_id=current_user.id)
    if not template or not template.is_template:
        flash('Template not found or access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.form
        raw_travelers = request.form.getlist('travelers')
        
        # Sanitize inputs
        sanitized_destination = ContentSanitizer.sanitize_strict(data.get('destination', ''))
        sanitized_notes = ContentSanitizer.sanitize_rich(data.get('special_notes', ''))
        sanitized_travelers = [
            ContentSanitizer.sanitize_strict(traveler)
            for traveler in raw_travelers if traveler
        ]
        
        # Create new trip with template data but new dates
        new_trip = trip_service.create_trip(
            destination=sanitized_destination,
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            travelers=sanitized_travelers,
            user_id=current_user.id,
            travel_style=template.travel_style.value,
            transportation=template.transportation.value,
            activities=template.activities,
            special_notes=sanitized_notes
        )
        
        # Copy packing items from template
        template_items = packing_service.get_items_for_trip(template_id)
        for item in template_items:
            packing_service.create_item(
                trip_id=new_trip.id,
                name=item.name,
                category=item.category.value,
                quantity=item.quantity,
                is_essential=item.is_essential,
                notes=item.notes
            )
        
        return redirect(url_for('view_trip', trip_id=new_trip.id))
    
    # GET: show form pre-filled with template data
    travel_styles = [style.value for style in TravelStyle]
    transport_methods = [method.value for method in TransportMethod]
    
    return render_template('new_trip_from_template.html', 
                         template=template,
                         travel_styles=travel_styles,
                         transport_methods=transport_methods)


@app.route('/trip/<trip_id>/delete', methods=['POST'])
@login_required
@limiter.limit("20 per hour")
def delete_trip(trip_id):
    """Delete a trip"""
    try:
        # Get trip details before deletion for audit log
        trip = trip_service.get_trip(trip_id, user_id=current_user.id)
        if not trip:
            return "Trip not found", 404
        
        destination = trip.destination
        success = trip_service.delete_trip(trip_id)
        
        if success:
            # Audit log trip deletion
            AuditLogger.log_trip_delete(
                trip_id=trip_id,
                destination=destination,
                user_id=current_user.id,
                username=current_user.username
            )
            return redirect(url_for('index'))
        else:
            return "Trip not found", 404
    except Exception as e:
        print(f"Error deleting trip: {e}")
        return f"Error deleting trip: {str(e)}", 500


@app.route('/api/item/<item_id>/toggle', methods=['POST'])
@login_required
@limiter.limit("100 per hour")
def toggle_item(item_id):
    """Toggle item packed status"""
    data = request.json
    is_packed = data.get('is_packed', False)
    
    item = packing_service.mark_item_packed(item_id, is_packed)
    
    if item:
        return jsonify({
            'success': True,
            'item_id': item_id,
            'is_packed': item.is_packed
        })
    
    return jsonify({'success': False, 'error': 'Item not found'}), 404


@app.route('/api/trip/<trip_id>/item', methods=['POST'])
@login_required
@limiter.limit("50 per hour")
def add_item(trip_id):
    """Add a new item to the packing list"""
    data = request.json
    
    # Sanitize item data
    sanitized_name = ContentSanitizer.sanitize_strict(data.get('name', ''))
    sanitized_notes = ContentSanitizer.sanitize_rich(data.get('notes', ''))
    
    item = packing_service.create_item(
        trip_id=trip_id,
        name=sanitized_name,
        category=data.get('category', 'other'),
        quantity=data.get('quantity', 1),
        is_essential=data.get('is_essential', False),
        notes=sanitized_notes
    )
    
    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'name': item.name,
            'category': item.category.value,
            'quantity': item.quantity,
            'is_packed': item.is_packed,
            'is_essential': item.is_essential,
            'notes': item.notes
        }
    })


@app.route('/api/item/<item_id>', methods=['DELETE'])
@login_required
@limiter.limit("100 per hour")
def delete_item(item_id):
    """Delete a packing item"""
    success = packing_service.delete_item(item_id)
    
    if success:
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Item not found'}), 404


@app.route('/api/trip/<trip_id>/reorder-items', methods=['POST'])
def reorder_items(trip_id):
    """Update the display order of packing items"""
    data = request.json
    items = data.get('items', [])
    
    # Update each item's display_order
    from src.database.repository import PackingItemRepository
    for item_data in items:
        PackingItemRepository.update(item_data['id'], display_order=item_data['order'])
    
    return jsonify({'success': True})


@app.route('/api/trip/<trip_id>/regenerate', methods=['POST'])
@login_required
def regenerate_suggestions(trip_id):
    """Regenerate AI suggestions for a trip"""
    # Verify ownership
    trip = trip_service.get_trip(trip_id, user_id=current_user.id)
    if not trip:
        return jsonify({'error': 'Access denied'}), 403
    trip = trip_service.get_trip(trip_id)
    if not trip:
        return jsonify({'success': False, 'error': 'Trip not found'}), 404
    
    # Generate AI suggestions (may update trip.weather_conditions)
    suggestions = packing_service.generate_suggestions(trip)
    
    # Persist weather data if it was fetched
    if trip.weather_conditions:
        trip_service.update_trip(trip_id, weather_conditions=trip.weather_conditions)
    
    # Convert suggestions to packing items and save them
    created_items = []
    for suggestion in suggestions:
        # Parse quantity and item name
        quantity, item_name = _parse_quantity_and_name(suggestion)
        
        # Categorize and create item
        category = _categorize_item(item_name)
        item = packing_service.create_item(
            trip_id=trip_id,
            name=item_name,
            category=category,
            quantity=quantity,
            is_essential=False,
            ai_suggested=True,
            notes=None
        )
        created_items.append({
            'id': item.id,
            'name': item.name,
            'category': item.category.value,
            'quantity': item.quantity,
            'ai_suggested': item.ai_suggested,
            'is_essential': item.is_essential
        })
    
    return jsonify({
        'success': True,
        'suggestions': created_items,
        'count': len(created_items)
    })


def _parse_quantity_and_name(suggestion: str) -> tuple:
    """Parse quantity and item name from AI suggestion
    
    Expected format: 'QUANTITY x ITEM_NAME'
    Examples: '5 x Pairs of socks', '1 x Toothpaste'
    
    Returns: (quantity: int, item_name: str)
    """
    import re
    
    # Try to match pattern: "NUMBER x ITEM"
    match = re.match(r'^(\d+)\s*x\s*(.+)$', suggestion.strip(), re.IGNORECASE)
    if match:
        quantity = int(match.group(1))
        item_name = match.group(2).strip()
        return (quantity, item_name)
    
    # Fallback: no quantity specified, default to 1
    return (1, suggestion.strip())


def _categorize_item(item_name: str) -> str:
    """Simple categorization of items based on keywords"""
    item_lower = item_name.lower()
    
    if any(word in item_lower for word in ['shirt', 'pants', 'dress', 'shoes', 'socks', 'jacket', 'coat', 'hat']):
        return 'clothing'
    elif any(word in item_lower for word in ['toothbrush', 'shampoo', 'soap', 'deodorant', 'toiletries']):
        return 'toiletries'
    elif any(word in item_lower for word in ['phone', 'charger', 'laptop', 'camera', 'headphones', 'adapter']):
        return 'electronics'
    elif any(word in item_lower for word in ['passport', 'visa', 'ticket', 'id', 'license', 'document']):
        return 'documents'
    elif any(word in item_lower for word in ['medicine', 'medication', 'first aid', 'bandage', 'pills']):
        return 'medical'
    elif any(word in item_lower for word in ['book', 'game', 'kindle', 'entertainment']):
        return 'entertainment'
    elif any(word in item_lower for word in ['backpack', 'luggage', 'bag', 'tent', 'sleeping']):
        return 'gear'
    else:
        return 'other'


# Health check endpoint for container orchestration
@app.route('/health')
@limiter.exempt  # Health checks shouldn't be rate limited
@csrf.exempt  # Health checks shouldn't require CSRF tokens
def health_check():
    """
    Health check endpoint for Docker/Kubernetes.
    Returns 200 OK if the application is running and healthy.
    Checks database connectivity and essential services.
    """
    try:
        # Check database connectivity
        from src.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        
        # Check if the app is properly configured
        if not app.config.get('SECRET_KEY'):
            return jsonify({
                'status': 'unhealthy',
                'error': 'Missing SECRET_KEY configuration'
            }), 503
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'services': {
                'database': 'ok',
                'flask': 'ok'
            }
        }), 200
    except Exception as e:
        # Return 503 Service Unavailable if unhealthy
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


# CSP Violation Reporting endpoint
@app.route('/csp-report', methods=['POST'])
@limiter.exempt  # CSP reports shouldn't be rate limited (could block security monitoring)
@csrf.exempt  # CSP reports are from browser, no CSRF token
def csp_report():
    """
    Content Security Policy violation reporting endpoint.
    Receives and logs CSP violations from browsers for security monitoring.
    
    CSP violations indicate potential XSS attacks or misconfigured policies.
    This endpoint helps identify and respond to security threats.
    """
    try:
        # Get the CSP violation report from the request
        report = request.get_json(force=True, silent=True)
        
        if not report:
            # Browser sent invalid JSON or empty report
            return '', 204  # No content, but acknowledge receipt
        
        # Extract violation details
        csp_report = report.get('csp-report', {})
        
        # Log the violation with important details
        violation_details = {
            'timestamp': datetime.utcnow().isoformat(),
            'document_uri': csp_report.get('document-uri', 'unknown'),
            'violated_directive': csp_report.get('violated-directive', 'unknown'),
            'effective_directive': csp_report.get('effective-directive', 'unknown'),
            'blocked_uri': csp_report.get('blocked-uri', 'unknown'),
            'source_file': csp_report.get('source-file', 'unknown'),
            'line_number': csp_report.get('line-number', 'unknown'),
            'column_number': csp_report.get('column-number', 'unknown'),
            'status_code': csp_report.get('status-code', 'unknown'),
            'referrer': csp_report.get('referrer', 'unknown'),
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'ip_address': get_remote_address(),
        }
        
        # Log to application logger (configure logging for production)
        app.logger.warning(
            f"CSP Violation Detected: {violation_details['violated_directive']} | "
            f"Blocked: {violation_details['blocked_uri']} | "
            f"Page: {violation_details['document_uri']} | "
            f"Source: {violation_details['source_file']}:{violation_details['line_number']} | "
            f"IP: {violation_details['ip_address']}"
        )
        
        # In production, you might want to:
        # 1. Store violations in database for analysis
        # 2. Send alerts for suspicious patterns
        # 3. Generate security reports
        # 4. Integrate with SIEM systems
        
        # Example: Store in database (uncomment if needed)
        # from src.database import db_session
        # from src.models import CSPViolation
        # violation = CSPViolation(**violation_details)
        # db_session.add(violation)
        # db_session.commit()
        
        # Example: Alert on repeated violations (uncomment if needed)
        # if is_suspicious_pattern(violation_details):
        #     send_security_alert(violation_details)
        
        return '', 204  # No content response (browser doesn't need feedback)
        
    except Exception as e:
        # Log the error but don't fail (CSP reporting is non-critical)
        app.logger.error(f"Error processing CSP report: {e}")
        return '', 204  # Still return success to avoid browser retries


# Error handlers for custom error pages
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors with custom page"""
    return render_template('errors/404.html'), 404


@app.errorhandler(429)
def ratelimit_error(error):
    """Handle rate limit errors with custom page"""
    # Extract retry_after from error description if available
    retry_after = getattr(error, 'description', None)
    return render_template('errors/429.html', retry_after=retry_after), 429


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with custom page"""
    # Log the error for debugging
    print(f"Internal error: {error}")
    return render_template('errors/500.html'), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle uncaught exceptions in production"""
    # Log the error
    print(f"Unhandled exception: {error}")
    
    # In production, show generic error page
    # In development, let Flask show the detailed traceback
    if app.debug:
        raise error
    else:
        return render_template('errors/500.html'), 500


if __name__ == '__main__':
    # Bind to 0.0.0.0 to make the app accessible on all network interfaces
    # This allows access from other devices on your network
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', debug=debug_mode, port=5000)
