"""
Traveler model
"""

from enum import StrEnum

from pydantic import BaseModel


class TravelerType(StrEnum):
    """Types of travelers"""

    ADULT = "adult"
    CHILD = "child"
    INFANT = "infant"
    PET = "pet"


class Traveler(BaseModel):
    """Traveler information"""

    id: str | None = None
    name: str
    traveler_type: TravelerType
    age: int | None = None
    special_needs: list[str] = []
    preferences: list[str] = []
