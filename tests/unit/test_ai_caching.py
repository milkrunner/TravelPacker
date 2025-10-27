"""
Unit tests for AI suggestion caching behavior
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.ai_service import AIService
from src.services.cache_service import CacheService, NullCacheService
from src.models.trip import Trip, TravelStyle, TransportMethod


class TestAICachingStrategy:
    """Test AI suggestion caching with different trip contexts"""
    
    def test_cache_key_includes_all_relevant_context(self):
        """Verify cache key includes destination, dates, travelers, style, transport, activities, weather"""
        ai_service = AIService()
        
        trip = Trip(
            id="trip_123",
            destination="Paris",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Alice", "Bob"],
            travel_style=TravelStyle.LEISURE,
            transportation=TransportMethod.FLIGHT,
            activities=["museums", "dining"],
            weather_conditions="Sunny, 20-25°C"
        )
        
        cache_data = ai_service._trip_to_cache_data(trip)
        
        # Verify all context fields are present
        assert cache_data["destination"] == "Paris"
        assert cache_data["start_date"] == "2025-06-15"  # Season matters
        assert cache_data["duration"] == 8
        assert cache_data["travel_style"] == TravelStyle.LEISURE
        assert cache_data["transportation"] == TransportMethod.FLIGHT
        assert cache_data["activities"] == ["dining", "museums"]  # Sorted
        assert cache_data["weather"] == "Sunny, 20-25°C"
        assert cache_data["travelers"] == ["Alice", "Bob"]  # Sorted
    
    def test_cache_key_differs_for_different_destinations(self):
        """Different destinations should produce different cache keys"""
        ai_service = AIService()
        
        trip_paris = Trip(
            destination="Paris",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Alice"]
        )
        
        trip_london = Trip(
            destination="London",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Alice"]
        )
        
        cache_paris = ai_service._trip_to_cache_data(trip_paris)
        cache_london = ai_service._trip_to_cache_data(trip_london)
        
        assert cache_paris != cache_london
    
    def test_cache_key_differs_for_different_dates(self):
        """Different travel dates should produce different cache keys (seasonal context)"""
        ai_service = AIService()
        
        trip_summer = Trip(
            destination="Paris",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Alice"]
        )
        
        trip_winter = Trip(
            destination="Paris",
            start_date="2025-12-15",
            end_date="2025-12-22",
            travelers=["Alice"]
        )
        
        cache_summer = ai_service._trip_to_cache_data(trip_summer)
        cache_winter = ai_service._trip_to_cache_data(trip_winter)
        
        assert cache_summer["start_date"] != cache_winter["start_date"]
        assert cache_summer != cache_winter
    
    def test_cache_key_differs_for_different_travelers(self):
        """Different travelers should produce different cache keys"""
        ai_service = AIService()
        
        trip_solo = Trip(
            destination="Paris",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Alice"]
        )
        
        trip_couple = Trip(
            destination="Paris",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Alice", "Bob"]
        )
        
        cache_solo = ai_service._trip_to_cache_data(trip_solo)
        cache_couple = ai_service._trip_to_cache_data(trip_couple)
        
        assert cache_solo["travelers"] != cache_couple["travelers"]
        assert cache_solo != cache_couple
    
    def test_cache_key_same_for_reordered_activities(self):
        """Activities in different order should produce same cache key (sorted)"""
        ai_service = AIService()
        
        trip_1 = Trip(
            destination="Paris",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Alice"],
            activities=["museums", "dining", "shopping"]
        )
        
        trip_2 = Trip(
            destination="Paris",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Alice"],
            activities=["shopping", "museums", "dining"]
        )
        
        cache_1 = ai_service._trip_to_cache_data(trip_1)
        cache_2 = ai_service._trip_to_cache_data(trip_2)
        
        assert cache_1["activities"] == cache_2["activities"]
        assert cache_1 == cache_2
    
    def test_cache_key_same_for_reordered_travelers(self):
        """Travelers in different order should produce same cache key (sorted)"""
        ai_service = AIService()
        
        trip_1 = Trip(
            destination="Paris",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Bob", "Alice", "Charlie"]
        )
        
        trip_2 = Trip(
            destination="Paris",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Alice", "Bob", "Charlie"]
        )
        
        cache_1 = ai_service._trip_to_cache_data(trip_1)
        cache_2 = ai_service._trip_to_cache_data(trip_2)
        
        assert cache_1["travelers"] == cache_2["travelers"]
        assert cache_1 == cache_2


class TestCacheInvalidation:
    """Test cache invalidation on trip mutations"""
    
    @patch('src.services.cache_service.get_cache_service')
    def test_cache_invalidated_on_trip_update(self, mock_get_cache):
        """Verify AI cache is invalidated when trip is updated"""
        from src.services.trip_service import TripService
        
        # Mock cache service
        mock_cache = Mock()
        mock_cache.enabled = True
        mock_cache.invalidate_ai_suggestions_for_trip = Mock(return_value=True)
        mock_cache.invalidate_trip = Mock(return_value=True)
        mock_get_cache.return_value = mock_cache
        
        trip_service = TripService(use_database=False)
        
        # Create trip
        trip = trip_service.create_trip(
            destination="Paris",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Alice"]
        )
        
        assert trip.id is not None, "Trip ID should not be None"
        
        # Update trip
        trip_service.update_trip(trip.id, destination="London")
        
        # Verify cache was invalidated
        mock_cache.invalidate_ai_suggestions_for_trip.assert_called_once_with(trip.id)
        mock_cache.invalidate_trip.assert_called_once_with(trip.id)
    
    @patch('src.services.cache_service.get_cache_service')
    def test_cache_invalidated_on_trip_deletion(self, mock_get_cache):
        """Verify AI cache is invalidated when trip is deleted"""
        from src.services.trip_service import TripService
        
        # Mock cache service
        mock_cache = Mock()
        mock_cache.enabled = True
        mock_cache.invalidate_ai_suggestions_for_trip = Mock(return_value=True)
        mock_cache.invalidate_trip = Mock(return_value=True)
        mock_get_cache.return_value = mock_cache
        
        trip_service = TripService(use_database=False)
        
        # Create trip
        trip = trip_service.create_trip(
            destination="Paris",
            start_date="2025-06-15",
            end_date="2025-06-22",
            travelers=["Alice"]
        )
        
        assert trip.id is not None, "Trip ID should not be None"
        
        # Delete trip
        trip_service.delete_trip(trip.id)
        
        # Verify cache was invalidated
        mock_cache.invalidate_ai_suggestions_for_trip.assert_called_once_with(trip.id)
        mock_cache.invalidate_trip.assert_called_once_with(trip.id)
    
    def test_cache_miss_generates_new_suggestions(self):
        """Verify cache miss triggers AI generation"""
        with patch('src.services.ai_service.genai'), \
             patch('src.services.ai_service.get_cache_service') as mock_get_cache:
            
            # Mock cache to always miss
            mock_cache = NullCacheService()
            mock_get_cache.return_value = mock_cache
            
            ai_service = AIService()
            
            trip = Trip(
                id="trip_123",
                destination="Paris",
                start_date="2025-06-15",
                end_date="2025-06-22",
                travelers=["Alice"]
            )
            
            suggestions = ai_service.generate_packing_suggestions(trip)
            
            # Verify suggestions were generated (mock suggestions)
            assert len(suggestions) > 0
            assert all(isinstance(s, str) for s in suggestions)
    
    @patch('src.services.ai_service.get_cache_service')
    def test_cache_hit_skips_ai_generation(self, mock_get_cache):
        """Verify cache hit returns cached suggestions without AI call"""
        with patch('src.services.ai_service.genai'):
            # Mock cache to always hit
            cached_suggestions = ["1 x Passport", "2 x T-shirts"]
            mock_cache = Mock()
            mock_cache.enabled = True
            mock_cache.get_ai_suggestions = Mock(return_value=cached_suggestions)
            mock_cache.set_ai_suggestions = Mock(return_value=True)
            mock_get_cache.return_value = mock_cache
            
            ai_service = AIService()
            
            trip = Trip(
                id="trip_123",
                destination="Paris",
                start_date="2025-06-15",
                end_date="2025-06-22",
                travelers=["Alice"]
            )
            
            suggestions = ai_service.generate_packing_suggestions(trip)
            
            # Verify cached suggestions returned
            assert suggestions == cached_suggestions
            mock_cache.get_ai_suggestions.assert_called_once()


class TestCachePerformance:
    """Test caching improves performance"""
    
    def test_cache_disabled_still_works(self):
        """Verify app works correctly when cache is disabled"""
        with patch('src.services.ai_service.genai'), \
             patch('src.services.ai_service.get_cache_service') as mock_get_cache:
            
            # Simulate Redis down
            mock_cache = NullCacheService()
            mock_get_cache.return_value = mock_cache
            
            ai_service = AIService()
            
            trip = Trip(
                id="trip_123",
                destination="Paris",
                start_date="2025-06-15",
                end_date="2025-06-22",
                travelers=["Alice"]
            )
            
            # Should fall back to direct AI generation
            suggestions = ai_service.generate_packing_suggestions(trip)
            assert len(suggestions) > 0
    
    def test_cache_key_deterministic(self):
        """Verify same trip always produces same cache key"""
        from src.services.cache_service import CacheService
        
        cache = CacheService(redis_url="redis://fake:6379")
        
        trip_data = {
            "destination": "Paris",
            "start_date": "2025-06-15",
            "duration": 8,
            "travel_style": "leisure",
            "transportation": "flight",
            "activities": ["museums", "dining"],
            "weather": "Sunny",
            "travelers": ["Alice", "Bob"]
        }
        
        # Generate key multiple times
        key1 = cache._generate_key("ai_suggestions", trip_data)
        key2 = cache._generate_key("ai_suggestions", trip_data)
        key3 = cache._generate_key("ai_suggestions", trip_data)
        
        # All keys should be identical
        assert key1 == key2 == key3
        assert key1.startswith("ai_suggestions:")
    
    def test_different_trips_produce_different_cache_keys(self):
        """Verify different trips produce different cache keys"""
        from src.services.cache_service import CacheService
        
        cache = CacheService(redis_url="redis://fake:6379")
        
        trip_data_1 = {
            "destination": "Paris",
            "start_date": "2025-06-15",
            "duration": 8,
            "travelers": ["Alice"]
        }
        
        trip_data_2 = {
            "destination": "London",
            "start_date": "2025-06-15",
            "duration": 8,
            "travelers": ["Alice"]
        }
        
        key1 = cache._generate_key("ai_suggestions", trip_data_1)
        key2 = cache._generate_key("ai_suggestions", trip_data_2)
        
        # Keys must be different
        assert key1 != key2
