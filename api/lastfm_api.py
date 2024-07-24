from constants.project import TRANSLATIONS
import pylast
import time

class LastFmUser:
    def __init__(self, api_key, api_secret, username, cooldown=6):
        self.network = pylast.LastFMNetwork(api_key, api_secret)
        self.username = username
        self.user = self.network.get_user(username)
        self.cooldown = cooldown

    def now_playing(self):
        """
        Retrieves the currently playing track for the user, if available.

        Returns a tuple containing the current track, title, artist, album, artwork, and time remaining.
        """
        current_track = None

        try:
            current_track = self.user.get_now_playing()
        except (pylast.WSError, pylast.NetworkError, pylast.MalformedResponseError) as e:
            self._handle_error(e)
            time.sleep(self.cooldown)
            return ()

        if current_track:
            return self._get_track_details(current_track)
        else:
            print(TRANSLATIONS['no_song'].format(str(self.cooldown)))
            time.sleep(self.cooldown)
            return ()

    def _get_track_details(self, current_track):
        """
        Extracts details from the current track.

        Returns a tuple containing the current track, title, artist, album, artwork, and time remaining.
        """
        title, artist, album, artwork, time_remaining = None, None, None, None, 0

        try:
            title = current_track.get_title()
            artist = current_track.get_artist()
            album = current_track.get_album()
            time_remaining = current_track.get_duration()
            if album:
                artwork = album.get_cover_image()
        except pylast.WSError as e:
            print(f'pylast.WSError: {e}')
        except pylast.NetworkError:
            print(TRANSLATIONS['pylast_network_error'])

        return current_track, title, artist, album, artwork, time_remaining

    def _handle_error(self, error):
        """
        Handles errors that occur during the retrieval of the current track.
        """
        if isinstance(error, pylast.WSError):
            print(TRANSLATIONS['pylast_ws_error'].format(str(self.cooldown)))
        elif isinstance(error, pylast.NetworkError):
            print(TRANSLATIONS['pylast_network_error'])
        elif isinstance(error, pylast.MalformedResponseError):
            print(TRANSLATIONS['pylast_malformed_response_error'])