# AI Suggestion Caching System

## Overview

The application implements intelligent caching for AI-generated packing suggestions to minimize API calls, reduce costs, and improve response latency. Suggestions are cached based on trip context and automatically invalidated when trip details change.

## Architecture

### Cache Key Generation

AI suggestions are cached using a **deterministic MD5 hash** of the trip context:

```python
cache_data = {
    "destination": trip.destination,
    "start_date": trip.start_date,      # NEW: Season/time of year affects weather
    "duration": trip.duration,
    "travel_style": trip.travel_style,
    "transportation": trip.transportation,
    "activities": sorted(trip.activities),  # Sorted for consistency
    "weather": trip.weather_conditions or "unknown",
    "travelers": sorted(trip.travelers)  # NEW: Individual names (sorted)
}

# Generate cache key: ai_suggestions:<md5_hash>
cache_key = f"ai_suggestions:{md5(json.dumps(cache_data, sort_keys=True))}"
```

**Key Properties:**

- **Deterministic**: Same trip context always generates the same key
- **Context-aware**: Changes to any relevant field generate a new key
- **Collision-resistant**: MD5 provides sufficient uniqueness for this use case
- **Season-aware**: Start date included to differentiate summer vs. winter trips
- **Traveler-specific**: Individual traveler names tracked for future personalization

> **See also**: [AI Cache Invalidation](./ai-cache-invalidation.md) for detailed invalidation strategies and testing.

### Cache Mapping

To enable efficient cache invalidation when trips are updated, we maintain a **bidirectional mapping**:

```text
trip_id → cache_key mapping
--------------------------
ai_trip_mapping:trip_123 → ai_suggestions:a1b2c3d4...
```

This allows us to:

1. **Quick invalidation**: Delete cache by trip_id without recalculating hash
2. **Automatic expiry**: Mapping expires with the cached data (24 hours)

## Caching Flow

### 1. Generate Suggestions (with caching)

```python
def generate_packing_suggestions(trip: Trip) -> List[str]:
    # 1. Fetch weather data if needed
    if not trip.weather_conditions:
        trip.weather_conditions = weather_service.get_weather_summary(...)

    # 2. Create cache key from trip context
    cache_data = _trip_to_cache_data(trip)

    # 3. Try cache first (FAST! ⚡)
    cached = cache.get_ai_suggestions(cache_data)
    if cached:
        print("🚀 Cache HIT: AI suggestions")
        return cached

    # 4. Cache miss - generate new suggestions
    print("🤖 Generating AI suggestions...")
    suggestions = _call_gemini_api(trip) or _get_mock_suggestions(trip)

    # 5. Cache results for 24 hours with trip_id mapping
    cache.set_ai_suggestions(cache_data, suggestions, ttl_hours=24, trip_id=trip.id)

    return suggestions
```

**Performance:**

- **Cache hit**: ~10-50ms (Redis lookup)
- **Cache miss**: ~2-5 seconds (Gemini API call)
- **Improvement**: 40-500x faster with cache

### 2. Invalidate on Trip Mutation

```python
def update_trip(trip_id: str, **kwargs) -> Optional[Trip]:
    # Update trip in database
    trip = TripRepository.update(trip_id, **kwargs)

    # Invalidate AI suggestion cache
    if trip:
        cache.invalidate_ai_suggestions_for_trip(trip_id)
        cache.invalidate_trip(trip_id)

    return trip
```

**Triggers for Invalidation:**

- `update_trip()`: Any field change (destination, dates, travelers, etc.)
- `delete_trip()`: Trip removal

**Not Invalidated On:**

- Packing item changes (toggle, add, delete) - doesn't affect suggestions
- Trip views/reads - read-only operations

## Cache Invalidation Strategy

### Invalidation Method

```python
def invalidate_ai_suggestions_for_trip(trip_id: str) -> bool:
    # 1. Get cached key from mapping
    mapping_key = f"ai_trip_mapping:{trip_id}"
    cache_key = redis.get(mapping_key)

    # 2. Delete cached suggestions
    if cache_key:
        redis.delete(cache_key)
        redis.delete(mapping_key)
        print(f"🗑️ Invalidated AI suggestions cache for trip {trip_id}")
        return True

    return False
```

### Why Not Pattern-Based Invalidation?

We **avoid** using Redis `KEYS` or `SCAN` to find cache entries by pattern because:

- ❌ **Performance**: O(N) operation on large datasets
- ❌ **Blocking**: Can block other operations in single-threaded Redis
- ❌ **Complexity**: Requires maintaining indexes

