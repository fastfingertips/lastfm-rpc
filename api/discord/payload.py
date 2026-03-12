from loguru import logger

from api.discord.formatter import format_rpc_text
from api.lastfm.models import TrackInfo, UserState
from constants.project import (
    DAY_MODE_COVER,
    DEFAULT_AVATAR_URL,
    LASTFM_ICON_URL,
    LASTFM_TRACK_URL_TEMPLATE,
    NIGHT_MODE_COVER,
    YT_MUSIC_SEARCH_TEMPLATE,
)
from utils.clock import is_night_hours
from utils.i18n import messenger
from utils.strings import format_placeholders
from utils.urls import url_encoder

logger = logger.bind(name="rpc_payload")


def format_template(template: str, info: TrackInfo, username: str, user_state: UserState) -> str:
    """Adapts formatted_placeholders for internal use with models."""
    if not template:
        return ""

    placeholders = {
        "artist": info.artist or "",
        "title": info.title or "",
        "album": info.album or messenger("rpc_no_album"),
        "username": username,
        "display_name": user_state.display_name or username,
        "scrobbles": str(info.artist_scrobbles or 0),
        "track_scrobbles": str(info.track_scrobbles or 0),
        "total_scrobbles": str(user_state.total_scrobbles),
        "avatar_url": user_state.avatar_url or DEFAULT_AVATAR_URL,
        "artwork_url": info.artwork_url or DAY_MODE_COVER,
    }
    return format_placeholders(template, placeholders)


class RPCPayloadBuilder:
    """Encapsulates the construction logic for the Discord RPC payload."""

    def __init__(
        self, info: TrackInfo, username: str, user_state: UserState, lib_data: dict, start_time: float, rpc_config
    ):
        self.info = info
        self.username = username
        self.user_state = user_state
        self.lib_data = lib_data
        self.start_time = start_time
        self.config = rpc_config
        self.artist_count = lib_data.get("artist_count", 0)

    def build(self):
        """Assembles the final dictionary for pypresence."""
        from pypresence.types import ActivityType, StatusDisplayType

        # 1. Component Preparation
        buttons = self._prepare_buttons()
        artwork_asset, large_text = self._prepare_large_image_group()
        small_asset, small_text = self._prepare_small_image_group()
        details, state = self._prepare_core_text()

        # 2. Final adjustments & Validation
        has_duration = self.info.duration > 0
        display_type = StatusDisplayType.STATE if self.config.focus_artist else StatusDisplayType.DETAILS

        return {
            "activity_type": ActivityType.LISTENING,
            "status_display_type": display_type,
            "details": details if len(details) >= 2 else f"{details} ",
            "state": state if len(state) >= 2 else f"{state} ",
            "buttons": buttons,
            "small_image": small_asset,
            "small_text": small_text,
            "large_text": large_text,
            "large_image": artwork_asset,
            "start": self.start_time,
            "end": (self.info.duration + self.start_time) if (has_duration and self.start_time) else None,
        }

    def _prepare_buttons(self):
        """Compiles buttons based on templates and config."""
        from constants.project import LASTFM_TRACK_GLOBAL_URL, LASTFM_USER_URL, SPOTIFY_SEARCH_TEMPLATE

        artist, title, album = self.info.artist, self.info.title, self.info.album
        enc_artist, enc_title, enc_album = url_encoder(artist), url_encoder(title), url_encoder(album)

        options = {
            "lastfm_track": {
                "label": "View Track on Last.fm",
                "url": str(LASTFM_TRACK_GLOBAL_URL.format(artist=enc_artist, title=enc_title)),
            },
            "lastfm_user_track": {
                "label": messenger("menu_focus_track"),
                "url": str(
                    LASTFM_TRACK_URL_TEMPLATE.format(username=self.username, artist=enc_artist, title=enc_title)
                ),
            },
            "lastfm_profile": {
                "label": "View Last.fm Profile",
                "url": str(LASTFM_USER_URL.format(username=self.username)),
            },
            "youtube": {
                "label": "YouTube Music",
                "url": str(YT_MUSIC_SEARCH_TEMPLATE.format(query=enc_album if album else f"{enc_artist} {enc_title}")),
            },
            "spotify": {
                "label": "Search on Spotify",
                "url": str(SPOTIFY_SEARCH_TEMPLATE.format(query=enc_album if album else f"{enc_artist} {enc_title}")),
            },
        }

        buttons = [options[opt_key] for opt_key in [self.config.button_1, self.config.button_2] if opt_key in options]
        return buttons[:2] if buttons else None

    def _prepare_large_image_group(self):
        """Handles artwork and its hover text."""
        # ── Artwork Asset ──
        if self.config.use_custom_large_image:
            asset = format_template(self.config.large_image_template, self.info, self.username, self.user_state)
        else:
            asset = self.info.artwork_url
            if asset is None:
                asset = DAY_MODE_COVER if is_night_hours() else NIGHT_MODE_COVER

        # ── Hover Text ──
        if not self.config.show_large_text:
            text = None
        elif self.config.use_custom_large_text:
            text = format_template(self.config.large_text_template, self.info, self.username, self.user_state)
        else:
            lines = {}
            if self.artist_count:
                if self.config.show_artist_scrobbles_large:
                    track_count = self.lib_data.get("track_count")
                    msg = (
                        messenger("rpc_scrobbles_total", [self.artist_count, track_count])
                        if track_count
                        else messenger("rpc_scrobbles", self.artist_count)
                    )
                    lines["artist_scrobbles"] = msg
            elif self.config.show_artist_scrobbles_large:
                lines["first_time"] = messenger("rpc_first_time")

            text = format_rpc_text(lines) or (self.info.album if self.info.album else None)

        return asset, text

    def _prepare_small_image_group(self):
        """Prepares user status icon and its hover text."""
        if not self.config.show_small_image:
            return None, None

        # ── Asset ──
        if self.config.use_custom_small_image:
            asset = format_template(self.config.small_image_template, self.info, self.username, self.user_state)
        else:
            if self.config.use_custom_profile_image and self.user_state.avatar_url:
                asset = self.user_state.avatar_url
            elif self.config.use_default_icon:
                asset = DEFAULT_AVATAR_URL
            elif self.config.use_lastfm_icon:
                asset = LASTFM_ICON_URL
            else:
                asset = None

        # ── Hover Text ──
        if not self.config.show_small_text:
            text = None
        elif self.config.use_custom_small_text:
            text = format_template(self.config.small_text_template, self.info, self.username, self.user_state)
        else:
            stats = {}
            if self.config.show_username:
                display = self.user_state.display_name or self.user_state.username
                stats["username"] = f"{display} (@{self.user_state.username})"
            if self.config.show_scrobbles:
                stats["scrobbles"] = messenger("rpc_scrobbles", self.user_state.total_scrobbles)
            if self.config.show_artists:
                stats["artists"] = messenger("rpc_artists", self.user_state.total_artists)
            if self.config.show_loved:
                stats["loved"] = messenger("rpc_loved_tracks", self.user_state.total_loved_tracks)
            text = format_rpc_text(stats)

        return asset, text

    def _prepare_core_text(self):
        """Formats the main two lines of text."""
        details = format_template(self.config.details_template, self.info, self.username, self.user_state)
        state = format_template(self.config.state_template, self.info, self.username, self.user_state)
        return details, state


def build_rpc_payload(
    info: TrackInfo, username: str, user_state: UserState, lib_data: dict, start_time: float, rpc_config
):
    """Factory function for creating the RPC payload dictionary."""
    builder = RPCPayloadBuilder(info, username, user_state, lib_data, start_time, rpc_config)
    return builder.build()
