# AI Suggestion Caching & Invalidation

## Overview

AI-generated packing suggestions are cached using Redis to dramatically reduce API calls and improve response times from **2-5 seconds** to **10-50ms** (cache hits). The caching system intelligently tracks trip context and invalidates caches when relevant data changes.

## Cache Key Strategy

### Context-Based Cache Keys

AI suggestions are cached based on **all factors that affect packing recommendations**:

```python
cache_key_data = {
    "destination": "Paris",           # Location affects climate, culture, activities
    "start_date": "2025-06-15",       # Season/time of year affects weather needs
    "duration": 8,                     # Trip length determines quantities
    "travel_style": "leisure",         # Business/adventure/luxury affects items
    "transportation": "flight",        # Luggage constraints differ by transport
    "activities": ["museums", "dining"], # Sorted for consistent hashing
    "weather": "Sunny, 20-25°C",       # Temperature affects clothing choices
    "travelers": ["Alice", "Bob"]      # Sorted for consistent hashing
}
```

**Why these fields?**

- **Destination + Season**: Paris in June needs different items than Paris in December
- **Duration**: 3-day trip vs. 3-week trip requires different quantities
- **Travel Style**: Business trip needs suits; adventure trip needs hiking gear
- **Transportation**: Flight restrictions vs. road trip flexibility
- **Activities**: Museum visits need different items than beach days
- **Weather**: Temperature directly affects clothing selection
- **Travelers**: Individual names for potential personalization (future)

### Cache Key Generation

Cache keys are generated using **MD5 hashing** of sorted JSON data:

```python
# From CacheService._generate_key()
sorted_data = json.dumps(trip_data, sort_keys=True)
hash_value = hashlib.md5(sorted_data.encode()).hexdigest()
cache_key = f"ai_suggestions:{hash_value}"  # e.g., "ai_suggestions:a1b2c3d4..."
```

**Sorted arrays** (activities, travelers) ensure consistent hashing regardless of input order.

## Cache Invalidation Strategy

### Automatic Invalidation Triggers

#### 1. Trip Updates (Any Context Change)

**When**: `TripService.update_trip()` called with any parameter  
**What's Invalidated**:

- AI suggestions cache (trip context changed)
- Trip metadata cache (basic trip data changed)

```python
# Example: Changing destination invalidates AI cache
trip_service.update_trip(trip_id, destination="London")
# → invalidate_ai_suggestions_for_trip(trip_id)
# → invalidate_trip(trip_id)
```

**Why**: Any change to destination, dates, travelers, style, transportation, activities, or weather affects packing recommendations.

#### 2. Trip Deletion

**When**: `TripService.delete_trip()` called  
**What's Invalidated**:

- AI suggestions cache (trip no longer exists)
- Trip metadata cache (cleanup)

```python
trip_service.delete_trip(trip_id)
# → invalidate_ai_suggestions_for_trip(trip_id)  # Before deletion
# → invalidate_trip(trip_id)
# → Delete trip from database
```

**Why**: Prevent stale cache entries for deleted trips.

### Cache Mapping Architecture

**Problem**: Cache keys are MD5 hashes of trip data. How do we invalidate by `trip_id`?

**Solution**: Two-tier caching system:

1. **AI Suggestions Cache**: `ai_suggestions:{hash}` → `["item1", "item2", ...]`
2. **Trip Mapping Cache**: `ai_trip_mapping:{trip_id}` → `ai_suggestions:{hash}`

```python
# When caching AI suggestions
cache.set_ai_suggestions(trip_data, suggestions, ttl_hours=24, trip_id=trip.id)
# → Sets: ai_suggestions:a1b2c3d4 → ["1 x Passport", ...]
# → Sets: ai_trip_mapping:trip_123 → "ai_suggestions:a1b2c3d4"

# When invalidating
cache.invalidate_ai_suggestions_for_trip(trip_id)
# → Reads: ai_trip_mapping:trip_123 → "ai_suggestions:a1b2c3d4"
# → Deletes: ai_suggestions:a1b2c3d4
# → Deletes: ai_trip_mapping:trip_123
```

This allows **instant invalidation** by `trip_id` without needing to reconstruct the cache key.

## Performance Impact

### Cache Hit Performance

- **Cache HIT**: 10-50ms (Redis lookup)
- **Cache MISS**: 2-5 seconds (Gemini API call + processing)
- **Speedup**: ~50-200x faster on cache hits

### Cache Hit Rates (Expected)

- **New trips**: 0% (first-time generation)
- **Repeated views**: ~70-80% (same trip viewed multiple times)
- **Template trips**: ~90% (popular destinations/styles)

### TTL (Time-To-Live)

- **AI Suggestions**: 24 hours (suggestions remain valid for typical planning period)
- **Trip Mapping**: 24 hours (matches AI suggestion TTL)
- **Trip Metadata**: 30 minutes (short-lived, frequently changing)

## Cache Consistency Guarantees

### Strong Consistency on Mutations

✅ **Trip updates invalidate cache immediately**  
✅ **Trip deletions cleanup all associated caches**  
✅ **No stale AI suggestions after context changes**