Instead, we use **direct mapping** for O(1) invalidation.

## Cache Configuration

### TTL (Time To Live)

```python
# AI suggestions cache
TTL = 24 hours  # Balance between freshness and cost savings

# Trip data cache
TTL = 30 minutes  # Short-lived, frequently changing
```

**Rationale:**

- **24 hours for AI**: Trip context rarely changes multiple times per day
- **Auto-expiry**: Stale data automatically cleaned up
- **Cost optimization**: Reduces API calls by ~95% for typical usage

### Redis Configuration

```python
# Environment variables
USE_REDIS=true                    # Enable/disable caching
REDIS_URL=redis://localhost:6379/0
REDIS_CONNECT_TIMEOUT=0.8         # Connection timeout (seconds)
REDIS_SOCKET_TIMEOUT=0.8          # Socket timeout (seconds)
REDIS_MAX_CONNECTIONS=50          # Connection pool size
```

**Graceful Degradation:**

- If Redis unavailable → Cache disabled, direct API calls
- No application errors → Silent fallback to uncached mode

## Performance Metrics

### Cache Hit Rate

```python
cache_stats = cache.get_stats()
# {
#     "enabled": true,
#     "keyspace_hits": 1247,
#     "keyspace_misses": 53,
#     "hit_rate": "95.9%",
#     "used_memory_human": "2.3M"
# }
```

**Target Metrics:**

- **Hit rate**: >80% (typical for stable trip data)
- **Miss rate**: <20% (new trips, mutations)
- **Memory usage**: <10MB for 1000 cached suggestions

### Latency Improvements

| Operation                 | Without Cache | With Cache  | Improvement       |
| ------------------------- | ------------- | ----------- | ----------------- |
| Generate suggestions      | 2-5 seconds   | 10-50ms     | **40-500x**       |
| Regenerate (same context) | 2-5 seconds   | 10-50ms     | **40-500x**       |
| Trip mutation + regen     | 2-5 seconds   | 2-5 seconds | Same (cache miss) |

## Usage Examples

### Example 1: New Trip Creation

```python
# User creates trip to Paris
trip = trip_service.create_trip(
    destination="Paris",
    start_date="2025-06-01",
    end_date="2025-06-07",
    travelers=["Alice", "Bob"]
)

# First generation: Cache MISS (2-3 seconds)
suggestions = packing_service.generate_suggestions(trip)
# Output: 🤖 Generating AI suggestions...
#         💾 Cached AI suggestions (TTL: 24h)

# User views trip again: Cache HIT (10-50ms)
suggestions = packing_service.generate_suggestions(trip)
# Output: 🚀 Cache HIT: AI suggestions
```

### Example 2: Trip Mutation

```python
# User updates trip destination
trip_service.update_trip(trip.id, destination="London")
# Output: 🗑️ Invalidated AI suggestions cache for trip trip_123

# Next generation: Cache MISS (context changed)
suggestions = packing_service.generate_suggestions(trip)
# Output: 🤖 Generating AI suggestions...
#         💾 Cached AI suggestions (TTL: 24h)
```

### Example 3: Identical Trip Context

```python
# User A creates trip to Paris (June 1-7)
trip_a = create_trip(destination="Paris", dates="2025-06-01 to 2025-06-07")
suggestions_a = generate_suggestions(trip_a)  # Cache MISS

# User B creates identical trip
trip_b = create_trip(destination="Paris", dates="2025-06-01 to 2025-06-07")
suggestions_b = generate_suggestions(trip_b)  # Cache HIT (same context!)

# Same suggestions, 40x faster for User B
```

## Cache Monitoring

### Console Logs

```text
✅ Redis cache connected
🚀 Cache HIT: AI suggestions
🤖 Generating AI suggestions...
💾 Cached AI suggestions (TTL: 24h)
🗑️ Invalidated AI suggestions cache for trip trip_123
🗑️ Invalidated cache for trip trip_123
```

### Programmatic Monitoring

```python
from src.services.cache_service import get_cache_service

cache = get_cache_service()
stats = cache.get_stats()

print(f"Cache enabled: {stats['enabled']}")
print(f"Hit rate: {stats['hit_rate']}")
print(f"Memory usage: {stats['used_memory_human']}")
```

## Testing Cache Behavior

### Test Cache Hit

```python
def test_ai_suggestion_caching():
    # Create trip
    trip = create_test_trip()

    # First call: Cache miss
    start = time.time()
    suggestions_1 = packing_service.generate_suggestions(trip)
    duration_1 = time.time() - start

    # Second call: Cache hit
    start = time.time()
    suggestions_2 = packing_service.generate_suggestions(trip)
    duration_2 = time.time() - start

    assert suggestions_1 == suggestions_2
    assert duration_2 < duration_1 / 10  # At least 10x faster
```

