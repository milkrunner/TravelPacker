"""
Packing list management service
"""

from src.database.repository import PackingItemRepository
from src.models.packing_item import ItemCategory, PackingItem
from src.models.trip import Trip
from src.services.ai_service import AIService


class PackingListService:
    """Service for managing packing lists"""

    def __init__(self, ai_service: AIService, use_database: bool = True):
        self.ai_service = ai_service
        self.use_database = use_database
        self.items = {}  # In-memory fallback

    def generate_suggestions(self, trip: Trip) -> list[str]:
        """Generate AI-powered packing suggestions"""
        return self.ai_service.generate_packing_suggestions(trip)

    def create_item(
        self,
        trip_id: str,
        name: str,
        category: str,
        quantity: int = 1,
        is_essential: bool = False,
        ai_suggested: bool = False,
        notes: str | None = None,
    ) -> PackingItem:
        """Create a packing item"""
        item = PackingItem(
            trip_id=trip_id,
            name=name,
            category=ItemCategory(category),
            quantity=quantity,
            is_essential=is_essential,
            ai_suggested=ai_suggested,
            notes=notes,
        )

        if self.use_database:
            return PackingItemRepository.create(item)
        else:
            # In-memory fallback
            item_id = f"item_{len(self.items) + 1}"
            item.id = item_id
            self.items[item_id] = item
            return item

    def get_items_for_trip(self, trip_id: str) -> list[PackingItem]:
        """Get all packing items for a trip"""
        if self.use_database:
            return PackingItemRepository.get_by_trip(trip_id)
        else:
            return [item for item in self.items.values() if item.trip_id == trip_id]

    def mark_item_packed(self, item_id: str, is_packed: bool = True) -> PackingItem | None:
        """Mark an item as packed or unpacked"""
        if self.use_database:
            return PackingItemRepository.update(item_id, is_packed=is_packed)
        else:
            item = self.items.get(item_id)
            if item:
                item.is_packed = is_packed
            return item

    def update_item(self, item_id: str, **kwargs) -> PackingItem | None:
        """Update a packing item with arbitrary fields"""
        if self.use_database:
            return PackingItemRepository.update(item_id, **kwargs)
        else:
            item = self.items.get(item_id)
            if item:
                for key, value in kwargs.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
            return item

    def delete_item(self, item_id: str) -> bool:
        """Delete a packing item"""
        if self.use_database:
            return PackingItemRepository.delete(item_id)
        else:
            if item_id in self.items:
                del self.items[item_id]
                return True
            return False

    def get_packing_progress(self, trip_id: str) -> dict:
        """Get packing progress statistics"""
        items = self.get_items_for_trip(trip_id)
        total = len(items)
        packed = sum(1 for item in items if item.is_packed)

        return {
            "total_items": total,
            "packed_items": packed,
            "unpacked_items": total - packed,
            "completion_percentage": (packed / total * 100) if total > 0 else 0,
        }
