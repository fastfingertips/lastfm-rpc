from loguru import logger
import pylast
import constants.project as project

logger = logger.bind(name='lastfm')

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
                raise APIKeyError(error_str)
            
            logger.error(f"{project.TRANSLATIONS['pylast_ws_error'].format(self.cooldown)} | Details: {e}")
        except pylast.NetworkError:
            logger.error(project.TRANSLATIONS['pylast_network_error'])
        except pylast.MalformedResponseError:
            logger.error(project.TRANSLATIONS['pylast_malformed_response_error'])
        return None

    def _get_track_info(self, current_track):
        title, artist, album, artwork, time_remaining = None, None, None, None, 0
        try:
            title = current_track.get_title()
            artist = current_track.get_artist()
            album = current_track.get_album()
            if album:
                artwork = album.get_cover_image()
            time_remaining = current_track.get_duration()
        except pylast.WSError as e:
            logger.error(f'pylast.WSError: {e}')
        except pylast.NetworkError:
            logger.error(project.TRANSLATIONS['pylast_network_error'])
        if artwork:
            logger.debug(f"Fetched artwork URL: {artwork}")
        else:
            logger.debug("No artwork found for track.")
        return title, artist, album, artwork, time_remaining

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
        else:
            self.last_track = None
            self.last_track_info = None
            logger.debug(project.TRANSLATIONS['no_song'].format(self.cooldown))
            return current_track, None
