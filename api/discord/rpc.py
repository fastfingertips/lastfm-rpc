from loguru import logger
from pypresence import exceptions
from pypresence.presence import Presence
from pypresence.types import ActivityType, StatusDisplayType

from api.discord.formatter import format_rpc_text
from api.lastfm.models import TrackInfo, UserState
from api.lastfm.user.library import get_library_data
from api.lastfm.user.profile import get_user_data
from constants.project import (
    CLIENT_ID,
    DAY_MODE_COVER,
    DEFAULT_AVATAR_URL,
    LASTFM_ICON_URL,
    LASTFM_TRACK_URL_TEMPLATE,
    NIGHT_MODE_COVER,
    YT_MUSIC_SEARCH_TEMPLATE,
)
from utils.i18n import messenger
from utils.time_utils import is_night_hours, now, now_timestamp
from utils.url_utils import url_encoder

logger = logger.bind(name="rpc")


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
        self.show_small_image = True  # Main toggle for small image area
        self.use_custom_profile_image = True  # Toggle between user avatar and default icon
        self.use_default_icon = False  # Toggle for default avatar fallback
        self.use_lastfm_icon = False  # Toggle for Last.fm icon fallback
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
                self.connection_time = now()
                logger.info("Connected with Discord")
                self._enabled = True
                self._disabled = False
            except exceptions.DiscordNotFound:
                logger.warning("Discord not found, will retry in next cycle")
            except Exception as e:
                logger.error(f"Error connecting to Discord: {e}")

    def _disconnect(self):
        """
        Disconnects from Discord.

        Clears the current RPC state, closes the connection, and updates state variables.
        """
        if not self._disabled and self.RPC:
            self.RPC.clear()  # Clear the current RPC state
            self.RPC.close()  # Close the connection to Discord
            self.connection_time = None
            self.last_track = None  # Reset so update triggers on reconnect
            self.current_artist = None
            self.artist_scrobbles = None
            logger.info("Disconnected from Discord due to inactivity on Last.fm")
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

    def _prepare_artwork_status(self, artwork, artist_count, library_data):
        """Handles artwork fallback and library scrobble counts."""
        large_image_lines = {}

        # artwork
        if artwork is None:
            # if there is no artwork, use the default one
            is_night = is_night_hours()
            artwork = DAY_MODE_COVER if is_night else NIGHT_MODE_COVER
            large_image_lines["theme"] = messenger("rpc_night_mode") if is_night else messenger("rpc_day_mode")

        if artist_count:
            # if the artist is in the library
            if self.show_artist_scrobbles_large:
                track_count = library_data["track_count"]
                msg = (
                    messenger("rpc_scrobbles_total", [artist_count, track_count])
                    if track_count
                    else messenger("rpc_scrobbles", artist_count)
                )
                large_image_lines["artist_scrobbles"] = msg
        else:
            large_image_lines["first_time"] = messenger("rpc_first_time")

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
            {
                "label": messenger("menu_focus_track"),
                "url": str(
                    LASTFM_TRACK_URL_TEMPLATE.format(
                        username=username, artist=url_encoder(artist), title=url_encoder(title)
                    )
                ),
            },
            {"label": "YouTube Music", "url": str(YT_MUSIC_SEARCH_TEMPLATE.format(query=url_encoder(album)))},
        ]

    def update_status(self, track_obj, info: TrackInfo, username: str, force=False):
        """Main entry point to update Discord Rich Presence with new track info."""
        if not info or not info.title:
            return

        # Ensure title is not too short (Discord requirement)
        display_title = info.title if len(info.title) >= 2 else f"{info.title} "

        if self.last_track == track_obj and self.current_artist is not None and not force:
            return

        # Fetch additional metadata (User stats, library scrobbles)
        user_state, lib_data = self._get_metadata_with_cache(track_obj, username, info.artist, info.title)
        if not user_state or not lib_data:
            return

        # Map library stats to our info object
        info.artist_scrobbles = lib_data.get("artist_count", 0)
        info.track_scrobbles = lib_data.get("track_count", 0)

        # Update session start time if track changed
        if self.last_track != track_obj:
            self.start_time = now_timestamp()

        self.last_track = track_obj
        self.current_artist = info.artist
        self.artist_scrobbles = info.artist_scrobbles

        # Prepare Discord Assets
        rpc_buttons = self._prepare_buttons(username, info.artist, info.title, info.album)
        small_image_asset, small_text = self._prepare_small_image_details(user_state)
        artwork_asset, large_text = self._prepare_artwork_and_large_text(info.artwork_url, info.album, lib_data)

        # Logic for Discord Display
        display_type = StatusDisplayType.STATE if self.focus_artist else StatusDisplayType.DETAILS

        # Format state line
        has_duration = info.duration > 0
        rpc_state = f"{info.artist} - {info.album}" if has_duration and info.album else info.artist

        update_assets = {
            "activity_type": ActivityType.LISTENING,
            "status_display_type": display_type,
            "details": display_title,
            "state": rpc_state,
            "buttons": rpc_buttons,
            "small_image": small_image_asset,
            "small_text": small_text,
            "large_text": large_text,
            "large_image": "artwork" if not has_duration and not info.album else artwork_asset,
            "start": self.start_time,
            "end": (info.duration + self.start_time) if (has_duration and self.start_time is not None) else None,
        }

        self._send_rpc_update(update_assets)

    def _get_metadata_with_cache(self, track_obj, username, artist, title) -> tuple[UserState | None, dict | None]:
        """Fetch user and library data with caching logic."""
        if self.last_fetched_track == track_obj and self.cached_user_data and self.cached_library_data:
            logger.debug(f"Using cached Last.fm stats for {track_obj}")
            return self.cached_user_data, self.cached_library_data

        user_state = get_user_data(username)
        if not user_state:
            logger.error(f"User data not found for {username}")
            return None, None

        library_data = get_library_data(username, artist, title)

        # Update cache
        self.last_fetched_track = track_obj
        self.cached_user_data = user_state
        self.cached_library_data = library_data

        return user_state, library_data

    def _prepare_small_image_details(self, user_state: UserState):
        """Prepares the small image (avatar/badge) and its hover text."""
        if not self.show_small_image:
            return None, None

        # Assets
        small_image = None
        if self.use_custom_profile_image and user_state.avatar_url:
            small_image = user_state.avatar_url
        elif self.use_default_icon:
            small_image = DEFAULT_AVATAR_URL
        elif self.use_lastfm_icon:
            small_image = LASTFM_ICON_URL

        # Hover Text
        stats_lines = {}
        if self.show_username:
            display = user_state.display_name or user_state.username
            stats_lines["username"] = f"{display} (@{user_state.username})"

        if self.show_scrobbles:
            stats_lines["scrobbles"] = messenger("rpc_scrobbles", user_state.total_scrobbles)
        if self.show_artists:
            stats_lines["artists"] = messenger("rpc_artists", user_state.total_artists)
        if self.show_loved:
            stats_lines["loved"] = messenger("rpc_loved_tracks", user_state.total_loved_tracks)

        small_text = format_rpc_text(stats_lines)
        return small_image, small_text

    def _prepare_artwork_and_large_text(self, artwork, album, library_data):
        """Prepares the large image asset and hover text."""
        artist_count = library_data["artist_count"]
        artwork, lines = self._prepare_artwork_status(artwork, artist_count, library_data)

        text = format_rpc_text(lines)
        if not text or text.strip() == "":
            text = album if album else messenger("rpc_listening_now")

        return artwork, text

    def _send_rpc_update(self, update_assets):
        """Sends the prepared payload to Discord."""
        if self.RPC:
            try:
                # Clean up None values to avoid sending empty/null fields to Discord
                payload = {k: v for k, v in update_assets.items() if v is not None}
                logger.debug(f"RPC payload: {payload}")
                self.RPC.update(**payload)
            except Exception as e:
                logger.error(f"Error updating RPC: {e}")
                # If update fails (e.g. BrokenPipe, Request Terminated), force disconnect
                # so the app effectively tries to reconnect on next cycle.
                self._disconnect()
