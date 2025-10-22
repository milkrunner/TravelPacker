"""
Tests for trip service
"""

import pytest
from src.database import Base, engine
from src.services.trip_service import TripService


@pytest.fixture(scope="function")
def setup_database():
    """Setup test database before each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


def test_create_trip(setup_database):
    """Test creating a trip"""
    service = TripService()
    
    trip = service.create_trip(
        destination="Tokyo, Japan",
        start_date="2025-12-01",
        end_date="2025-12-10",
        travelers=["Adult", "Adult"],
        user_id="test_user",
        travel_style="leisure"
    )
    
    assert trip.destination == "Tokyo, Japan"
    assert trip.duration == 10
    assert len(trip.travelers) == 2
    assert trip.id is not None


def test_get_trip(setup_database):
    """Test retrieving a trip"""
    service = TripService()
    
    trip = service.create_trip(
        destination="London, UK",
        start_date="2025-11-01",
        end_date="2025-11-05",
        travelers=["Adult"],
        user_id="test_user"
    )
    
    retrieved = service.get_trip(trip.id)
    assert retrieved is not None
    assert retrieved.destination == "London, UK"


def test_list_trips(setup_database):
    """Test listing all trips"""
    service = TripService()
    
    service.create_trip("Paris", "2025-11-01", "2025-11-05", ["Adult"], "test_user")
    service.create_trip("Rome", "2025-12-01", "2025-12-07", ["Adult", "Child"], "test_user")
    
    trips = service.list_trips()
    assert len(trips) == 2


def test_delete_trip(setup_database):
    """Test deleting a trip"""
    service = TripService()
    
    trip = service.create_trip("Berlin", "2025-11-01", "2025-11-03", ["Adult"], "test_user")
    trip_id = trip.id
    
    assert service.delete_trip(trip_id) is True
    assert service.get_trip(trip_id) is None