### Eventual Consistency for Non-Mutating Changes

⚠️ **Weather updates** (background fetch) trigger immediate invalidation  
⚠️ **Manual regeneration** (`/regenerate` endpoint) bypasses cache and forces fresh generation

## Testing Coverage

Comprehensive test suite in `tests/unit/test_ai_caching.py`:

### Test Categories

1. **Cache Key Generation** (6 tests)

   - ✅ All context fields included in cache key
   - ✅ Different destinations produce different keys
   - ✅ Different dates produce different keys (seasonal)
   - ✅ Different travelers produce different keys
   - ✅ Activity order doesn't affect key (sorted)
   - ✅ Traveler order doesn't affect key (sorted)

2. **Cache Invalidation** (4 tests)

   - ✅ Trip updates trigger invalidation
   - ✅ Trip deletions trigger invalidation
   - ✅ Cache miss generates new suggestions
   - ✅ Cache hit skips AI generation

3. **Performance & Reliability** (3 tests)
   - ✅ Cache disabled still works (graceful degradation)
   - ✅ Cache keys are deterministic
   - ✅ Different trips produce different keys

Run tests: `pytest tests/unit/test_ai_caching.py -v`

## Monitoring & Debugging

### Cache Hit/Miss Logging

```python
# Cache HIT (fast path)
⚡ Cache HIT for trip trip_123: Paris (8d, 2 travelers)

# Cache MISS (slow path)
💭 Cache MISS for trip trip_123: Generating fresh AI suggestions...
🤖 Generating AI suggestions...
💾 Cached 15 suggestions for trip trip_123 (TTL: 24h)
```

### Cache Invalidation Logging

```python
# Trip update invalidation
🗑️  Invalidated AI cache for trip trip_123 - fresh suggestions will be generated on next request
🗑️  Invalidated trip cache for trip_123

# No cached suggestions (info only)
ℹ️  No cached AI suggestions found for trip trip_123
```

### Cache Statistics

Get cache stats via `CacheService.get_stats()`:

```python
{
    "enabled": True,
    "connected_clients": 5,
    "used_memory_human": "2.1MB",
    "total_commands_processed": 1234,
    "keyspace_hits": 850,
    "keyspace_misses": 384,
    "hit_rate": "68.9%"
}
```

## Fallback Behavior

### Redis Unavailable

If Redis is down or disabled (`USE_REDIS=false`):

1. ✅ App continues to function normally
2. ✅ AI suggestions generated on every request (no caching)
3. ✅ Performance degrades to ~2-5s per generation
4. ⚠️ Increased Gemini API usage (rate limiting may apply)

### Gemini API Unavailable

If Gemini API fails or is disabled:

1. ✅ App falls back to **mock suggestions** (rule-based)
2. ✅ Mock suggestions consider duration, travelers, travel style
3. ⚠️ Mock suggestions less personalized than AI-generated

## Best Practices

### When to Invalidate Cache Manually

Use `/trip/<trip_id>/regenerate` endpoint when:

- User edits trip details (automatic)
- Weather data updates (automatic)
- User explicitly requests fresh suggestions (manual button)

### When NOT to Invalidate Cache

Don't invalidate on:

- Packing item toggles (packed/unpacked status)
- Adding/removing individual packing items
- Viewing trip details
- PDF exports

**Reason**: AI suggestions are **input** to packing list, not dependent on packing list state.

### Cache Warming (Future)

Consider pre-generating suggestions for:

- Popular destinations (Paris, London, Tokyo)
- Common travel styles (leisure, business)
- Standard durations (3-day, 7-day, 14-day trips)

## Architecture Diagram

```flow-chart
┌─────────────────────────────────────────────────────┐
│              User Request                           │
│  "Generate packing list for Paris trip"             │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│          AIService.generate_packing_suggestions()   │
│  • Builds cache key from trip context               │
│  • Checks Redis for cached suggestions              │
└─────────────────┬───────────────────────────────────┘
                  │
           ┌──────┴──────┐
           │             │
     Cache HIT?    Cache MISS?
           │             │
           ▼             ▼
┌────────────────┐  ┌──────────────────────────────┐
│ Redis Cache    │  │ Gemini API Call              │
│ 10-50ms ⚡     │  │ 2-5 seconds 🤖               │
│ Return cached  │  │ • Generate fresh suggestions │
│ suggestions    │  │ • Parse response             │
└────────────────┘  │ • Cache results (24h TTL)    │
                    │ • Store trip_id mapping      │
                    └──────────────────────────────┘

Trip Update/Delete → invalidate_ai_suggestions_for_trip()
                  → Deletes both cache entries
```

## Related Documentation

- [AI Suggestions Feature](./ai-suggestions.md) - How AI generates suggestions
- [Redis Cache Service](../architecture/performance.md#redis-caching) - Cache infrastructure
- [Weather Integration](./weather-integration.md) - Weather data caching
- [Performance Optimization](../architecture/performance.md) - Overall performance strategy
