"""
Redis caching service for blazing fast AI responses
"""

import os
import json
import hashlib
from typing import Optional, List, Dict, Any
from datetime import timedelta

# Lazy import: we'll import redis only if enabled
try:  # pragma: no cover - import path
    from redis.exceptions import RedisError  # type: ignore
except Exception:  # pragma: no cover
    class RedisError(Exception):
        pass


class NullCacheService:
    """No-op cache service used when Redis is disabled or unavailable."""

    enabled: bool = False

    def get(self, key: str) -> Optional[str]:
        return None

    def set(self, key: str, value: str, ttl_hours: int = 24) -> bool:
        return False

    def get_ai_suggestions(self, trip_data: Dict[str, Any]) -> Optional[List[str]]:
        return None

    def set_ai_suggestions(self, trip_data: Dict[str, Any], suggestions: List[str], ttl_hours: int = 24, trip_id: Optional[str] = None) -> bool:
        return False

    def get_trip(self, trip_id: str) -> Optional[Dict]:
        return None

    def set_trip(self, trip_id: str, trip_data: Dict, ttl_minutes: int = 30) -> bool:
        return False

    def invalidate_trip(self, trip_id: str) -> bool:
        return False
    
    def invalidate_ai_suggestions_for_trip(self, trip_id: str) -> bool:
        return False

    def get_stats(self) -> Dict[str, Any]:
        return {"enabled": False}

    def clear_all(self) -> bool:
        return False


