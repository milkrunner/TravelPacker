"""
Tests for packing list service
"""

import pytest
from src.database import Base, engine
from src.services.packing_list_service import PackingListService
from src.services.trip_service import TripService
from src.services.ai_service import AIService
from src.models.trip import Trip


@pytest.fixture(scope="function")
def setup_database():
    """Setup test database before each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_trip(setup_database, test_user):
    """Create a test trip"""
    trip_service = TripService()
    return trip_service.create_trip(
        destination="Test Destination",
        start_date="2025-12-01",
        end_date="2025-12-10",
        travelers=["Adult"],
        user_id=test_user.id
    )


def test_create_item(test_trip):
    """Test creating a packing item"""
    ai_service = AIService()
    service = PackingListService(ai_service)
    
    item = service.create_item(
        trip_id=test_trip.id,
        name="Passport",
        category="documents",
        is_essential=True
    )
    
    assert item.name == "Passport"
    assert item.is_essential is True
    assert item.is_packed is False


def test_mark_item_packed(test_trip):
    """Test marking an item as packed"""
    ai_service = AIService()
    service = PackingListService(ai_service)
    
    item = service.create_item(test_trip.id, "Toothbrush", "toiletries")
    item_id = item.id
    
    assert item_id is not None
    updated = service.mark_item_packed(item_id, True)
    
    assert updated is not None
    assert updated.is_packed is True


def test_get_items_for_trip(setup_database, test_user):
    """Test getting all items for a trip"""
    user_id = test_user.id  # Store ID to avoid detached instance issues
    
    # Create two trips
    trip_service = TripService()
    trip1 = trip_service.create_trip("Paris", "2025-12-01", "2025-12-10", ["Adult"], user_id)
    trip2 = trip_service.create_trip("London", "2025-12-01", "2025-12-10", ["Adult"], user_id)
    
    assert trip1.id is not None and trip2.id is not None
    
    ai_service = AIService()
    service = PackingListService(ai_service)
    
    service.create_item(trip1.id, "Passport", "documents")
    service.create_item(trip1.id, "Sunscreen", "toiletries")
    service.create_item(trip2.id, "Laptop", "electronics")
    
    items = service.get_items_for_trip(trip1.id)
    assert len(items) == 2


def test_packing_progress(test_trip):
    """Test packing progress calculation"""
    ai_service = AIService()
    service = PackingListService(ai_service)
    
    item1 = service.create_item(test_trip.id, "Passport", "documents")
    item2 = service.create_item(test_trip.id, "Sunscreen", "toiletries")
    item3 = service.create_item(test_trip.id, "Phone", "electronics")
    
    assert item1.id is not None and item2.id is not None
    
    service.mark_item_packed(item1.id, True)
    service.mark_item_packed(item2.id, True)
    
    progress = service.get_packing_progress(test_trip.id)
    
    assert progress["total_items"] == 3
    assert progress["packed_items"] == 2
    assert progress["unpacked_items"] == 1
    assert progress["completion_percentage"] == pytest.approx(66.67, rel=0.01)
