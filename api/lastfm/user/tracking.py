import pylast
from loguru import logger

from api.lastfm.models import TrackInfo
from core.config import config
from core.exceptions import APIKeyError, LastFMError
from utils.clock import ms_to_seconds
from utils.i18n import messenger

logger = logger.bind(name="lastfm")


class LastFMTracker:
    def __init__(self, username, cooldown=None):
        from constants.project import DEFAULT_COOLDOWN

        self.username = username
        self.cooldown = cooldown if cooldown is not None else DEFAULT_COOLDOWN
        self.network = None
        self.lastfm_user = None
        self.last_track = None
        self.last_track_info = None

        self.refresh_network(username)

    def refresh_network(self, username):
        """Initializes or updates the Last.fm network connection."""
        self.username = username
        self.network = pylast.LastFMNetwork(
            config.api_key,
            config.api_secret,
        )
        self.lastfm_user = self.network.get_user(username)
        logger.debug(f"LastFMTracker network refreshed for user: {username}")

        self.last_track = None
        self.last_track_info = None

    def _handle_pylast_error(self, e, context=""):
        """Centralized handler for pylast exceptions."""
        error_str = str(e)
        if isinstance(e, pylast.WSError):
            if "Invalid API key" in error_str or "API Key Suspended" in error_str:
                logger.critical(f"FATAL API ERROR: {error_str}")
                raise APIKeyError(error_str) from e
            logger.error(f"Last.fm WS Error ({context}): {e}")
            raise LastFMError(f"Last.fm API error: {e}") from e

        if isinstance(e, pylast.NetworkError):
            logger.warning(f"Network error in {context}: {e}")
            # We don't necessarily want to raise here, maybe just log and return None
            return

        logger.error(f"Unexpected error in {context}: {e}")
        return

    def _get_current_track(self):
        try:
            return self.lastfm_user.get_now_playing()
        except (pylast.WSError, pylast.NetworkError, pylast.MalformedResponseError) as e:
            return self._handle_pylast_error(e, "get_now_playing")

    def _get_track_info(self, current_track) -> TrackInfo:
        info = TrackInfo()
        try:
            info.title = current_track.get_title()
            info.artist = current_track.get_artist().get_name()

            album = current_track.get_album()
            if album:
                info.album = album.get_title()
                info.artwork_url = album.get_cover_image()

            # pylast returns duration in milliseconds, convert to seconds
            info.duration = ms_to_seconds(current_track.get_duration())
            # Note: We could also check is_loved here if needed
        except (pylast.WSError, pylast.NetworkError, pylast.MalformedResponseError) as e:
            self._handle_pylast_error(e, "get_track_info")

        if info.artwork_url:
            logger.debug(f"Fetched artwork URL: {info.artwork_url}")
        else:
            logger.debug("No artwork found for track.")
        return info

    def now_playing(self):
        current_track = self._get_current_track()

        if current_track:
            # If track is same as last time, return cached info
            if self.last_track and str(current_track) == str(self.last_track):
                return current_track, self.last_track_info

            # New track, fetch info
            info = self._get_track_info(current_track)
            self.last_track = current_track
            self.last_track_info = info
            return current_track, info
        self.last_track = None
        self.last_track_info = None
        logger.debug(messenger("no_song", self.cooldown))
        return None, None
