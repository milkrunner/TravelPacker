"""
Packing item model
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ItemCategory(str, Enum):
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
    id: Optional[str] = None
    trip_id: Optional[str] = None
    name: str
    category: ItemCategory
    quantity: int = 1
    is_packed: bool = False
    is_essential: bool = False
    notes: Optional[str] = None
    ai_suggested: bool = False
    display_order: int = 0
