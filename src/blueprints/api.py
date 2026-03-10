"""
API blueprint - RESTful API routes for AJAX operations
"""

from flask import Blueprint, jsonify, request

from src.extensions import csrf
from src.services.sanitization_service import ContentSanitizer

api_bp = Blueprint("api", __name__)

# Services will be initialized in factory
trip_service = None
packing_service = None


def init_services(service_container):
    """Initialize blueprint with services"""
    global trip_service, packing_service
    trip_service = service_container["trip_service"]
    packing_service = service_container["packing_service"]


def _parse_quantity_and_name(suggestion: str) -> tuple:
    """Parse quantity and item name from AI suggestion"""
    import re

    match = re.match(r"^(\d+)\s*x\s*(.+)$", suggestion.strip(), re.IGNORECASE)
    if match:
        quantity = int(match.group(1))
        item_name = match.group(2).strip()
        return (quantity, item_name)

    return (1, suggestion.strip())


def _categorize_item(item_name: str) -> str:
    """Simple categorization of items based on keywords"""
    item_lower = item_name.lower()

    if any(word in item_lower for word in ["shirt", "pants", "dress", "shoes", "socks", "jacket", "coat", "hat"]):
        return "clothing"
    elif any(word in item_lower for word in ["toothbrush", "shampoo", "soap", "deodorant", "toiletries"]):
        return "toiletries"
    elif any(word in item_lower for word in ["phone", "charger", "laptop", "camera", "headphones", "adapter"]):
        return "electronics"
    elif any(word in item_lower for word in ["passport", "visa", "ticket", "id", "license", "document"]):
        return "documents"
    elif any(word in item_lower for word in ["medicine", "medication", "first aid", "bandage", "pills"]):
        return "medical"
    elif any(word in item_lower for word in ["book", "game", "kindle", "entertainment"]):
        return "entertainment"
    elif any(word in item_lower for word in ["backpack", "luggage", "bag", "tent", "sleeping"]):
        return "gear"
    else:
        return "other"


@api_bp.route("/item/<item_id>/toggle", methods=["POST"])
def toggle_item(item_id):
    """Toggle item packed status"""
    data = request.get_json() or {}
    is_packed = data.get("is_packed", False)

    item = packing_service.mark_item_packed(item_id, is_packed)

    if item:
        return jsonify({"success": True, "item_id": item_id, "is_packed": item.is_packed})

    return jsonify({"success": False, "error": "Item not found"}), 404


@api_bp.route("/trip/<trip_id>/item", methods=["POST"])
def add_item(trip_id):
    """Add a new item to the packing list"""
    data = request.get_json() or {}

    # Sanitize item data
    sanitized_name = ContentSanitizer.sanitize_strict(data.get("name", ""))
    sanitized_notes = ContentSanitizer.sanitize_rich(data.get("notes", ""))

    item = packing_service.create_item(
        trip_id=trip_id,
        name=sanitized_name,
        category=data.get("category", "other"),
        quantity=data.get("quantity", 1),
        is_essential=data.get("is_essential", False),
        notes=sanitized_notes,
    )

    return jsonify(
        {
            "success": True,
            "item": {
                "id": item.id,
                "name": item.name,
                "category": item.category.value,
                "quantity": item.quantity,
                "is_packed": item.is_packed,
                "is_essential": item.is_essential,
                "notes": item.notes,
            },
        }
    )


@api_bp.route("/item/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete a packing item"""

    from src.utils.security_utils import check_security_threats, get_ip_address

    # Check for security threats
    threat_response = check_security_threats()
    if threat_response:
        return threat_response

    # Log sensitive operation
    get_ip_address()

    success = packing_service.delete_item(item_id)

    if success:
        return jsonify({"success": True})

    return jsonify({"success": False, "error": "Item not found"}), 404


@api_bp.route("/trip/<trip_id>/reorder-items", methods=["POST"])
def reorder_items(trip_id):
    """Update the display order of packing items"""
    data = request.get_json() or {}
    items = data.get("items", [])

    # Update each item's display_order
    from src.database.repository import PackingItemRepository

    for item_data in items:
        PackingItemRepository.update(item_data["id"], display_order=item_data["order"])

    return jsonify({"success": True})


@api_bp.route("/trip/<trip_id>/regenerate", methods=["POST"])
def regenerate_suggestions(trip_id):
    """Regenerate AI suggestions for a trip (expensive AI operation)"""

    from src.utils.security_utils import check_security_threats, get_ip_address

    # Check for security threats
    threat_response = check_security_threats()
    if threat_response:
        return threat_response

    # Log expensive operation
    get_ip_address()

    trip = trip_service.get_trip(trip_id)
    if not trip:
        return jsonify({"success": False, "error": "Trip not found"}), 404

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
            notes=None,
        )
        created_items.append(
            {
                "id": item.id,
                "name": item.name,
                "category": item.category.value,
                "quantity": item.quantity,
                "ai_suggested": item.ai_suggested,
                "is_essential": item.is_essential,
            }
        )

    return jsonify({"success": True, "suggestions": created_items, "count": len(created_items)})


@api_bp.route("/item/<item_id>/review", methods=["POST"])
def review_item(item_id):
    """Mark whether an item was actually used after the trip"""
    data = request.get_json() or {}
    actually_used = data.get("actually_used")

    if actually_used is None:
        return jsonify({"success": False, "error": "actually_used is required"}), 400

    item = packing_service.update_item(item_id, actually_used=bool(actually_used))

    if item:
        return jsonify({"success": True, "item_id": item_id, "actually_used": item.actually_used})

    return jsonify({"success": False, "error": "Item not found"}), 404


@api_bp.route("/trip/<trip_id>/review", methods=["POST"])
def review_trip_items(trip_id):
    """Batch review: mark multiple items as used/unused after a trip"""
    data = request.get_json() or {}
    reviews = data.get("reviews", [])

    if not reviews:
        return jsonify({"success": False, "error": "No reviews provided"}), 400

    updated = []
    for review in reviews:
        item_id = review.get("item_id")
        actually_used = review.get("actually_used")
        if item_id is not None and actually_used is not None:
            item = packing_service.update_item(item_id, actually_used=bool(actually_used))
            if item:
                updated.append(item_id)

    return jsonify({"success": True, "updated_count": len(updated)})


@api_bp.route("/history", methods=["GET"])
def packing_history():
    """Get packing history for the current user - items reviewed after trips"""
    from flask_login import current_user

    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    from src.database.repository import PackingItemRepository

    history = PackingItemRepository.get_history(current_user.id)

    # Aggregate: count how often each item was used vs not used
    item_stats = {}
    for entry in history:
        name = entry["name"].lower()
        if name not in item_stats:
            item_stats[name] = {"name": entry["name"], "category": entry["category"], "used": 0, "not_used": 0}
        if entry["actually_used"]:
            item_stats[name]["used"] += 1
        else:
            item_stats[name]["not_used"] += 1

    # Sort by most frequently used
    stats_list = sorted(item_stats.values(), key=lambda x: x["used"], reverse=True)

    return jsonify({"success": True, "history": stats_list})


@api_bp.route("/log-client-error", methods=["POST"])
@csrf.exempt  # Client-side error logging shouldn't require CSRF token
def log_client_error():
    """Log client-side errors for diagnostics"""
    try:
        data = request.get_json() or {}

        # Sanitize error data to prevent log injection
        ContentSanitizer.sanitize_strict(data.get("context", "unknown"))
        ContentSanitizer.sanitize_strict(str(data.get("error", "unknown")))

        # Log the client error

        return jsonify({"success": True}), 200

    except Exception:
        return jsonify({"success": False}), 500
