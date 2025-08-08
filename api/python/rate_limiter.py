"""Adaptive rate limiter that maximizes API throughput."""

import asyncio
import time
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that learns from API responses.
    Maximizes throughput while handling rate limit errors gracefully.
    """
    
    def __init__(self, initial_rate: Optional[int] = None):
        """
        Initialize adaptive rate limiter.
        
        Args:
            initial_rate: Initial requests per second (None = unlimited)
        """
        self.current_rate = initial_rate  # None means no limit
        self.last_429_time = None
        self.backoff_until = None
        self.request_times = []
        self.window_size = 60  # Track last 60 seconds
        self._lock = asyncio.Lock()
        
    async def acquire(self) -> None:
        """Wait if we're in backoff period."""
        async with self._lock:
            # Check if we're in backoff
            if self.backoff_until and time.time() < self.backoff_until:
                wait_time = self.backoff_until - time.time()
                logger.info(f"Rate limited, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self.backoff_until = None
                
            # Clean old request times
            cutoff = time.time() - self.window_size
            self.request_times = [t for t in self.request_times if t > cutoff]
            
            # Record this request
            self.request_times.append(time.time())
            
    async def handle_response(self, status: int, headers: Dict[str, Any]) -> None:
        """
        Handle API response to adapt rate.
        
        Args:
            status: HTTP status code
            headers: Response headers
        """
        async with self._lock:
            if status == 429:  # Rate limited
                # Check for Retry-After header
                retry_after = headers.get('Retry-After', headers.get('retry-after'))
                if retry_after:
                    try:
                        # Could be seconds or HTTP date
                        if retry_after.isdigit():
                            wait_seconds = int(retry_after)
                        else:
                            wait_seconds = 60  # Default fallback
                    except:
                        wait_seconds = 60
                else:
                    # Exponential backoff
                    if self.last_429_time:
                        time_since_last = time.time() - self.last_429_time
                        if time_since_last < 10:
                            wait_seconds = min(120, 30)  # Quick succession, longer wait
                        else:
                            wait_seconds = 10
                    else:
                        wait_seconds = 10
                        
                self.backoff_until = time.time() + wait_seconds
                self.last_429_time = time.time()
                logger.warning(f"Rate limited! Backing off for {wait_seconds}s")
                
            elif status == 200:
                # Success - check rate limit headers if provided
                remaining = headers.get('X-RateLimit-Remaining', headers.get('x-ratelimit-remaining'))
                reset_time = headers.get('X-RateLimit-Reset', headers.get('x-ratelimit-reset'))
                
                if remaining and reset_time:
                    try:
                        remaining = int(remaining)
                        reset_timestamp = int(reset_time)
                        
                        if remaining < 10:  # Getting close to limit
                            seconds_until_reset = max(1, reset_timestamp - time.time())
                            # Slow down to use remaining requests over the reset period
                            delay = seconds_until_reset / max(1, remaining)
                            logger.info(f"Approaching rate limit: {remaining} requests remaining, slowing to {delay:.1f}s between requests")
                            await asyncio.sleep(delay)
                    except:
                        pass  # Ignore parsing errors
                        
    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limiter statistics."""
        cutoff = time.time() - self.window_size
        recent_requests = [t for t in self.request_times if t > cutoff]
        
        return {
            'requests_last_minute': len(recent_requests),
            'current_rps': len(recent_requests) / min(60, time.time() - min(recent_requests)) if recent_requests else 0,
            'in_backoff': self.backoff_until and time.time() < self.backoff_until,
            'backoff_remaining': max(0, self.backoff_until - time.time()) if self.backoff_until else 0
        }


# Global instance - no initial limit, will adapt based on API responses
adaptive_limiter = AdaptiveRateLimiter()

async def rate_limit() -> None:
    """Apply adaptive rate limiting."""
    await adaptive_limiter.acquire()