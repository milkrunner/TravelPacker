"""
Trip model
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TravelStyle(StrEnum):
    """Types of travel styles"""

    BUSINESS = "business"
    LEISURE = "leisure"
    ADVENTURE = "adventure"
    BACKPACKING = "backpacking"
    LUXURY = "luxury"


class TransportMethod(StrEnum):
    """Transportation methods"""

    FLIGHT = "flight"
    ROAD_TRIP = "road_trip"
    TRAIN = "train"
    CRUISE = "cruise"
    OTHER = "other"


class Trip(BaseModel):
    """Trip information model"""

    id: str | None = None
    destination: str
    start_date: str
    end_date: str
    duration: int = Field(default=1)
    travelers: list[str] = Field(default_factory=list)
    travel_style: TravelStyle = TravelStyle.LEISURE
    transportation: TransportMethod = TransportMethod.FLIGHT
    activities: list[str] = Field(default_factory=list)
    special_notes: str | None = None
    weather_conditions: str | None = None
    is_template: bool = False
    template_name: str | None = None

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
            TransportMethod.OTHER: "🚶 Other",
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
            TravelStyle.LUXURY: "✨ Luxury",
        }
        return style_map.get(self.travel_style, "🌍 Travel")
