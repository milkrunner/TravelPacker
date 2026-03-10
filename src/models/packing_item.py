"""
Packing item model
"""

from enum import StrEnum

from pydantic import BaseModel


class ItemCategory(StrEnum):
    """Categories for packing items"""

    CLOTHING = "clothing"
    TOILETRIES = "toiletries"
    ELECTRONICS = "electronics"
    DOCUMENTS = "documents"
    MEDICAL = "medical"
    ENTERTAINMENT = "entertainment"
    GEAR = "gear"
    FOOD = "food"
    OTHER = "other"


class PackingItem(BaseModel):
    """Individual packing list item"""

    id: str | None = None
    trip_id: str | None = None
    name: str
    category: ItemCategory
    quantity: int = 1
    is_packed: bool = False
    is_essential: bool = False
    notes: str | None = None
    ai_suggested: bool = False
    actually_used: bool | None = None  # None = not reviewed, True = used, False = not used
    display_order: int = 0
