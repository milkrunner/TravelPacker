# Weather Integration Setup

## Overview

NikNotes integrates with OpenWeatherMap API to fetch real-time weather data for your destination. The AI packing suggestions automatically consider the expected weather conditions, helping you pack smarter.

## Features

- **Automatic Weather Fetching**: When generating AI suggestions, weather is automatically retrieved
- **Smart Caching**: Weather data is cached for 24 hours to minimize API calls
- **Trip Timeline Awareness**:
  - For trips within 5 days: Uses 5-day forecast
  - For future trips: Uses current weather as an estimate
- **Graceful Degradation**: App works normally if weather API is unavailable
- **Weather Summary Persistence**: Fetched weather is saved with your trip

## Getting Your Weather API Key

### OpenWeatherMap (Free Tier)

1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Click "Sign Up" (or "Sign In" if you have an account)
3. Navigate to "API keys" in your account
4. Copy your API key
5. Free tier includes:
   - 1,000 API calls per day
   - Current weather data
   - 5-day forecast
   - More than enough for personal use!

**Note**: API key activation can take up to 2 hours after signup.

## Configuration

### Local Development

Add to your `.env` file:

```bash
# Weather API Configuration
WEATHER_API_KEY=your_actual_api_key_here
WEATHER_UNITS=metric
WEATHER_PROVIDER=openweathermap
```

**Units Options:**

- `metric` - Celsius, km/h (default)
- `imperial` - Fahrenheit, mph

### Docker Deployment

Set environment variable before starting:

```bash
export WEATHER_API_KEY="your_actual_api_key_here"
docker-compose up -d
```

Or add to your `.env` file in the project root (Docker Compose will read it).

## How It Works

### 1. Trip Creation with AI Suggestions

When you create a trip with AI suggestions enabled:

```text
User creates trip → AI Service fetches weather → Weather added to prompt →
Suggestions generated → Weather saved to trip
```

### 2. Regenerating Suggestions

When you click "Get More Suggestions":

```text
Trip loaded → Check for existing weather → Fetch if missing →
Update prompt → Generate suggestions → Update trip
```

### 3. Weather Summary Format

Examples of weather summaries:

- **Near-term trip**: "Expected: light rain, 18°C (feels like 16°C), high humidity (78%)"
- **Future trip**: "Typical weather: clear sky, around 22°C"
- **Forecast range**: "Clouds, 15-23°C, expect rain"

## Weather-Aware AI Suggestions

The AI considers weather in several ways:

### Temperature-Based Items

- **Cold weather** (< 10°C): Warm jacket, gloves, thermal layers
- **Moderate** (10-20°C): Light jacket, layers
- **Warm** (20-30°C): Light clothing, sun protection
- **Hot** (> 30°C): Breathable fabrics, cooling items

### Condition-Based Items

- **Rain/Drizzle**: Umbrella, rain jacket, waterproof bags
- **Snow**: Winter boots, warm clothing, hand warmers
- **High humidity**: Quick-dry clothing, extra changes
- **Clear/Sunny**: Sunglasses, sunscreen, hat

### Example Prompt Enhancement

**Without weather:**

```text
Generate packing list for:
Destination: Tokyo, Japan
Duration: 5 days
Travel style: leisure
```

**With weather:**

```text
Generate packing list for:
Destination: Tokyo, Japan
Duration: 5 days
Travel style: leisure
Weather: Expected: light rain, 18°C (feels like 16°C), high humidity (78%)
```

**Result:** AI suggests rain gear, layers for cool temperatures, and quick-dry items for humidity.

## Troubleshooting

### Weather Not Fetching

**Check the logs:**

```bash
# Local development
Check console output for weather warnings

# Docker
docker-compose logs web | grep -i weather
```

**Common issues:**

1. **API key not set or invalid**

   ```text
   ⚠️ Weather API key not configured, weather integration disabled
   ```

   → Set `WEATHER_API_KEY` in `.env`

2. **API key not activated yet**

   ```text
   ⚠️ Weather fetch failed: 401
   ```

   → Wait up to 2 hours after OpenWeatherMap signup

3. **Unknown destination**

   ```text
   ⚠️ Current weather API error: 404
   ```

   → Use standard city names or "City, Country" format

4. **Network timeout**

5. ```text
   ⚠️ Weather fetch failed: timeout
   ```

   → Temporary issue, retry or check network

### Testing Weather Integration

Test with a simple Python script:

```python
import os
import requests

api_key = "your_api_key_here"
city = "Tokyo"

url = f"https://api.openweathermap.org/data/2.5/weather"
params = {
    "q": city,
    "appid": api_key,
    "units": "metric"
}

response = requests.get(url, params=params)
print(f"Status: {response.status_code}")
print(response.json())
```

Expected: Status 200 with weather data

### Checking Cached Weather

Weather is cached in Redis (if available) for 24 hours:

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# List weather cache keys
KEYS weather:*

# Get a specific weather cache
GET "weather:Tokyo:2025-10-25:2025-10-30:metric"
```

## API Rate Limits

OpenWeatherMap Free Tier:

- **Limit**: 1,000 calls/day
- **Cache duration**: 24 hours
- **Typical usage**: 5-20 calls/day (depends on new trip creation)

**Optimization strategies:**

- Weather is cached for 24 hours
- Only fetched when generating AI suggestions
- Existing weather data is reused when regenerating suggestions
- Failed fetches don't prevent trip creation

## Privacy & Data

- Weather API receives only: city name, start/end dates
- No personal information sent
- Weather summary stored in your database only
- No third-party tracking

## Future Enhancements

Potential improvements for future versions:

- Multiple weather provider support (WeatherAPI, Weather.gov)
- Manual weather input override
- Weather alerts and warnings
- Historical weather data for past trips
- Weather-based packing templates
- Multi-location trips with different weather

## Related Documentation

- [GEMINI_SETUP.md](GEMINI_SETUP.md) - AI service configuration
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - All features overview
- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Production setup

---

**Weather-aware packing = Stress-free travel!** 🌤️🧳
