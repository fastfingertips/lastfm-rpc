import datetime
from loguru import logger

from api.lastfm.user.library import get_library_data
from api.lastfm.user.profile import get_user_data

from pypresence.presence import Presence
from pypresence import exceptions
from pypresence.types import ActivityType, StatusDisplayType

from utils.url_utils import url_encoder
from utils.string_utils import messenger
from constants.project import (
    CLIENT_ID, 
    DAY_MODE_COVER, NIGHT_MODE_COVER,
    RPC_LINE_LIMIT, RPC_XCHAR,
    LASTFM_TRACK_URL_TEMPLATE, YT_MUSIC_SEARCH_TEMPLATE,
    DEFAULT_AVATAR_URL, LASTFM_ICON_URL
)

logger = logger.bind(name='rpc')

class DiscordRPC:
    def __init__(self):
        """
        Initializes the DiscordRPC class.
        
        Sets up the state variables. The actual Presence object is initialized
        when enable() is called.
        """
        self.RPC = None
        self._enabled = False
        self._disabled = True
        self.start_time = None
        self.last_track = None
        self.connection_time = None
        self.current_artist = None
        self.connection_time = None
        self.current_artist = None
        self.artist_scrobbles = 0
        
        # Display Options
        self.show_scrobbles = True
        self.show_artists = True
        self.show_loved = True
        self.show_small_image = True # Main toggle for small image area
        self.use_custom_profile_image = True # Toggle between user avatar and default icon
        self.use_default_icon = False # Toggle for default avatar fallback
        self.use_lastfm_icon = False # Toggle for Last.fm icon fallback
        self.show_username = True
        
        self.show_artist_scrobbles_large = True
        self.focus_artist = True
        
        # Cache for forced updates
        self.last_fetched_track = None
        self.cached_user_data = None
        self.cached_library_data = None

    @property
    def is_connected(self):
        """Returns whether the RPC is currently connected and active."""
        return self._enabled and not self._disabled

    def _connect(self):
        """
        Establishes a connection to Discord.
        """
        if not self._enabled:
            try:
                if self.RPC is None:
                    self.RPC = Presence(CLIENT_ID)
                
                self.RPC.connect()
                self.connection_time = datetime.datetime.now()
                logger.info('Connected with Discord')
                self._enabled = True
                self._disabled = False
            except exceptions.DiscordNotFound:
                logger.warning('Discord not found, will retry in next cycle')
            except Exception as e:
                logger.error(f'Error connecting to Discord: {e}')

    def _disconnect(self):
        """
        Disconnects from Discord.
        
        Clears the current RPC state, closes the connection, and updates state variables.
        """
        if not self._disabled and self.RPC:
            self.RPC.clear()  # Clear the current RPC state
            self.RPC.close()  # Close the connection to Discord
            self.connection_time = None
            self.last_track = None # Reset so update triggers on reconnect
            self.current_artist = None
            self.artist_scrobbles = None
            logger.info('Disconnected from Discord due to inactivity on Last.fm')
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

    def _format_image_text(self, lines, limit, xchar):
        """Processes and formats text for RPC images while strictly preserving comments."""
        logger.debug(f"Format Text: {list(lines.keys())}")
        result_text = ''
        
        for line_key in lines:
            line = f'{lines[line_key]} '
            if line_key in ['theme', 'artist_scrobbles', 'first_time']:
                # Processing logic for large image lines
                if len(lines) == 1: 
                    result_text = line
                else:
                    """
                    line_suffix = "" if len(line) > 20 else (line_limit - len(line) - sum(_.isupper() for _ in line))*xchar
                    rpc_large_image_text += f'{line}{line_suffix} '
                    """
                    result_text += f'{line}{(limit - len(line) - sum(c.isupper() for c in line))*xchar} '
            else:
                # Processing logic for small image lines
                line_suffix = "" if len(line) > 20 else (limit - len(line) - sum(c.isupper() for c in line))*xchar
                result_text += f'{line}{line_suffix} '
        
                # if the text is too long, cut it
        if len(result_text) > 128:
            result_text = result_text.replace(xchar, '')
            
        return result_text.strip()

    def _prepare_artwork_status(self, artwork, artist_count, library_data):
        """Handles artwork fallback and library scrobble counts."""
        large_image_lines = {}
        
        # artwork
        if artwork is None:
            # if there is no artwork, use the default one
            now = datetime.datetime.now()
            #day: false, night: true
            is_day = now.hour >= 18 or now.hour < 9 
            artwork = DAY_MODE_COVER if is_day else NIGHT_MODE_COVER
            large_image_lines['theme'] = messenger('rpc_night_mode') if is_day else messenger('rpc_day_mode')

        if artist_count:
            # if the artist is in the library
            if self.show_artist_scrobbles_large:
                track_count = library_data["track_count"]
                msg = messenger('rpc_scrobbles_total', [artist_count, track_count]) if track_count else messenger('rpc_scrobbles', artist_count)
                large_image_lines["artist_scrobbles"] = msg
        else:
            large_image_lines['first_time'] = messenger('rpc_first_time')
            
        return artwork, large_image_lines

    def _prepare_buttons(self, username, artist, title, album):
        """
        Compiles the RPC buttons.
        
        Alternative button templates for future use:
        - Spotify: {"label": "Search on Spotify", "url": str(SPOTIFY_SEARCH_TEMPLATE.format(query=url_encoder(album)))}
        - track_url: {"label": "View Track", "url": str(f"https://www.last.fm/music/{url_encoder(artist)}/{url_encoder(title)}")}
        - user_url: {"label": "View Last.fm Profile", "url": str(LASTFM_USER_URL.format(username=username))}
        """
        return [
            {"label": messenger('menu_focus_track'), "url": str(LASTFM_TRACK_URL_TEMPLATE.format(username=username, artist=url_encoder(artist), title=url_encoder(title)))},
            {"label": "YouTube Music", "url": str(YT_MUSIC_SEARCH_TEMPLATE.format(query=url_encoder(album)))}
        ]

    def update_status(self, track, title, artist, album, time_remaining, username, artwork, force=False):
        if len(title) < 2:
            title = title + ' '

        if self.last_track == track and self.current_artist is not None and not force:
            return

        time_remaining_bool = time_remaining > 0
        if time_remaining_bool:
            time_remaining = float(str(time_remaining)[0:3])

        user_data, library_data = self._get_metadata_with_cache(track, username, artist, title)
        if not user_data or not library_data:
            return

        # Only reset start_time if it's a new track
        if self.last_track != track:
            self.start_time = datetime.datetime.now().timestamp()
            
        self.last_track = track
        self.current_artist = artist
        self.artist_scrobbles = library_data["artist_count"]

        # Prepare Assets
        rpc_buttons = self._prepare_buttons(username, artist, title, album)
        small_image_asset, small_text = self._prepare_small_image_details(user_data, username)
        artwork_asset, large_text = self._prepare_artwork_and_large_text(artwork, album, library_data)

        # Logic for Discord Display
        display_type = StatusDisplayType.STATE if self.focus_artist else StatusDisplayType.DETAILS
        rpc_state = f'{artist} - {album}' if time_remaining_bool and album else artist

        update_assets = {
            'activity_type': ActivityType.LISTENING,
            'status_display_type': display_type,
            'details': title,
            'state': rpc_state,
            'buttons': rpc_buttons,
            'small_image': small_image_asset,
            'small_text': small_text,
            'large_text': large_text,
            'large_image': 'artwork' if not time_remaining_bool and not album else artwork_asset,
            'start': self.start_time,
            'end': time_remaining + self.start_time if (time_remaining_bool and self.start_time is not None) else None
        }

        self._send_rpc_update(update_assets)

    def _get_metadata_with_cache(self, track, username, artist, title):
        """Fetch user and library data with caching logic."""
        if self.last_fetched_track == track and self.cached_user_data and self.cached_library_data:
            logger.debug(f"Using cached Last.fm stats for {track}")
            return self.cached_user_data, self.cached_library_data

        user_data = get_user_data(username)
        if not user_data:
            logger.error(f"User data not found for {username}")
            return None, None
        logger.info(f"User data found for {username}")
        logger.debug(f"User data: {user_data}")

        library_data = get_library_data(username, artist, title)
        if not library_data:
            logger.error(f"Library data not found for {username}")
            return None, None
        logger.info(f"Library data found for {username}")
        logger.debug(f"Library data: {library_data}")

        self.last_fetched_track = track
        self.cached_user_data = user_data
        self.cached_library_data = library_data
        return user_data, library_data

    def _prepare_small_image_details(self, user_data, username):
        """Prepares the small image asset and hover text."""
        if not self.show_small_image:
            return None, None

        asset = None
        if self.use_custom_profile_image:
            asset = user_data["avatar_url"]
        elif self.use_default_icon:
            asset = DEFAULT_AVATAR_URL
        elif self.use_lastfm_icon:
            asset = LASTFM_ICON_URL
        
        lines = {}
        if self.show_username:
            lines['name'] = f"{user_data['display_name']} (@{username})"
        
        # Unpack header status
        scrobbles, artists, loved_tracks = user_data["header_status"]
        if self.show_scrobbles:
            lines["scrobbles"] = messenger('rpc_scrobbles', scrobbles)
        if self.show_artists:
            lines["artists"] = messenger('rpc_artists', artists)
        if self.show_loved:
            lines["loved_tracks"] = messenger('rpc_loved_tracks', loved_tracks)

        text = self._format_image_text(lines, RPC_LINE_LIMIT, RPC_XCHAR)
        return asset, text

    def _prepare_artwork_and_large_text(self, artwork, album, library_data):
        """Prepares the large image asset and hover text."""
        artist_count = library_data["artist_count"]
        artwork, lines = self._prepare_artwork_status(artwork, artist_count, library_data)
        
        text = self._format_image_text(lines, RPC_LINE_LIMIT, RPC_XCHAR)
        if not text or text.strip() == "":
            text = album if album else messenger('rpc_listening_now')
        
        return artwork, text

    def _send_rpc_update(self, update_assets):
        """Sends the prepared payload to Discord."""
        if self.RPC:
            try:
                logger.debug(f"RPC update_assets: {update_assets}")
                self.RPC.update(**update_assets)
            except Exception as e:
                logger.error(f'Error updating RPC: {e}')
                # If update fails (e.g. BrokenPipe, Request Terminated), force disconnect
                # so the app effectively tries to reconnect on next cycle.
                self._disconnect()
