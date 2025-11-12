"""
AI service for generating packing suggestions with Redis caching
"""

import os
from typing import List, Dict, Any, TYPE_CHECKING
from dotenv import load_dotenv
from src.models.trip import Trip
from src.services.cache_service import get_cache_service
from src.services.weather_service import get_weather_service
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    if TYPE_CHECKING:
        import google.generativeai as genai


class AIService:
    """Service for AI-powered features with blazing fast caching"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-pro")
        self.use_mock = not self.api_key or self.api_key == "your_api_key_here" or not GEMINI_AVAILABLE
        self.cache = get_cache_service()
        self.weather = get_weather_service()
        
        if not self.use_mock:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"AI Service initialized (Cache: {'ON' if self.cache.enabled else 'OFF'})")
    
    def generate_packing_suggestions(self, trip: Trip) -> List[str]:
        """Generate packing suggestions with blazing fast Redis caching ⚡"""
        # Fetch weather if not already present
        weather_summary = trip.weather_conditions
        if not weather_summary and self.weather.enabled:
            weather_summary = self.weather.get_weather_summary(
                trip.destination,
                trip.start_date,
                trip.end_date
            )
            if weather_summary:
                # Update trip with weather data (caller should persist)
                trip.weather_conditions = weather_summary
        
        # Create cache key from trip data
        cache_data = self._trip_to_cache_data(trip)
        
        # Try cache first (LIGHTNING FAST! ⚡)
        cached_suggestions = self.cache.get_ai_suggestions(cache_data)
        if cached_suggestions:
            logger.info(f"Cache HIT for trip {trip.id}: {trip.destination} ({trip.duration}d, {len(trip.travelers)} travelers)")
            return cached_suggestions
        
        logger.info(f"Cache MISS for trip {trip.id}: Generating fresh AI suggestions...")
        
        # Cache miss - generate new suggestions
        logger.info("Generating AI suggestions...")
        if self.use_mock:
            suggestions = self._get_mock_suggestions(trip)
        else:
            try:
                import re
                prompt = self._build_prompt(trip)
                response = self.model.generate_content(prompt)
                
                # Parse the response into a list - only keep lines matching "QUANTITY x ITEM" pattern
                suggestions = []
                for line in response.text.split('\n'):
                    line = line.strip()
                    # Remove bullet points, numbers, or dashes at start
                    cleaned = line.lstrip('•-*0123456789. ')
                    
                    # Only accept lines matching "QUANTITY x ITEM" format
                    if cleaned and re.match(r'^\d+\s*x\s*.+', cleaned, re.IGNORECASE):
                        suggestions.append(cleaned)
                
                suggestions = suggestions if suggestions else self._get_mock_suggestions(trip)
            except Exception as e:
                logger.error(f"Error generating AI suggestions: {e}")
                suggestions = self._get_mock_suggestions(trip)
        
        # Cache the results for 24 hours with trip_id mapping for easy invalidation
        cache_success = self.cache.set_ai_suggestions(cache_data, suggestions, ttl_hours=24, trip_id=trip.id)
        if cache_success:
            logger.info(f"Cached {len(suggestions)} suggestions for trip {trip.id} (TTL: 24h)")
        
        return suggestions
    
    def _trip_to_cache_data(self, trip: Trip) -> Dict[str, Any]:
        """Convert trip to cache key data (only relevant fields)
        
        Cache key includes:
        - destination: Location affects suggestions
        - start_date: Season/time of year affects packing needs
        - duration: Trip length determines quantities
        - travel_style: Business/leisure/adventure affects item selection
        - transportation: Flight/road trip affects luggage constraints
        - activities: Specific activities require specialized gear
        - weather: Temperature/conditions affect clothing choices
        - traveler_names: Individual travelers for personalization
        """
        return {
            "destination": trip.destination,
            "start_date": trip.start_date,  # Season matters for packing
            "duration": trip.duration,
            "travel_style": trip.travel_style,
            "transportation": trip.transportation,
            "activities": sorted(trip.activities) if trip.activities else [],
            "weather": trip.weather_conditions or "unknown",
            "travelers": sorted(trip.travelers) if trip.travelers else []  # Sorted for consistent hashing
        }
    
    def _get_mock_suggestions(self, trip: Trip) -> List[str]:
        """Get mock suggestions for testing"""
        num_travelers = len(trip.travelers)
        duration = trip.duration
        
        base_items = [
            f"{num_travelers} x Passport and travel documents",
            f"{num_travelers} x Phone charger",
            f"{num_travelers} x Comfortable walking shoes",
            f"{duration} x T-shirts",
            f"{duration} x Pairs of socks",
            f"{duration + 2} x Underwear",
            f"{num_travelers} x Toothbrush",
            "1 x Toothpaste",
            f"{num_travelers} x Deodorant",
            "1 x Sunscreen",
            f"{num_travelers} x Reusable water bottle",
        ]
        
        # Add items based on travel style
        if trip.travel_style == "business":
            base_items.extend([
                f"{duration} x Business shirts",
                f"{num_travelers} x Laptop and accessories",
                "1 x Business cards holder",
            ])
        elif trip.travel_style == "adventure":
            base_items.extend([
                f"{num_travelers} x Hiking boots",
                f"{num_travelers} x Backpack",
                "1 x First aid kit",
            ])
        
        # Add items based on transportation
        if trip.transportation == "flight":
            base_items.extend([
                f"{num_travelers} x Luggage tags",
                f"{num_travelers} x Travel pillow",
                f"{num_travelers} x Eye mask",
            ])
        
        return base_items[:15]  # Return top 15 suggestions
    
    def _build_prompt(self, trip: Trip) -> str:
        """Build prompt for AI model"""
        prompt = f"""Generate a comprehensive packing list for the following trip:

Destination: {trip.destination}
Duration: {trip.duration} days
Number of travelers: {len(trip.travelers)}
Travel style: {trip.travel_style}
Transportation: {trip.transportation}
"""
        
        if trip.activities:
            prompt += f"Activities: {', '.join(trip.activities)}\n"
        
        if trip.weather_conditions:
            prompt += f"Weather: {trip.weather_conditions}\n"
        
        if trip.special_notes:
            prompt += f"Special notes: {trip.special_notes}\n"
        
        prompt += f"""

IMPORTANT: For each item, suggest smart quantities based on:
- Trip duration ({trip.duration} days)
- Number of travelers ({len(trip.travelers)} person(s))
- Item shareability (e.g., toothpaste can be shared, but toothbrushes cannot)

Format each line EXACTLY as: "QUANTITY x ITEM_NAME"
Examples:
- "{trip.duration} x Pairs of socks" (one per day)
- "{len(trip.travelers)} x Toothbrush" (one per person)
- "1 x Toothpaste" (shared among all travelers)
- "{len(trip.travelers) * 2} x Underwear" (multiple per person)

Provide the complete packing list with smart quantities, one item per line.
"""
        
        return prompt
