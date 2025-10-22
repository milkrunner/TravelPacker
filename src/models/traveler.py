"""
Traveler model
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel


class TravelerType(str, Enum):
    """Types of travelers"""
    ADULT = "adult"
    CHILD = "child"
    INFANT = "infant"
    PET = "pet"


class Traveler(BaseModel):
    """Traveler information"""
    id: Optional[str] = None
    name: str
    traveler_type: TravelerType
    age: Optional[int] = None
    special_needs: List[str] = []
    preferences: List[str] = []
