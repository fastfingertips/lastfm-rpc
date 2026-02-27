"""Centralized custom exceptions for the application."""


class LastFMRPCError(Exception):
    """Base exception for all application-specific errors."""


class APIKeyError(LastFMRPCError):
    """Raised when the Last.fm API key is invalid or suspended."""


class ConfigurationError(LastFMRPCError):
    """Raised when the configuration is incomplete or invalid."""


class ConnectionError(LastFMRPCError):
    """Raised when a connection to an external service fails."""
