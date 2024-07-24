from api.lastfm.user.library import get_library_data
from api.lastfm.user.profile import get_user_data
from api.discord import Presence

from helpers.url_utils import url_encoder

from libs.monitoring import logging
from libs.system import datetime

from constants.project import CLIENT_ID

class DiscordRPC:
    def __init__(self):
        """
        Initializes the DiscordRPC class.
        
        Sets up the Presence object for Discord Rich Presence and initializes
        state variables.
        """
        self.RPC = Presence(CLIENT_ID)
        self._enabled = False
        self._disabled = True
        self.start_time = None
        self.last_track = None

    def _connect(self):
        """
        Establishes a connection to Discord.
        
        Connects to Discord if not already connected and updates state variables.
        """
        if not self._enabled:
            self.RPC.connect()  # Establish the connection to Discord
            logging.info('Connected with Discord')
            self._enabled = True
            self._disabled = False

    def _disconnect(self):
        """
        Disconnects from Discord.
        
        Clears the current RPC state, closes the connection, and updates state variables.
        """
        if not self._disabled:
            self.RPC.clear()  # Clear the current RPC state
            self.RPC.close()  # Close the connection to Discord
            logging.info('Disconnected from Discord due to inactivity on Last.fm')
            self._disabled = True
            self._enabled = False

    def enable(self):
        """
        Connects to Discord if not already connected.
        
        Checks if the connection to Discord is not already enabled. If not, it 
        establishes the connection.
        """
        self._connect()

    def disable(self):
        """
        Disconnects from Discord.
        
        Checks if the connection to Discord is not already disabled. If not, 
        it clears the current RPC state and closes the connection.
        """
        self._disconnect()

    def update_status(self, track, title, artist, album, time_remaining, username, artwork):
        """
        for _ in [track, title, artist, album, time_remaining, username, artwork]:
            print(_)
        """

        if len(title) < 2:
            title = title + ' '

        if self.last_track == track:
            # if the track is the same as the last track, don't update the status
            pass
        else:
            # if the track is different, update the status
            album_bool = album is not None
            time_remaining_bool = time_remaining > 0
            if time_remaining_bool:
                time_remaining = float(str(time_remaining)[0:3])

            logging.info(f'Album: {album}')
            logging.info(f'Time Remaining: {time_remaining_bool} - {time_remaining}')
            logging.info(f"Now Playing: {track}")

            self.start_time = datetime.datetime.now().timestamp()
            self.last_track = track
            track_artist_album = f'{artist} - {album}'

            rpcButtons = [
                {"label": "View Track", "url": str(f"https://www.last.fm/tr/user/{username}/library/music/{url_encoder(artist)}/_/{url_encoder(title)}")},
                {"label": "Search on YouTube Music", "url": str(f"https://music.youtube.com/search?q={url_encoder(album)}")}
                #{"label": "Search on Spotify", "url": str(f"https://open.spotify.com/search/{url_encoder(album)}")}
                #{"label": "View Track", "url": str(f"https://www.last.fm/music/{url_encoder(artist)}/{url_encoder(title)}")}
                #{"label": "View Last.fm Profile", "url": str(f"https://www.last.fm/user/{username}")}
            ]

            user_data = get_user_data(username)
            #print(json.dumps(user_data, indent=2))

            user_display_name = user_data["display_name"]
            scrobbles, artists, loved_tracks = user_data["header_status"] # unpacking

            library_data = get_library_data(username, artist, title)
            #print(json.dumps(library_data, indent=2))

            rpc_small_image = user_data["avatar_url"]
            artist_count = library_data["artist_count"]

            large_image_lines = {}
            small_image_lines = {
                'name':         f"{user_display_name} (@{username})",
                "scrobbles":    f'Scrobbles: {scrobbles}',
                "artists":      f'Artists: {artists}',
                "loved_tracks": f'Loved Tracks: {loved_tracks}'}

            # artwork
            if artwork == None:
                # if there is no artwork, use the default one
                now = datetime.datetime.now()
                #day: false, night: true
                is_day = now.hour >= 18 or now.hour < 9 
                artwork = 'https://i.imgur.com/GOVbNaF.png' if is_day else 'https://i.imgur.com/kvGS4Pa.png'
                large_image_lines['theme'] = f"{'Night' if is_day else 'Day'} Mode Cover"
            else:
                pass

            if artist_count:
                # if the artist is in the library
                track_count = library_data["track_count"]
                large_image_lines["artist_scrobbles"] = f'Scrobbles: {artist_count}/{track_count}' if track_count else f'Scrobbles: {artist_count}'
            else:
                large_image_lines['first_time'] = f'First time listening!'

            # line process
            rpc_small_image_text = ''
            rpc_large_image_text = ''
            line_limit = 26
            xchar = ' '

            #print(len(large_image_lines), large_image_lines)

            for line_key in small_image_lines:
                line = f'{small_image_lines[line_key]} '
                line_suffix = "" if len(line) > 20 else (line_limit - len(line) - sum(_.isupper() for _ in line))*xchar
                rpc_small_image_text += f'{line}{line_suffix} '

            for line_key in large_image_lines:
                line = f'{large_image_lines[line_key]} '
                if len(large_image_lines) == 1: rpc_large_image_text = line
                else:
                    """
                    line_suffix = "" if len(line) > 20 else (line_limit - len(line) - sum(_.isupper() for _ in line))*xchar
                    rpc_large_image_text += f'{line}{line_suffix} '
                    """
                    rpc_large_image_text += f'{line}{(line_limit - len(line) - sum(_.isupper() for _ in line))*xchar} '

            # if the text is too long, cut it
            if len(rpc_small_image_text) > 128:
                rpc_small_image_text = rpc_small_image_text.replace(xchar,'')
            if len(rpc_large_image_text) > 128:
                rpc_large_image_text = rpc_large_image_text.replace(xchar,'')

            update_assets = {
                'details': title,
                'buttons': rpcButtons,
                'small_image': rpc_small_image,
                'small_text': rpc_small_image_text,
                'large_text': rpc_large_image_text,
                # situation-dependent assets
                'large_image': 'artwork' if not time_remaining_bool and not album_bool else artwork,
                'state': track_artist_album if time_remaining_bool and not album_bool else artist,
                'end': time_remaining + self.start_time if time_remaining_bool else None}

            """
            # logging
            if time_remaining_bool:
                if album_bool:
                    print('Updating status with album, time remaining.')
                else:
                    print('Updating status without album, time remaining.')
            else:
                if album_bool:
                    print('Updating status with album, no time remaining')
                else:
                    print('Updating status without album, no time remaining')
            """

            try:
                self.RPC.update(**update_assets)
            except Exception as e:
                logging.error(f'Error updating RPC: {e}')