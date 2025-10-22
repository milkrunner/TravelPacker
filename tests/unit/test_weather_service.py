"""
Tests for weather service
"""

import pytest
from unittest.mock import Mock, patch
from src.services.weather_service import WeatherService, get_weather_service


@pytest.fixture
def weather_service_enabled():
    """Create weather service with mocked API key"""
    with patch.dict('os.environ', {'WEATHER_API_KEY': 'test_api_key', 'WEATHER_UNITS': 'metric'}):
        service = WeatherService()
        return service


@pytest.fixture
def weather_service_disabled():
    """Create weather service without API key"""
    with patch.dict('os.environ', {}, clear=True):
        service = WeatherService()
        return service


def test_weather_service_disabled_without_api_key(weather_service_disabled):
    """Test weather service is disabled without API key"""
    assert weather_service_disabled.enabled is False
    
    result = weather_service_disabled.get_weather_summary("Tokyo", "2025-11-01", "2025-11-05")
    assert result is None


def test_weather_service_enabled_with_api_key(weather_service_enabled):
    """Test weather service is enabled with API key"""
    assert weather_service_enabled.enabled is True


@patch('requests.get')
def test_fetch_current_weather_success(mock_get, weather_service_enabled):
    """Test successful current weather fetch"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "main": {
            "temp": 22.5,
            "feels_like": 21.0,
            "humidity": 65
        },
        "weather": [
            {"description": "scattered clouds", "main": "Clouds"}
        ]
    }
    mock_get.return_value = mock_response
    
    result = weather_service_enabled._fetch_current_weather("Tokyo")
    
    assert result is not None
    assert result["main"]["temp"] == 22.5
    mock_get.assert_called_once()


@patch('requests.get')
def test_fetch_forecast_success(mock_get, weather_service_enabled):
    """Test successful forecast fetch"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "list": [
            {
                "main": {"temp": 18.0},
                "weather": [{"main": "Rain"}]
            },
            {
                "main": {"temp": 20.0},
                "weather": [{"main": "Clouds"}]
            },
            {
                "main": {"temp": 22.0},
                "weather": [{"main": "Clear"}]
            }
        ]
    }
    mock_get.return_value = mock_response
    
    result = weather_service_enabled._fetch_forecast("Paris")
    
    assert result is not None
    assert "list" in result
    assert len(result["list"]) == 3
    mock_get.assert_called_once()


@patch('requests.get')
def test_fetch_weather_api_error(mock_get, weather_service_enabled):
    """Test weather fetch handles API errors gracefully"""
    mock_get.side_effect = Exception("API Error")
    
    result = weather_service_enabled._fetch_current_weather("InvalidCity")
    
    assert result is None


def test_build_summary_current_weather(weather_service_enabled):
    """Test building summary from current weather data"""
    from datetime import datetime
    
    weather_data = {
        "main": {
            "temp": 25.0,
            "feels_like": 24.0,
            "humidity": 55
        },
        "weather": [
            {"description": "clear sky", "main": "Clear"}
        ]
    }
    
    start = datetime(2025, 11, 1)
    end = datetime(2025, 11, 5)
    
    summary = weather_service_enabled._build_summary(weather_data, start, end, days_until_trip=10)
    
    assert "clear sky" in summary
    assert "25°C" in summary or "25" in summary


def test_build_summary_forecast(weather_service_enabled):
    """Test building summary from forecast data"""
    from datetime import datetime
    
    weather_data = {
        "list": [
            {"main": {"temp": 15.0}, "weather": [{"main": "Rain"}]},
            {"main": {"temp": 18.0}, "weather": [{"main": "Rain"}]},
            {"main": {"temp": 20.0}, "weather": [{"main": "Clouds"}]},
            {"main": {"temp": 22.0}, "weather": [{"main": "Clear"}]},
        ]
    }
    
    start = datetime(2025, 10, 25)
    end = datetime(2025, 10, 28)
    
    summary = weather_service_enabled._build_summary(weather_data, start, end, days_until_trip=3)
    
    assert "15" in summary or "22" in summary  # Temperature range
    assert "rain" in summary.lower()  # Rain mentioned


@patch('requests.get')
def test_get_weather_summary_uses_cache(mock_get, weather_service_enabled):
    """Test weather summary uses cache"""
    # Mock cache
    weather_service_enabled.cache.enabled = True
    weather_service_enabled.cache.get = Mock(return_value="Cached weather: sunny, 25°C")
    
    result = weather_service_enabled.get_weather_summary("Tokyo", "2025-11-01", "2025-11-05")
    
    assert result == "Cached weather: sunny, 25°C"
    # Should not call API if cache hit
    mock_get.assert_not_called()


@patch('requests.get')
@patch.object(WeatherService, '_fetch_current_weather')
def test_get_weather_summary_far_future_trip(mock_fetch_current, mock_get, weather_service_enabled):
    """Test far future trips use current weather"""
    mock_fetch_current.return_value = {
        "main": {"temp": 20.0, "feels_like": 19.0, "humidity": 60},
        "weather": [{"description": "partly cloudy", "main": "Clouds"}]
    }
    
    # Trip 30 days in future
    from datetime import datetime, timedelta
    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
    
    # Mock cache to return None (cache miss)
    weather_service_enabled.cache.get = Mock(return_value=None)
    weather_service_enabled.cache.set = Mock()
    
    result = weather_service_enabled.get_weather_summary("London", future_date, end_date)
    
    assert result is not None
    assert "partly cloudy" in result or "Clouds" in result or "20" in result


def test_singleton_weather_service():
    """Test get_weather_service returns singleton"""
    service1 = get_weather_service()
    service2 = get_weather_service()
    
    assert service1 is service2
