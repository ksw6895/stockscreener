"""Caching layer for API responses with TTL support and multiple backends."""

import json
import hashlib
import time
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional, Dict
import logging
import pickle
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, expires_at: float) -> None:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        pass
    
    @abstractmethod
    def clear(self) -> None:
        pass


class InMemoryBackend(CacheBackend):
    """In-memory cache backend."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if time.time() < self._cache[key]['expires_at']:
                return self._cache[key]['data']
            else:
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, expires_at: float) -> None:
        self._cache[key] = {
            'data': value,
            'expires_at': expires_at
        }
    
    def delete(self, key: str) -> None:
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        self._cache.clear()


class FileBackend(CacheBackend):
    """File-based cache backend."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.cache"
    
    async def get(self, key: str) -> Optional[Any]:
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            if time.time() < cache_data['expires_at']:
                return cache_data['data']
            else:
                cache_path.unlink()
                return None
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, expires_at: float) -> None:
        cache_path = self._get_cache_path(key)
        cache_data = {
            'data': value,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            logger.warning(f"Error writing cache: {e}")
    
    def delete(self, key: str) -> None:
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
    
    def clear(self) -> None:
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()


class SQLiteBackend(CacheBackend):
    """SQLite-based cache backend."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    data BLOB,
                    expires_at REAL,
                    created_at REAL
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)')
    
    async def get(self, key: str) -> Optional[Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT data, expires_at FROM cache WHERE key = ?',
                (key,)
            )
            row = cursor.fetchone()
            if row:
                data_blob, expires_at = row
                if time.time() < expires_at:
                    return pickle.loads(data_blob)
                else:
                    conn.execute('DELETE FROM cache WHERE key = ?', (key,))
        return None
    
    async def set(self, key: str, value: Any, expires_at: float) -> None:
        data_blob = pickle.dumps(value)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT OR REPLACE INTO cache (key, data, expires_at, created_at) VALUES (?, ?, ?, ?)',
                (key, data_blob, expires_at, time.time())
            )
    
    def delete(self, key: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM cache WHERE key = ?', (key,))
    
    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM cache')
    
    def cleanup_expired(self) -> None:
        """Remove expired entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM cache WHERE expires_at < ?', (time.time(),))


class CacheManager:
    """Manages cached API responses with TTL and multiple backend support."""
    
    def __init__(self, backend: str = "file", cache_dir: str = ".cache", 
                 default_ttl: int = 3600):
        """
        Initialize cache manager.
        
        Args:
            backend: Cache backend type ('memory', 'file', 'sqlite')
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.backend_type = backend
        
        # Initialize backend
        if backend == 'memory':
            self.backend = InMemoryBackend()
        elif backend == 'file':
            self.backend = FileBackend(self.cache_dir)
        elif backend == 'sqlite':
            db_path = str(self.cache_dir / 'cache.db')
            self.backend = SQLiteBackend(db_path)
        else:
            raise ValueError(f"Unknown backend: {backend}")
        
        # Endpoint-specific TTLs (in seconds)
        self.ttl_config = {
            'symbol': 86400,  # 24 hours for symbol lists
            'profile': 86400,  # 24 hours for company profiles
            'sector': 86400,  # 24 hours for sector data
            'financial-statement': 3600,  # 1 hour for financials
            'key-metrics': 3600,  # 1 hour for metrics
            'ratios': 3600,  # 1 hour for ratios
            'earnings': 900,  # 15 minutes for earnings
            'quote': 300,  # 5 minutes for quotes
            'historical-price-full': 300,  # 5 minutes for historical prices (shorter for real-time updates)
            'analyst': 7200,  # 2 hours for analyst estimates
            'esg': 86400,  # 24 hours for ESG scores
        }
        
        logger.info(f"Cache initialized with {backend} backend")
        
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        # Include full URL with all parameters (including dates) in cache key
        # This ensures different date ranges get different cache entries
        return hashlib.md5(url.encode()).hexdigest()
        
    def _get_ttl_for_url(self, url: str) -> int:
        """Determine TTL based on URL endpoint."""
        # Special handling for historical data with date ranges
        if 'historical-price-full' in url:
            # If it has date parameters (from/to), use longer TTL
            if 'from=' in url and 'to=' in url:
                return 86400  # 24 hours for historical data with specific date range
            else:
                return 300  # 5 minutes for latest prices without date range
        
        for endpoint, ttl in self.ttl_config.items():
            if endpoint in url:
                return ttl
        return self.default_ttl
        
    async def get(self, url: str) -> Optional[Any]:
        """
        Get cached response for URL.
        
        Args:
            url: The URL to look up
            
        Returns:
            Cached data if valid, None otherwise
        """
        cache_key = self._get_cache_key(url)
        result = await self.backend.get(cache_key)
        if result is not None:
            logger.debug(f"Cache hit for {url}")
        return result
            
    async def set(self, url: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        Cache response for URL.
        
        Args:
            url: The URL to cache
            data: The data to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        if data is None:
            return  # Don't cache None responses
            
        cache_key = self._get_cache_key(url)
        
        if ttl is None:
            ttl = self._get_ttl_for_url(url)
        
        expires_at = time.time() + ttl
        await self.backend.set(cache_key, data, expires_at)
        logger.debug(f"Cached response for {url} (TTL: {ttl}s)")
            
    def clear(self) -> None:
        """Clear all cached entries."""
        self.backend.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self) -> None:
        """Clean up expired entries (for SQLite backend)."""
        if isinstance(self.backend, SQLiteBackend):
            self.backend.cleanup_expired()
            logger.info("Cleaned up expired cache entries")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'backend': self.backend_type,
            'cache_dir': str(self.cache_dir)
        }
        
        if isinstance(self.backend, FileBackend):
            total_files = 0
            total_size = 0
            expired_count = 0
            
            for cache_file in self.cache_dir.glob("*.cache"):
                total_files += 1
                total_size += cache_file.stat().st_size
                
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)
                    if time.time() > cache_data['expires_at']:
                        expired_count += 1
                except:
                    pass
            
            stats.update({
                'total_files': total_files,
                'total_size_mb': total_size / (1024 * 1024),
                'expired_count': expired_count
            })
        elif isinstance(self.backend, SQLiteBackend):
            with sqlite3.connect(self.backend.db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM cache')
                total_entries = cursor.fetchone()[0]
                
                cursor = conn.execute('SELECT COUNT(*) FROM cache WHERE expires_at < ?', (time.time(),))
                expired_count = cursor.fetchone()[0]
                
                stats.update({
                    'total_entries': total_entries,
                    'expired_count': expired_count
            })
        elif isinstance(self.backend, InMemoryBackend):
            stats.update({
                'total_entries': len(self.backend._cache),
                'expired_count': sum(1 for v in self.backend._cache.values() 
                                   if time.time() >= v['expires_at'])
            })
                
        return stats


# Global cache instance
cache_manager = CacheManager()