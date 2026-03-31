# src/utils/cache.py
"""
Caching layer for embeddings and query results.
Reduces API calls and improves performance.
"""
import hashlib
import time
from typing import Any, Optional, Dict
from functools import lru_cache
from config.constants import CacheConfig
from src.utils.logging_utils import get_logger

logger = get_logger("cache")


class TTLCache:
    """
    Time-to-live cache with automatic expiration.
    Thread-safe simple implementation.
    """
    
    def __init__(self, ttl_seconds: int = CacheConfig.CACHE_TTL_SECONDS):
        """
        Initialize TTL cache.
        
        Args:
            ttl_seconds: Time-to-live for cached items in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._hits = 0
        self._misses = 0
        logger.info("TTL Cache initialized", ttl_seconds=ttl_seconds)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            logger.debug("Cache miss", key=key[:50])
            return None
        
        value, timestamp = self._cache[key]
        
        # Check if expired
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[key]
            self._misses += 1
            logger.debug("Cache expired", key=key[:50])
            return None
        
        self._hits += 1
        logger.debug("Cache hit", key=key[:50])
        return value
    
    def set(self, key: str, value: Any):
        """
        Set item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (value, time.time())
        logger.debug("Cache set", key=key[:50])
        
        # Cleanup if cache is too large
        if len(self._cache) > CacheConfig.MAX_CACHE_SIZE:
            self._cleanup_oldest()
    
    def _cleanup_oldest(self):
        """Remove oldest 10% of cache entries"""
        num_to_remove = max(1, len(self._cache) // 10)
        
        # Sort by timestamp and remove oldest
        sorted_items = sorted(
            self._cache.items(),
            key=lambda x: x[1][1]  # Sort by timestamp
        )
        
        for key, _ in sorted_items[:num_to_remove]:
            del self._cache[key]
        
        logger.debug("Cache cleanup", removed=num_to_remove)
    
    def clear(self):
        """Clear all cache entries"""
        size = len(self._cache)
        self._cache.clear()
        logger.info("Cache cleared", entries_removed=size)
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl_seconds
        }


class QueryCache:
    """
    Specialized cache for query results.
    Uses content-based hashing for keys.
    """
    
    def __init__(self):
        self._cache = TTLCache(ttl_seconds=CacheConfig.CACHE_TTL_SECONDS)
        logger.info("Query cache initialized")
    
    @staticmethod
    def _hash_query(query: str, context_preview: str = "") -> str:
        """
        Create hash key from query and context.
        
        Args:
            query: User query
            context_preview: Preview of context (optional)
            
        Returns:
            Hash string to use as cache key
        """
        # Normalize query
        normalized = query.lower().strip()
        
        # Create hash
        content = f"{normalized}:{context_preview}"
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()
    
    def get(self, query: str, context_preview: str = "") -> Optional[str]:
        """
        Get cached response for query.
        
        Args:
            query: User query
            context_preview: Preview of context used
            
        Returns:
            Cached response or None
        """
        key = self._hash_query(query, context_preview)
        result = self._cache.get(key)
        
        if result:
            logger.info("Query cache hit", query=query[:50])
        
        return result
    
    def set(self, query: str, response: str, context_preview: str = ""):
        """
        Cache response for query.
        
        Args:
            query: User query
            response: LLM response to cache
            context_preview: Preview of context used
        """
        if not CacheConfig.ENABLE_QUERY_CACHE:
            return
        
        key = self._hash_query(query, context_preview)
        self._cache.set(key, response)
        logger.debug("Query cached", query=query[:50])
    
    def clear(self):
        """Clear query cache"""
        self._cache.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return self._cache.get_stats()


class EmbeddingCache:
    """
    Cache for text embeddings.
    Useful when re-embedding the same text multiple times.
    """
    
    def __init__(self):
        self._cache = TTLCache(ttl_seconds=CacheConfig.CACHE_TTL_SECONDS * 2)  # Longer TTL
        logger.info("Embedding cache initialized")
    
    @staticmethod
    def _hash_text(text: str) -> str:
        """
        Create hash key from text.
        
        Args:
            text: Text to hash
            
        Returns:
            Hash string
        """
        hash_obj = hashlib.sha256(text.encode())
        return hash_obj.hexdigest()
    
    def get(self, text: str) -> Optional[list]:
        """
        Get cached embedding for text.
        
        Args:
            text: Text to get embedding for
            
        Returns:
            Cached embedding vector or None
        """
        if not CacheConfig.ENABLE_EMBEDDING_CACHE:
            return None
        
        key = self._hash_text(text)
        return self._cache.get(key)
    
    def set(self, text: str, embedding: list):
        """
        Cache embedding for text.
        
        Args:
            text: Text that was embedded
            embedding: Embedding vector
        """
        if not CacheConfig.ENABLE_EMBEDDING_CACHE:
            return
        
        key = self._hash_text(text)
        self._cache.set(key, embedding)
    
    def clear(self):
        """Clear embedding cache"""
        self._cache.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return self._cache.get_stats()


# Global cache instances
query_cache = QueryCache()
embedding_cache = EmbeddingCache()


# Decorators for easy caching
def cache_query(func):
    """
    Decorator to cache query results.
    
    Usage:
        @cache_query
        def my_query_function(query: str) -> str:
            # expensive operation
            return result
    """
    def wrapper(query: str, *args, **kwargs):
        # Try to get from cache
        cached = query_cache.get(query)
        if cached is not None:
            return cached
        
        # Execute function
        result = func(query, *args, **kwargs)
        
        # Cache result
        if result:
            query_cache.set(query, result)
        
        return result
    
    return wrapper
