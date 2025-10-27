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


def test_create_trip(setup_database, test_user):
    """Test creating a trip"""
    service = TripService()
    
    trip = service.create_trip(
        destination="Tokyo, Japan",
        start_date="2025-12-01",
        end_date="2025-12-10",
        travelers=["Adult", "Adult"],
        user_id=test_user.id,
        travel_style="leisure"
    )
    
    assert trip.destination == "Tokyo, Japan"
    assert trip.duration == 10
    assert len(trip.travelers) == 2
    assert trip.id is not None


def test_get_trip(setup_database, test_user):
    """Test retrieving a trip"""
    service = TripService()
    
    trip = service.create_trip(
        destination="London, UK",
        start_date="2025-11-01",
        end_date="2025-11-05",
        travelers=["Adult"],
        user_id=test_user.id
    )
    
    assert trip.id is not None
    retrieved = service.get_trip(trip.id)
    assert retrieved is not None
    assert retrieved.destination == "London, UK"


def test_list_trips(setup_database, test_user):
    """Test listing all trips"""
    user_id = test_user.id  # Store ID to avoid detached instance issues
    service = TripService()
    
    service.create_trip("Rome", "2025-12-01", "2025-12-07", ["Adult", "Child"], user_id)
    service.create_trip("Rome", "2025-12-01", "2025-12-07", ["Adult", "Child"], user_id)
    
    trips = service.list_trips()
    assert len(trips) == 2


def test_delete_trip(setup_database, test_user):
    """Test deleting a trip"""
    service = TripService()
    
    trip = service.create_trip("Berlin", "2025-11-01", "2025-11-03", ["Adult"], test_user.id)
    trip_id = trip.id
    
    assert trip_id is not None
    assert service.delete_trip(trip_id) is True
    assert service.get_trip(trip_id) is None
