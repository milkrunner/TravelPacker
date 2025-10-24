"""
Authentication blueprint - Login, logout, OAuth routes
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from src.extensions import csrf


auth_bp = Blueprint('auth', __name__)

# OAuth service will be initialized in factory
google_signin_service = None


def init_services(service_container):
    """Initialize blueprint with services"""
    global google_signin_service
    google_signin_service = service_container['google_signin_service']


@auth_bp.route('/login')
def login():
    """Login page with Google Sign-In"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template(
        'login.html', 
        google_signin_enabled=google_signin_service.enabled,
        google_client_id=google_signin_service.client_id if google_signin_service.enabled else None
    )


@auth_bp.route('/google', methods=['POST'])
@csrf.exempt  # Google Sign-In sends POST from client-side; JWT verification provides CSRF protection
def google_signin():
    """Verify Google Sign-In token and log user in"""
    if not google_signin_service.enabled:
        return jsonify({'success': False, 'error': 'Google Sign-In not configured'}), 503
    
    try:
        # Get the credential (JWT token) from the request
        data = request.get_json()
        if not data or 'credential' not in data:
            return jsonify({'success': False, 'error': 'Missing credential'}), 400
        
        credential = data['credential']
        
        # Verify the token with Google
        user_info = google_signin_service.verify_google_token(credential)
        
        if not user_info:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        # Check if email is verified
        if not user_info.get('email_verified', False):
            return jsonify({'success': False, 'error': 'Email not verified with Google'}), 403
        
        # Find or create user in database
        user = google_signin_service.find_or_create_user(user_info)
        
        if not user:
            return jsonify({'success': False, 'error': 'Failed to create user'}), 500
        
        # Log the user in with Flask-Login
        login_user(user, remember=True)
        
        # Return success response
        return jsonify({
            'success': True,
            'redirect': url_for('main.index'),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'profile_picture': user.profile_picture
            }
        }), 200
        
    except Exception as e:
        print(f"Google Sign-In error: {e}")
        return jsonify({'success': False, 'error': 'Authentication error'}), 500


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    user_id = current_user.id
    username = current_user.username
    
    logout_user()
    
    # Log logout for security audit
    print(f'User logout: {username} (ID: {user_id}) from IP: {request.remote_addr}')
    
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))
