"""
Centralized HTTP client module.

All network requests across the application should go through these helpers.
This keeps the scrapling dependency in one place, making it easy to swap
the underlying library in the future.
"""

from scrapling.fetchers import AsyncFetcher, Fetcher


def fetch(url: str, **kwargs):
    """Synchronous GET request. Returns a scrapling Response object."""
    return Fetcher.get(url, **kwargs)


async def async_fetch(url: str, **kwargs):
    """Asynchronous GET request. Returns a scrapling Response object."""
    return await AsyncFetcher.get(url, **kwargs)
