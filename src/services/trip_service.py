"""
Trip management service
"""

from typing import List, Optional
from src.models.trip import Trip, TravelStyle, TransportMethod
from src.database.repository import TripRepository


class TripService:
    """Service for managing trips"""
    
    def __init__(self, use_database: bool = True):
        self.use_database = use_database
        self.trips = {}  # In-memory fallback
    
    def create_trip(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        travelers: List[str],
        user_id: str,
        travel_style: str = "leisure",
        transportation: str = "flight",
        activities: Optional[List[str]] = None,
        special_notes: Optional[str] = None
    ) -> Trip:
        """Create a new trip"""
        trip = Trip(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            travelers=travelers,
            travel_style=TravelStyle(travel_style),
            transportation=TransportMethod(transportation),
            activities=activities or [],
            special_notes=special_notes
        )
        
        if self.use_database:
            return TripRepository.create(trip, user_id)
        else:
            # In-memory fallback
            trip_id = f"trip_{len(self.trips) + 1}"
            trip.id = trip_id
            self.trips[trip_id] = trip
            return trip
    
    def get_trip(self, trip_id: str, user_id: Optional[str] = None) -> Optional[Trip]:
        """Get a trip by ID, optionally verify ownership"""
        if self.use_database:
            return TripRepository.get(trip_id, user_id)
        else:
            return self.trips.get(trip_id)
    
    def list_trips(self, user_id: Optional[str] = None) -> List[Trip]:
        """List all trips, optionally filtered by user"""
        if self.use_database:
            return TripRepository.list_all(user_id)
        else:
            return list(self.trips.values())
    
    def update_trip(self, trip_id: str, **kwargs) -> Optional[Trip]:
        """Update trip details"""
        if self.use_database:
            return TripRepository.update(trip_id, **kwargs)
        else:
            trip = self.trips.get(trip_id)
            if not trip:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(trip, key):
                    setattr(trip, key, value)
            
            return trip
    
    def delete_trip(self, trip_id: str) -> bool:
        """Delete a trip"""
        if self.use_database:
            return TripRepository.delete(trip_id)
        else:
            if trip_id in self.trips:
                del self.trips[trip_id]
                return True
            return False
