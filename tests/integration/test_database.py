"""
Tests for database repository
"""

import pytest
from src.database import init_db, engine, Base
from src.database.repository import TripRepository, PackingItemRepository
from src.models.trip import Trip, TravelStyle, TransportMethod
from src.models.packing_item import PackingItem, ItemCategory


@pytest.fixture(scope="function")
def setup_database():
    """Setup test database before each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


def test_trip_repository_create(setup_database):
    """Test creating a trip in database"""
    trip = Trip(
        destination="Tokyo, Japan",
        start_date="2025-12-01",
        end_date="2025-12-10",
        travelers=["Adult", "Adult"],
        travel_style=TravelStyle.LEISURE,
        transportation=TransportMethod.FLIGHT
    )
    
    saved_trip = TripRepository.create(trip, "test_user")
    
    assert saved_trip.id is not None
    assert saved_trip.destination == "Tokyo, Japan"
    assert saved_trip.duration == 10


def test_trip_repository_get(setup_database):
    """Test retrieving a trip from database"""
    trip = Trip(
        destination="Paris, France",
        start_date="2025-11-01",
        end_date="2025-11-05",
        travelers=["Adult"]
    )
    
    saved_trip = TripRepository.create(trip, "test_user")
    retrieved_trip = TripRepository.get(saved_trip.id)
    
    assert retrieved_trip is not None
    assert retrieved_trip.destination == "Paris, France"


def test_trip_repository_list(setup_database):
    """Test listing all trips"""
    trip1 = Trip(destination="London", start_date="2025-11-01", end_date="2025-11-03", travelers=["Adult"])
    trip2 = Trip(destination="Rome", start_date="2025-12-01", end_date="2025-12-05", travelers=["Adult"])
    
    TripRepository.create(trip1, "test_user")
    TripRepository.create(trip2, "test_user")
    
    trips = TripRepository.list_all()
    assert len(trips) == 2


def test_trip_repository_delete(setup_database):
    """Test deleting a trip"""
    trip = Trip(destination="Berlin", start_date="2025-11-01", end_date="2025-11-03", travelers=["Adult"])
    saved_trip = TripRepository.create(trip, "test_user")
    
    success = TripRepository.delete(saved_trip.id)
    assert success is True
    
    deleted_trip = TripRepository.get(saved_trip.id)
    assert deleted_trip is None


def test_packing_item_repository_create(setup_database):
    """Test creating a packing item"""
    # First create a trip
    trip = Trip(destination="Sydney", start_date="2025-11-01", end_date="2025-11-05", travelers=["Adult"])
    saved_trip = TripRepository.create(trip, "test_user")
    
    item = PackingItem(
        trip_id=saved_trip.id,
        name="Passport",
        category=ItemCategory.DOCUMENTS,
        is_essential=True
    )
    
    saved_item = PackingItemRepository.create(item)
    
    assert saved_item.id is not None
    assert saved_item.name == "Passport"
    assert saved_item.is_essential is True


def test_packing_item_repository_get_by_trip(setup_database):
    """Test getting all items for a trip"""
    trip = Trip(destination="Bangkok", start_date="2025-11-01", end_date="2025-11-07", travelers=["Adult"])
    saved_trip = TripRepository.create(trip, "test_user")
    
    item1 = PackingItem(trip_id=saved_trip.id, name="Passport", category=ItemCategory.DOCUMENTS)
    item2 = PackingItem(trip_id=saved_trip.id, name="Sunscreen", category=ItemCategory.TOILETRIES)
    
    PackingItemRepository.create(item1)
    PackingItemRepository.create(item2)
    
    items = PackingItemRepository.get_by_trip(saved_trip.id)
    assert len(items) == 2


def test_packing_item_repository_update(setup_database):
    """Test updating a packing item"""
    trip = Trip(destination="Dubai", start_date="2025-11-01", end_date="2025-11-05", travelers=["Adult"])
    saved_trip = TripRepository.create(trip, "test_user")
    
    item = PackingItem(trip_id=saved_trip.id, name="Phone", category=ItemCategory.ELECTRONICS)
    saved_item = PackingItemRepository.create(item)
    
    updated_item = PackingItemRepository.update(saved_item.id, is_packed=True)
    
    assert updated_item.is_packed is True


def test_cascade_delete(setup_database):
    """Test that deleting a trip deletes all associated items"""
    trip = Trip(destination="Singapore", start_date="2025-11-01", end_date="2025-11-04", travelers=["Adult"])
    saved_trip = TripRepository.create(trip, "test_user")
    
    item = PackingItem(trip_id=saved_trip.id, name="Camera", category=ItemCategory.ELECTRONICS)
    saved_item = PackingItemRepository.create(item)
    
    # Delete the trip
    TripRepository.delete(saved_trip.id)
    
    # Item should be deleted too (cascade)
    deleted_item = PackingItemRepository.get(saved_item.id)
    assert deleted_item is None