class CacheService:
    """
    Redis-based caching service with graceful disable and NullCache fallback.

    Redis is enabled only if the USE_REDIS environment variable is set to 'true', '1', or 'yes'.
    All other disabling logic is handled via this flag for clarity and consistency.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = None  # type: ignore
        self.enabled = False

        # Single source of truth: USE_REDIS env variable
        use_redis = os.getenv('USE_REDIS', 'false').lower() in ['true', '1', 'yes']
        if not use_redis:
            print("ℹ️ Redis disabled via USE_REDIS flag (Cache: OFF)")
            return

        try:
            import redis  # type: ignore
        except ImportError:
            print("⚠️ redis package not installed - caching disabled")
            return

        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=float(os.getenv('REDIS_CONNECT_TIMEOUT', '0.8')),
                socket_timeout=float(os.getenv('REDIS_SOCKET_TIMEOUT', '0.8')),
                retry_on_timeout=False,
                max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
            )
            self.redis_client.ping()
            self.enabled = True
            print("✅ Redis cache connected")
        except Exception as e:
            print(f"⚠️ Redis unavailable, caching disabled: {type(e).__name__}: {e}")
            self.redis_client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Generate deterministic cache key from data"""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        hash_value = hashlib.md5(sorted_data.encode()).hexdigest()
        return f"{prefix}:{hash_value}"
    
    def get(self, key: str) -> Optional[str]:
        """Generic get method for any cached value"""
        if not self.enabled or self.redis_client is None:
            return None
        try:  # type: ignore[attr-defined]
            return self.redis_client.get(key)  # type: ignore[attr-defined]
        except RedisError as e:
            print(f"Cache read error: {e}")
            return None
    
    def set(self, key: str, value: str, ttl_hours: int = 24) -> bool:
        """Generic set method with TTL in hours"""
        if not self.enabled or self.redis_client is None:
            return False
        try:  # type: ignore[attr-defined]
            self.redis_client.setex(key, timedelta(hours=ttl_hours), value)  # type: ignore[attr-defined]
            return True
        except RedisError as e:
            print(f"Cache write error: {e}")
            return False
    
    def get_ai_suggestions(self, trip_data: Dict[str, Any]) -> Optional[List[str]]:
        """Get cached AI packing suggestions"""
        if not self.enabled or self.redis_client is None:
            return None
        try:  # type: ignore[attr-defined]
            key = self._generate_key("ai_suggestions", trip_data)
            cached = self.redis_client.get(key)  # type: ignore[attr-defined]
            if cached:
                print("🚀 Cache HIT: AI suggestions")
                return json.loads(str(cached))
            return None
        except RedisError as e:
            print(f"Cache read error: {e}")
            return None
    
    def set_ai_suggestions(
        self, 
        trip_data: Dict[str, Any], 
        suggestions: List[str],
        ttl_hours: int = 24,
        trip_id: Optional[str] = None
    ) -> bool:
        """Cache AI packing suggestions with TTL and optional trip_id mapping"""
        if not self.enabled or self.redis_client is None:
            return False
        try:  # type: ignore[attr-defined]
            key = self._generate_key("ai_suggestions", trip_data)
            value = json.dumps(suggestions)
            self.redis_client.setex(key, timedelta(hours=ttl_hours), value)  # type: ignore[attr-defined]
            
            # Store mapping from trip_id to cache key for easy invalidation
            if trip_id:
                mapping_key = f"ai_trip_mapping:{trip_id}"
                self.redis_client.setex(mapping_key, timedelta(hours=ttl_hours), key)  # type: ignore[attr-defined]
            
            print(f"💾 Cached AI suggestions (TTL: {ttl_hours}h)")
            return True
        except RedisError as e:
            print(f"Cache write error: {e}")
            return False
    
    def get_trip(self, trip_id: str) -> Optional[Dict]:
        """Get cached trip data"""
        if not self.enabled or self.redis_client is None:
            return None
        try:  # type: ignore[attr-defined]
            key = f"trip:{trip_id}"
            cached = self.redis_client.get(key)  # type: ignore[attr-defined]
            if cached:
                print(f"🚀 Cache HIT: Trip {trip_id}")
                return json.loads(str(cached))
            return None
        except RedisError as e:
            print(f"Cache read error: {e}")
            return None
    
    def set_trip(self, trip_id: str, trip_data: Dict, ttl_minutes: int = 30) -> bool:
        """Cache trip data with short TTL"""
        if not self.enabled or self.redis_client is None:
            return False
        try:  # type: ignore[attr-defined]
            key = f"trip:{trip_id}"
            value = json.dumps(trip_data)
            self.redis_client.setex(key, timedelta(minutes=ttl_minutes), value)  # type: ignore[attr-defined]
            return True
        except RedisError as e:
            print(f"Cache write error: {e}")
            return False
    
    def invalidate_trip(self, trip_id: str) -> bool:
        """Invalidate trip cache when data changes"""
        if not self.enabled or self.redis_client is None:
            return False
        try:  # type: ignore[attr-defined]
            key = f"trip:{trip_id}"
            self.redis_client.delete(key)  # type: ignore[attr-defined]
            print(f"🗑️  Invalidated cache for trip {trip_id}")
            return True
        except RedisError as e:
            print(f"Cache delete error: {e}")
            return False
    
    def invalidate_ai_suggestions_for_trip(self, trip_id: str) -> bool:
        """Invalidate AI suggestions cache for a specific trip"""
        if not self.enabled or self.redis_client is None:
            return False
        try:  # type: ignore[attr-defined]
            # Delete the mapping from trip_id to cache key
            mapping_key = f"ai_trip_mapping:{trip_id}"
            cache_key = self.redis_client.get(mapping_key)  # type: ignore[attr-defined]
            
            if cache_key:
                self.redis_client.delete(cache_key)  # type: ignore[attr-defined]
                self.redis_client.delete(mapping_key)  # type: ignore[attr-defined]
                print(f"🗑️  Invalidated AI suggestions cache for trip {trip_id}")
                return True
            return False
        except RedisError as e:
            print(f"Cache invalidation error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or self.redis_client is None:
            return {"enabled": False}
        try:  # type: ignore[attr-defined]
            info = self.redis_client.info()  # type: ignore[attr-defined]
            # Ensure info is a dict, not an awaitable
            if hasattr(info, '__await__'):
                return {"enabled": False, "error": "Async Redis client detected, use sync client"}
            
            # Ensure info is a dictionary before accessing attributes
            if not isinstance(info, dict):
                return {"enabled": False, "error": "Redis info() returned non-dict type"}
                
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except RedisError as e:
            return {"enabled": False, "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> str:
        """Calculate cache hit rate percentage"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        if total == 0:
            return "0%"
        rate = (hits / total) * 100
        return f"{rate:.1f}%"
    
    def clear_all(self) -> bool:
        """Clear all cached data (use with caution!)"""
        if not self.enabled or self.redis_client is None:
            return False
        try:  # type: ignore[attr-defined]
            self.redis_client.flushdb()  # type: ignore[attr-defined]
            print("🗑️  Cache cleared")
            return True
        except RedisError as e:
            print(f"Cache clear error: {e}")
            return False


# Singleton instance
_cache_instance: Optional[CacheService] = None


def get_cache_service(redis_url: Optional[str] = None) -> CacheService:
    """Get or create cache service singleton"""
    global _cache_instance
    if _cache_instance is None:
        if redis_url is None:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        service = CacheService(redis_url)
        if not service.enabled:
            # Use Null object to avoid repeated construction attempts
            _cache_instance = NullCacheService()  # type: ignore
        else:
            _cache_instance = service
    return _cache_instance  # type: ignore
