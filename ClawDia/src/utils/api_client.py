"""
api_client.py — Generic retry / rate-limit / fallback utilities for Clawdia API wrappers.

Patterns extracted from ClaudeHipHopperList (Genius API integration).

Usage:
    from api_client import retry, api_request, fallback_search

    @retry(max_attempts=3, delay=2.0, backoff=2.0)
    def fetch_data(url):
        return requests.get(url).json()
"""

import time
import random
import functools
import logging
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """Decorator: retry a function with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_attempts:
                        if on_retry:
                            on_retry(attempt, e)
                        log.warning(
                            "Attempt %d/%d failed for %s: %s. Retrying in %.1fs...",
                            attempt, max_attempts, func.__name__, e, current_delay,
                        )
                        time.sleep(current_delay + random.uniform(0, 0.5))
                        current_delay *= backoff
            raise last_exc
        return wrapper
    return decorator


def fallback_search(
    queries: list[str],
    search_fn: Callable[[str], Any],
    validate_fn: Optional[Callable[[Any], bool]] = None,
) -> Any:
    """Try multiple search queries, returning first valid result."""
    for query in queries:
        try:
            result = search_fn(query)
            if validate_fn is None or validate_fn(result):
                return result
        except Exception as e:
            log.debug("Fallback query '%s' failed: %s", query, e)
            continue
    return None


def rate_limited(max_per_minute: int = 60):
    """Decorator: rate-limit a function to N calls per minute."""
    import threading

    class TokenBucket:
        def __init__(self, rate):
            self.rate = rate
            self.tokens = rate
            self.last = time.monotonic()
            self.lock = threading.Lock()

        def consume(self):
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.last
                self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / 60.0))
                self.last = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                wait = (1 - self.tokens) * (60.0 / self.rate)
                time.sleep(wait)
                self.tokens = 0
                self.last = time.monotonic()
                return True

    bucket = TokenBucket(max_per_minute)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bucket.consume()
            return func(*args, **kwargs)
        return wrapper
    return decorator
