"""
Weather service for fetching destination weather forecasts
"""

import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.services.cache_service import get_cache_service

load_dotenv()


class WeatherService:
    """Service for fetching weather data with caching"""
    
    def __init__(self):
        self.api_key = os.getenv("WEATHER_API_KEY")
        self.units = os.getenv("WEATHER_UNITS", "metric")  # metric or imperial
        self.provider = os.getenv("WEATHER_PROVIDER", "openweathermap")
        self.cache = get_cache_service()
        self.enabled = bool(self.api_key and self.api_key != "your_weather_api_key_here")
        
        if not self.enabled:
            print("⚠️  Weather API key not configured, weather integration disabled")
    
    def get_weather_summary(
        self, 
        destination: str, 
        start_date: str, 
        end_date: str
    ) -> Optional[str]:
        """
        Get weather summary for a destination and date range
        
        Args:
            destination: City name or "City, Country"
            start_date: ISO format date string (YYYY-MM-DD)
            end_date: ISO format date string (YYYY-MM-DD)
            
        Returns:
            Human-readable weather summary or None if unavailable
        """
        if not self.enabled:
            return None
        
        # Check cache first (24 hour TTL for weather)
        cache_key = f"weather:{destination}:{start_date}:{end_date}:{self.units}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            # Parse dates
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            days_until_trip = (start - datetime.now()).days
            
            # Get weather based on timeframe
            if days_until_trip <= 5:
                # Use 5-day forecast for near-term trips
                weather_data = self._fetch_forecast(destination)
            else:
                # For far future trips, use current weather as estimate
                weather_data = self._fetch_current_weather(destination)
            
            if not weather_data:
                return None
            
            # Build summary
            summary = self._build_summary(weather_data, start, end, days_until_trip)
            
            # Cache for 24 hours
            self.cache.set(cache_key, summary, ttl_hours=24)
            
            return summary
            
        except Exception as e:
            print(f"⚠️  Weather fetch failed: {e}")
            return None
    
    def _fetch_current_weather(self, destination: str) -> Optional[Dict[str, Any]]:
        """Fetch current weather for a destination"""
        if self.provider != "openweathermap":
            return None
        
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": destination,
                "appid": self.api_key,
                "units": self.units,
                "lang": "en"
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"⚠️  Current weather API error: {e}")
            return None
    
    def _fetch_forecast(self, destination: str) -> Optional[Dict[str, Any]]:
        """Fetch 5-day forecast for a destination"""
        if self.provider != "openweathermap":
            return None
        
        try:
            url = "https://api.openweathermap.org/data/2.5/forecast"
            params = {
                "q": destination,
                "appid": self.api_key,
                "units": self.units,
                "lang": "en"
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"⚠️  Forecast API error: {e}")
            return None
    
    def _build_summary(
        self, 
        weather_data: Dict[str, Any], 
        start: datetime, 
        end: datetime,
        days_until_trip: int
    ) -> str:
        """Build human-readable weather summary from API response"""
        
        # Handle current weather response
        if "main" in weather_data and "weather" in weather_data:
            temp = weather_data["main"]["temp"]
            feels_like = weather_data["main"]["feels_like"]
            humidity = weather_data["main"]["humidity"]
            condition = weather_data["weather"][0]["description"]
            
            temp_unit = "°C" if self.units == "metric" else "°F"
            
            if days_until_trip > 5:
                # Far future - use current as estimate
                summary = f"Typical weather: {condition}, around {temp:.0f}{temp_unit}"
            else:
                # Near term
                summary = f"Expected: {condition}, {temp:.0f}{temp_unit} (feels like {feels_like:.0f}{temp_unit})"
            
            # Add humidity if high
            if humidity > 70:
                summary += f", high humidity ({humidity}%)"
            
            return summary
        
        # Handle forecast response
        if "list" in weather_data:
            forecasts = weather_data["list"]
            
            # Extract temperature range and conditions
            temps = [f["main"]["temp"] for f in forecasts]
            conditions = [f["weather"][0]["main"] for f in forecasts]
            
            min_temp = min(temps)
            max_temp = max(temps)
            temp_unit = "°C" if self.units == "metric" else "°F"
            
            # Get dominant condition
            from collections import Counter
            dominant_condition = Counter(conditions).most_common(1)[0][0]
            
            # Check for precipitation
            has_rain = any(c in ["Rain", "Drizzle", "Thunderstorm"] for c in conditions)
            has_snow = any(c == "Snow" for c in conditions)
            
            summary = f"{dominant_condition}, {min_temp:.0f}-{max_temp:.0f}{temp_unit}"
            
            if has_rain:
                summary += ", expect rain"
            if has_snow:
                summary += ", expect snow"
            
            return summary
        
        return "Weather data unavailable"


# Singleton instance
_weather_instance: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    """Get or create weather service singleton"""
    global _weather_instance
    if _weather_instance is None:
        _weather_instance = WeatherService()
    return _weather_instance
