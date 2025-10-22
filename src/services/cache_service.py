"""
Redis caching service for blazing fast AI responses
"""

import os
import json
import hashlib
from typing import Optional, List, Dict, Any
from datetime import timedelta
import redis
from redis.exceptions import RedisError


class CacheService:
    """Redis-based caching service for AI suggestions and trip data"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize Redis connection with connection pooling"""
        self.redis_client = None
        self.enabled = False
        
        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=1,  # Very short timeout
                socket_timeout=1,          # Very short timeout
                retry_on_timeout=False,    # Don't retry on timeout
                max_connections=50         # Connection pool for concurrent requests
            )
            # Test connection with its own try-catch to handle deep Redis exceptions
            try:
                self.redis_client.ping()
                self.enabled = True
                print("✅ Redis cache connected")
            except Exception as ping_error:
                # Ping failed, disable caching
                raise ConnectionError(f"Redis ping failed: {ping_error}")
                
        except Exception as e:
            print(f"⚠️  Redis unavailable, caching disabled: {type(e).__name__}")
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
        if not self.enabled:
            return None
        
        try:
            return self.redis_client.get(key)
        except RedisError as e:
            print(f"Cache read error: {e}")
            return None
    
    def set(self, key: str, value: str, ttl_hours: int = 24) -> bool:
        """Generic set method with TTL in hours"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.setex(
                key,
                timedelta(hours=ttl_hours),
                value
            )
            return True
        except RedisError as e:
            print(f"Cache write error: {e}")
            return False
    
    def get_ai_suggestions(self, trip_data: Dict[str, Any]) -> Optional[List[Dict]]:
        """Get cached AI packing suggestions"""
        if not self.enabled:
            return None
        
        try:
            key = self._generate_key("ai_suggestions", trip_data)
            cached = self.redis_client.get(key)
            if cached:
                print(f"🚀 Cache HIT: AI suggestions")
                return json.loads(cached)
            return None
        except RedisError as e:
            print(f"Cache read error: {e}")
            return None
    
    def set_ai_suggestions(
        self, 
        trip_data: Dict[str, Any], 
        suggestions: List[Dict],
        ttl_hours: int = 24
    ) -> bool:
        """Cache AI packing suggestions with TTL"""
        if not self.enabled:
            return False
        
        try:
            key = self._generate_key("ai_suggestions", trip_data)
            value = json.dumps(suggestions)
            self.redis_client.setex(
                key, 
                timedelta(hours=ttl_hours), 
                value
            )
            print(f"💾 Cached AI suggestions (TTL: {ttl_hours}h)")
            return True
        except RedisError as e:
            print(f"Cache write error: {e}")
            return False
    
    def get_trip(self, trip_id: str) -> Optional[Dict]:
        """Get cached trip data"""
        if not self.enabled:
            return None
        
        try:
            key = f"trip:{trip_id}"
            cached = self.redis_client.get(key)
            if cached:
                print(f"🚀 Cache HIT: Trip {trip_id}")
                return json.loads(cached)
            return None
        except RedisError as e:
            print(f"Cache read error: {e}")
            return None
    
    def set_trip(self, trip_id: str, trip_data: Dict, ttl_minutes: int = 30) -> bool:
        """Cache trip data with short TTL"""
        if not self.enabled:
            return False
        
        try:
            key = f"trip:{trip_id}"
            value = json.dumps(trip_data)
            self.redis_client.setex(
                key,
                timedelta(minutes=ttl_minutes),
                value
            )
            return True
        except RedisError as e:
            print(f"Cache write error: {e}")
            return False
    
    def invalidate_trip(self, trip_id: str) -> bool:
        """Invalidate trip cache when data changes"""
        if not self.enabled:
            return False
        
        try:
            key = f"trip:{trip_id}"
            self.redis_client.delete(key)
            print(f"🗑️  Invalidated cache for trip {trip_id}")
            return True
        except RedisError as e:
            print(f"Cache delete error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
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
        if not self.enabled:
            return False
        
        try:
            self.redis_client.flushdb()
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
        # Try to get Redis URL from environment, fallback to default
        if redis_url is None:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        _cache_instance = CacheService(redis_url)
    return _cache_instance
