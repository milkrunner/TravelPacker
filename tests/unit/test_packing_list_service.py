"""
Tests for packing list service
"""

import pytest
from src.database import Base, engine
from src.services.packing_list_service import PackingListService
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


def test_create_item(setup_database):
    """Test creating a packing item"""
    ai_service = AIService()
    service = PackingListService(ai_service)
    
    item = service.create_item(
        trip_id="trip_1",
        name="Passport",
        category="documents",
        is_essential=True
    )
    
    assert item.name == "Passport"
    assert item.is_essential is True
    assert item.is_packed is False


def test_mark_item_packed(setup_database):
    """Test marking an item as packed"""
    ai_service = AIService()
    service = PackingListService(ai_service)
    
    item = service.create_item("trip_1", "Toothbrush", "toiletries")
    item_id = item.id
    
    updated = service.mark_item_packed(item_id, True)
    
    assert updated is not None
    assert updated.is_packed is True


def test_get_items_for_trip(setup_database):
    """Test getting all items for a trip"""
    ai_service = AIService()
    service = PackingListService(ai_service)
    
    service.create_item("trip_1", "Passport", "documents")
    service.create_item("trip_1", "Sunscreen", "toiletries")
    service.create_item("trip_2", "Laptop", "electronics")
    
    items = service.get_items_for_trip("trip_1")
    assert len(items) == 2


def test_packing_progress(setup_database):
    """Test packing progress calculation"""
    ai_service = AIService()
    service = PackingListService(ai_service)
    
    item1 = service.create_item("trip_1", "Passport", "documents")
    item2 = service.create_item("trip_1", "Sunscreen", "toiletries")
    item3 = service.create_item("trip_1", "Phone", "electronics")
    
    service.mark_item_packed(item1.id, True)
    service.mark_item_packed(item2.id, True)
    
    progress = service.get_packing_progress("trip_1")
    
    assert progress["total_items"] == 3
    assert progress["packed_items"] == 2
    assert progress["unpacked_items"] == 1
    assert progress["completion_percentage"] == pytest.approx(66.67, rel=0.01)
