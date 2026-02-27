import pylast
from loguru import logger

import constants.project as project
from api.lastfm.models import TrackInfo

logger = logger.bind(name="lastfm")


class APIKeyError(Exception):
    """Exception raised for fatal Last.fm API key issues."""

    pass


class User:
    def __init__(self, username, cooldown=None):
        from constants.project import API_KEY, API_SECRET, DEFAULT_COOLDOWN

        self.username = username
        self.cooldown = cooldown if cooldown is not None else DEFAULT_COOLDOWN

        # Initialize network with current keys
        self.network = pylast.LastFMNetwork(API_KEY, API_SECRET)
        self.lastfm_user = self.network.get_user(username)

        self.last_track = None
        self.last_track_info = None

    def _get_current_track(self):
        try:
            return self.lastfm_user.get_now_playing()
        except pylast.WSError as e:
            error_str = str(e)
            if "Invalid API key" in error_str or "API Key Suspended" in error_str:
                logger.critical(f"FATAL API ERROR: {error_str}")
                raise APIKeyError(error_str) from e

            logger.error(f"{project.TRANSLATIONS['pylast_ws_error'].format(self.cooldown)} | Details: {e}")
        except pylast.NetworkError:
            logger.error(project.TRANSLATIONS["pylast_network_error"])
        except pylast.MalformedResponseError:
            logger.error(project.TRANSLATIONS["pylast_malformed_response_error"])
        return None

    def _get_track_info(self, current_track) -> TrackInfo:
        info = TrackInfo()
        try:
            info.title = current_track.get_title()
            info.artist = current_track.get_artist().get_name()

            album = current_track.get_album()
            if album:
                info.album = album.get_title()
                info.artwork_url = album.get_cover_image()

            info.duration = current_track.get_duration()
            # Note: We could also check is_loved here if needed
        except pylast.WSError as e:
            logger.error(f"pylast.WSError: {e}")
        except pylast.NetworkError:
            logger.error(project.TRANSLATIONS["pylast_network_error"])

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
        logger.debug(project.TRANSLATIONS["no_song"].format(self.cooldown))
        return None, None
