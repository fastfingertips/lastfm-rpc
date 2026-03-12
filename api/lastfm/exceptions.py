from core.exceptions import LastFMRPCError


class LastFMError(LastFMRPCError):
    """Raised when a Last.fm specific error occurs (e.g., user not found)."""


class APIKeyError(LastFMError):
    """Raised when the Last.fm API key is invalid or suspended."""
