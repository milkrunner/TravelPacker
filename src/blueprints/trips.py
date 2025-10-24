"""
Trips blueprint - Trip management routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from src.services.sanitization_service import ContentSanitizer
from src.models.trip import TravelStyle, TransportMethod


trips_bp = Blueprint('trips', __name__)

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


@trips_bp.route('/new', methods=['GET', 'POST'])
@login_required
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
        
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        if not start_date or not end_date:
            flash('Start date and end date are required', 'error')
            return redirect(url_for('trips.new_trip'))
        
        trip = trip_service.create_trip(
            destination=sanitized_destination,
            start_date=start_date,
            end_date=end_date,
            travelers=sanitized_travelers,
            user_id=current_user.id,
            travel_style=data.get('travel_style', 'leisure'),
            transportation=data.get('transportation', 'flight'),
            activities=sanitized_activities,
            special_notes=sanitized_notes
        )
        
        # Generate AI suggestions only if requested
        use_ai = data.get('use_ai_suggestions') == 'on'
        if use_ai and trip.id:
            suggestions = packing_service.generate_suggestions(trip)
            
            # Persist weather data if it was fetched
            if trip.weather_conditions:
                trip_service.update_trip(trip.id, weather_conditions=trip.weather_conditions)
            
            # Create packing items from suggestions
            for suggestion in suggestions:
                quantity, item_name = _parse_quantity_and_name(suggestion)
                category = _categorize_item(item_name)
                packing_service.create_item(
                    trip_id=trip.id,
                    name=item_name,
                    category=category,
                    quantity=quantity,
                    ai_suggested=True
                )
        
        return redirect(url_for('trips.view_trip', trip_id=trip.id))
    
    # GET request - show form
    travel_styles = [style.value for style in TravelStyle]
    transport_methods = [method.value for method in TransportMethod]
    
    return render_template(
        'new_trip.html',
        travel_styles=travel_styles,
        transport_methods=transport_methods
    )


@trips_bp.route('/<trip_id>')
def view_trip(trip_id):
    """View trip details and packing list"""
    trip = trip_service.get_trip(trip_id)
    if not trip:
        flash('Trip not found', 'error')
        return redirect(url_for('main.index'))
    
    items = packing_service.get_items_for_trip(trip_id)
    progress = packing_service.get_packing_progress(trip_id)
    
    # Group items by category
    items_by_category = {}
    for item in items:
        category = item.category.value
        if category not in items_by_category:
            items_by_category[category] = []
        items_by_category[category].append(item)
    
    # Format dates for display
    from datetime import datetime
    start_date_formatted = datetime.strptime(trip.start_date, '%Y-%m-%d').strftime('%B %d')
    end_date_formatted = datetime.strptime(trip.end_date, '%Y-%m-%d').strftime('%B %d, %Y')
    
    return render_template(
        'view_trip.html',
        trip=trip,
        items=items,
        items_by_category=items_by_category,
        progress=progress,
        start_date_formatted=start_date_formatted,
        end_date_formatted=end_date_formatted
    )


@trips_bp.route('/<trip_id>/export-pdf')
def export_trip_pdf(trip_id):
    """Export trip packing list as PDF"""
    from src.services.pdf_service import PDFService
    
    trip = trip_service.get_trip(trip_id)
    if not trip:
        flash('Trip not found or access denied', 'error')
        return redirect(url_for('main.index'))
    
    items = packing_service.get_items_for_trip(trip_id)
    progress = packing_service.get_packing_progress(trip_id)
    
    # Generate PDF
    pdf_buffer = PDFService.generate_packing_list_pdf(trip, items, progress)
    
    # Create safe filename
    safe_destination = "".join(c for c in trip.destination if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"PackingList_{safe_destination}_{trip.start_date}.pdf"
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@trips_bp.route('/<trip_id>/save-as-template', methods=['POST'])
@login_required
def save_as_template(trip_id):
    """Save a trip as a template"""
    trip = trip_service.get_trip(trip_id)
    if not trip:
        flash('Trip not found or access denied', 'error')
        return redirect(url_for('main.index'))
    
    template_name = request.form.get('template_name')
    if not template_name:
        flash('Template name required', 'error')
        return redirect(url_for('trips.view_trip', trip_id=trip_id))
    
    # Sanitize template name
    sanitized_template_name = ContentSanitizer.sanitize_basic(template_name)
    
    try:
        trip_service.update_trip(trip_id, is_template=True, template_name=sanitized_template_name)
        return redirect(url_for('main.index'))
    except Exception as e:
        print(f"Error saving template: {e}")
        return f"Error saving template: {str(e)}", 500


@trips_bp.route('/from-template/<template_id>', methods=['GET', 'POST'])
@login_required
def create_from_template(template_id):
    """Create a new trip from a template"""
    template = trip_service.get_trip(template_id)
    if not template or not template.is_template:
        flash('Template not found or access denied', 'error')
        return redirect(url_for('main.index'))
    
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
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        if not start_date or not end_date:
            flash('Start date and end date are required', 'error')
            return redirect(url_for('trips.create_from_template', template_id=template_id))
        
        new_trip = trip_service.create_trip(
            destination=sanitized_destination,
            start_date=start_date,
            end_date=end_date,
            travelers=sanitized_travelers,
            user_id=current_user.id,
            travel_style=template.travel_style.value,
            transportation=template.transportation.value,
            activities=template.activities,
            special_notes=sanitized_notes
        )
        
        # Copy packing items from template
        if new_trip.id:
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
        
        return redirect(url_for('trips.view_trip', trip_id=new_trip.id))
    
    # GET: show form pre-filled with template data
    travel_styles = [style.value for style in TravelStyle]
    transport_methods = [method.value for method in TransportMethod]
    
    return render_template('new_trip_from_template.html', 
                         template=template,
                         travel_styles=travel_styles,
                         transport_methods=transport_methods)


@trips_bp.route('/<trip_id>/delete', methods=['POST'])
@login_required
def delete_trip(trip_id):
    """Delete a trip"""
    try:
        success = trip_service.delete_trip(trip_id)
        
        if success:
            return redirect(url_for('main.index'))
        else:
            return "Trip not found", 404
    except Exception as e:
        print(f"Error deleting trip: {e}")
        return f"Error deleting trip: {str(e)}", 500
