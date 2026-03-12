"""Centralized base exceptions for the application."""


class LastFMRPCError(Exception):
    """Base exception for all application-specific errors."""


class ConfigurationError(LastFMRPCError):
    """Raised when the configuration is incomplete or invalid."""


class AppNetworkError(LastFMRPCError):
    """Raised when a connection to an external service fails (Application level)."""
