"""
API blueprint - RESTful API routes for AJAX operations
"""

from flask import Blueprint, jsonify, request
from src.services.sanitization_service import ContentSanitizer
from src.extensions import csrf


api_bp = Blueprint('api', __name__)

# Services will be initialized in factory
trip_service = None
packing_service = None


def init_services(service_container):
    """Initialize blueprint with services"""
    global trip_service, packing_service
    trip_service = service_container['trip_service']
    packing_service = service_container['packing_service']


def _parse_quantity_and_name(suggestion: str) -> tuple:
    """Parse quantity and item name from AI suggestion"""
    import re
    
    match = re.match(r'^(\d+)\s*x\s*(.+)$', suggestion.strip(), re.IGNORECASE)
    if match:
        quantity = int(match.group(1))
        item_name = match.group(2).strip()
        return (quantity, item_name)
    
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


@api_bp.route('/item/<item_id>/toggle', methods=['POST'])
def toggle_item(item_id):
    """Toggle item packed status"""
    data = request.get_json() or {}
    is_packed = data.get('is_packed', False)
    
    item = packing_service.mark_item_packed(item_id, is_packed)
    
    if item:
        return jsonify({
            'success': True,
            'item_id': item_id,
            'is_packed': item.is_packed
        })
    
    return jsonify({'success': False, 'error': 'Item not found'}), 404


@api_bp.route('/trip/<trip_id>/item', methods=['POST'])
def add_item(trip_id):
    """Add a new item to the packing list"""
    data = request.get_json() or {}
    
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


@api_bp.route('/item/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete a packing item"""
    from src.utils.security_utils import check_security_threats, get_ip_address
    from flask_login import current_user
    
    # Check for security threats
    threat_response = check_security_threats()
    if threat_response:
        return threat_response
    
    # Log sensitive operation
    ip = get_ip_address()
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'
    print(f"🗑️  DELETE operation: item={item_id} by user={user_id} from {ip}")
    
    success = packing_service.delete_item(item_id)
    
    if success:
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Item not found'}), 404


@api_bp.route('/trip/<trip_id>/reorder-items', methods=['POST'])
def reorder_items(trip_id):
    """Update the display order of packing items"""
    data = request.get_json() or {}
    items = data.get('items', [])
    
    # Update each item's display_order
    from src.database.repository import PackingItemRepository
    for item_data in items:
        PackingItemRepository.update(item_data['id'], display_order=item_data['order'])
    
    return jsonify({'success': True})


@api_bp.route('/trip/<trip_id>/regenerate', methods=['POST'])
def regenerate_suggestions(trip_id):
    """Regenerate AI suggestions for a trip (expensive AI operation)"""
    from src.utils.security_utils import check_security_threats, get_ip_address
    from flask_login import current_user
    
    # Check for security threats
    threat_response = check_security_threats()
    if threat_response:
        return threat_response
    
    # Log expensive operation
    ip = get_ip_address()
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'
    print(f"🤖 REGENERATE AI: trip={trip_id} by user={user_id} from {ip}")
    
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
        quantity, item_name = _parse_quantity_and_name(suggestion)
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


@api_bp.route('/log-client-error', methods=['POST'])
@csrf.exempt  # Client-side error logging shouldn't require CSRF token
def log_client_error():
    """Log client-side errors for diagnostics"""
    try:
        data = request.get_json() or {}
        
        # Sanitize error data to prevent log injection
        context = ContentSanitizer.sanitize_strict(data.get('context', 'unknown'))
        error_msg = ContentSanitizer.sanitize_strict(str(data.get('error', 'unknown')))
        
        # Log the client error
        print(f"⚠️  Client Error - Context: {context}, Error: {error_msg}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error logging client error: {e}")
        return jsonify({'success': False}), 500
