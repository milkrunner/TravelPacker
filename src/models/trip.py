"""
Trip model
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TravelStyle(str, Enum):
    """Types of travel styles"""
    BUSINESS = "business"
    LEISURE = "leisure"
    ADVENTURE = "adventure"
    BACKPACKING = "backpacking"
    LUXURY = "luxury"


class TransportMethod(str, Enum):
    """Transportation methods"""
    FLIGHT = "flight"
    ROAD_TRIP = "road_trip"
    TRAIN = "train"
    CRUISE = "cruise"
    OTHER = "other"


class Trip(BaseModel):
    """Trip information model"""
    id: Optional[str] = None
    destination: str
    start_date: str
    end_date: str
    duration: int = Field(default=1)
    travelers: List[str] = Field(default_factory=list)
    travel_style: TravelStyle = TravelStyle.LEISURE
    transportation: TransportMethod = TransportMethod.FLIGHT
    activities: List[str] = Field(default_factory=list)
    special_notes: Optional[str] = None
    weather_conditions: Optional[str] = None
    is_template: bool = False
    template_name: Optional[str] = None
    
    def model_post_init(self, __context):
        """Calculate duration after initialization"""
        if self.start_date and self.end_date:
            start = datetime.fromisoformat(self.start_date)
            end = datetime.fromisoformat(self.end_date)
            self.duration = (end - start).days + 1
    
    @property
    def transport_display(self) -> str:
        """Get friendly display name for transportation"""
        transport_map = {
            TransportMethod.FLIGHT: "✈️ Flight",
            TransportMethod.ROAD_TRIP: "🚗 Road Trip",
            TransportMethod.TRAIN: "🚂 Train",
            TransportMethod.CRUISE: "🚢 Cruise",
            TransportMethod.OTHER: "🚶 Other"
        }
        return transport_map.get(self.transportation, "🚶 Other")
    
    @property
    def travel_style_display(self) -> str:
        """Get friendly display name for travel style"""
        style_map = {
            TravelStyle.BUSINESS: "💼 Business",
            TravelStyle.LEISURE: "🏖️ Leisure",
            TravelStyle.ADVENTURE: "🏔️ Adventure",
            TravelStyle.BACKPACKING: "🎒 Backpacking",
            TravelStyle.LUXURY: "✨ Luxury"
        }
        return style_map.get(self.travel_style, "🌍 Travel")
