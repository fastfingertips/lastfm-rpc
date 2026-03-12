from core.exceptions import LastFMRPCError


class DiscordError(LastFMRPCError):
    """Raised when a Discord RPC specific error occurs."""
