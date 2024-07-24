from constants.project import API_KEY, API_SECRET, TRANSLATIONS
from api.discord.rpc import DiscordRPC
import pylast
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

network = pylast.LastFMNetwork(API_KEY, API_SECRET)
rpc = DiscordRPC()

class User:
    def __init__(self, username, cooldown=6):
        self.username = username
        self.user = network.get_user(username)
        self.cooldown = cooldown

    def _get_current_track(self):
        try:
            return self.user.get_now_playing()
        except pylast.WSError:
            logging.error(TRANSLATIONS['pylast_ws_error'].format(self.cooldown))
        except pylast.NetworkError:
            logging.error(TRANSLATIONS['pylast_network_error'])
        except pylast.MalformedResponseError:
            logging.error(TRANSLATIONS['pylast_malformed_response_error'])
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
            logging.error(f'pylast.WSError: {e}')
        except pylast.NetworkError:
            logging.error(TRANSLATIONS['pylast_network_error'])
        return title, artist, album, artwork, time_remaining

    def now_playing(self):
        while True:
            current_track = self._get_current_track()
            if current_track:
                title, artist, album, artwork, time_remaining = self._get_track_info(current_track)
                rpc.enable()
                rpc.update_status(
                    str(current_track),
                    str(title),
                    str(artist),
                    str(album),
                    time_remaining,
                    self.username,
                    artwork
                )
                time.sleep(self.cooldown + 8)
            else:
                logging.info(TRANSLATIONS['no_song'].format(self.cooldown))
                rpc.disable()
            time.sleep(self.cooldown)
