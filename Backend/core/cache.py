"""Simple namespaced in-process cache backed by cachetools.

This is intentionally lightweight so it works without Redis.  When the app
scales beyond a single process, this can be swapped for a Redis backend
without changing the public API.
"""

from cachetools import TTLCache
from typing import Any, Optional

# Namespace -> TTLCache
_caches: dict[str, TTLCache] = {}


def get_cache(namespace: str, maxsize: int = 1000, ttl: int = 300) -> TTLCache:
    """Return (or create) a namespaced TTL cache."""
    if namespace not in _caches:
        _caches[namespace] = TTLCache(maxsize=maxsize, ttl=ttl)
    return _caches[namespace]


def cache_get(namespace: str, key: str) -> Optional[Any]:
    cache = _caches.get(namespace)
    if cache is None:
        return None
    return cache.get(key)


def cache_set(namespace: str, key: str, value: Any, maxsize: int = 1000, ttl: int = 300) -> None:
    cache = get_cache(namespace, maxsize=maxsize, ttl=ttl)
    cache[key] = value


def cache_clear(namespace: str | None = None) -> None:
    if namespace is None:
        for cache in _caches.values():
            cache.clear()
        return
    cache = _caches.get(namespace)
    if cache:
        cache.clear()