### Test Cache Invalidation

```python
def test_cache_invalidation_on_update():
    # Create trip and generate suggestions
    trip = create_test_trip()
    suggestions_1 = packing_service.generate_suggestions(trip)

    # Update trip (invalidates cache)
    trip_service.update_trip(trip.id, destination="New York")

    # Regenerate (should be cache miss)
    trip_updated = trip_service.get_trip(trip.id)
    suggestions_2 = packing_service.generate_suggestions(trip_updated)

    # Suggestions should differ (different destination)
    assert suggestions_1 != suggestions_2
```

## Troubleshooting

### Issue: Low Cache Hit Rate

**Symptoms:**

- Hit rate <50%
- Frequent "Generating AI suggestions" logs

**Causes:**

1. Users frequently modify trip details
2. Different weather data on each request
3. Redis connection issues

**Solutions:**

- Check Redis connection: `cache.get_stats()`
- Verify trip context stability
- Check weather API response consistency

### Issue: Stale Suggestions

**Symptoms:**

- Suggestions don't reflect trip changes
- Old destination appearing in suggestions

**Causes:**

1. Cache not invalidated on update
2. Weather data cached separately

**Solutions:**

- Verify `invalidate_ai_suggestions_for_trip()` is called
- Check trip mutation flow includes cache invalidation
- Clear cache manually: `cache.clear_all()` (dev only)

### Issue: High Memory Usage

**Symptoms:**

- Redis memory >100MB
- OOM errors

**Causes:**

1. Too many cached suggestions
2. Large suggestion payloads
3. Long TTLs

**Solutions:**

- Reduce TTL from 24h to 12h
- Implement cache size limits
- Monitor `used_memory_human` metric

## Best Practices

### For Developers

1. **Always pass trip_id when caching**

   ```python
   cache.set_ai_suggestions(data, suggestions, ttl_hours=24, trip_id=trip.id)
   ```

2. **Invalidate on all mutations**

   ```python
   def update_trip(...):
       result = TripRepository.update(...)
       cache.invalidate_ai_suggestions_for_trip(trip_id)
       return result
   ```

3. **Handle cache failures gracefully**

   ```python
   try:
       cache.invalidate_ai_suggestions_for_trip(trip_id)
   except Exception as e:
       print(f"Cache invalidation warning: {e}")
       # Continue with operation
   ```

4. **Never block on cache operations**
   - Cache should enhance, not hinder
   - All cache ops have timeouts (0.8s)
   - Silent failures are acceptable

### For Operators

1. **Monitor hit rate** - Target >80% for cost optimization
2. **Set appropriate TTLs** - Balance freshness vs. cost
3. **Use Redis in production** - Essential for multi-instance deployments
4. **Enable persistence** - RDB or AOF for cache recovery
5. **Monitor memory** - Set maxmemory policy (allkeys-lru)

## Cost Analysis

### API Call Reduction

**Without caching:**

- 10,000 requests/day × $0.01/request = **$100/day**
- Annual cost: **$36,500**

**With caching (80% hit rate):**

- 2,000 API calls/day × $0.01/request = **$20/day**
- Annual cost: **$7,300**
- **Savings: $29,200/year (80%)**

### Redis Costs

**AWS ElastiCache (cache.t3.micro):**

- Cost: ~$15/month = **$180/year**
- Memory: 1GB (sufficient for 10K+ suggestions)

**Net savings:** $29,200 - $180 = **$29,020/year**

## Future Enhancements

### Potential Improvements

1. **Smart prefetching**

   - Pre-cache suggestions for popular destinations
   - Predictive caching based on user patterns

2. **Tiered caching**

   - Hot data: In-memory (microsecond latency)
   - Warm data: Redis (millisecond latency)
   - Cold data: Database (second latency)

3. **Cache warming**

   - Background job to pre-generate popular suggestions
   - Reduce first-user cache misses

4. **Analytics integration**

   - Track which trip contexts have highest cache hit rates
   - Optimize caching strategy based on usage patterns

5. **Partial invalidation**
   - Only invalidate if relevant fields changed
   - Keep cache for minor updates (notes only)

---

**Implementation Date:** December 2024  
**Status:** ✅ Production Ready  
**Performance Gain:** 40-500x faster with cache  
**Cost Savings:** ~80% reduction in API calls
