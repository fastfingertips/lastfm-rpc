import asyncio

from loguru import logger

import constants.project as project
from core.config import config
from core.exceptions import AppNetworkError
from discord.exceptions import DiscordError
from lastfm.exceptions import APIKeyError, LastFMError
from lastfm.models import TrackInfo
from lastfm.user.scraper import LastFMScraper
from lastfm.user.tracking import LastFMTracker
from utils.app.i18n import messenger

logger = logger.bind(name="sync")


class SyncService:
    """Orchestrates the background synchronization loop between Last.fm and Discord."""

    def __init__(self, app):
        self.app = app
        self._cached_track = None
        self._cached_metadata = (None, None)  # user_state, library_data
        self._scraper = LastFMScraper(config.username)

    def start(self):
        """Entry point for the service thread."""
        logger.info(messenger("starting_rpc"))
        try:
            asyncio.run(self._run_loop())
        except Exception as e:
            logger.error(f"Fatal crash in SyncService: {e}")

    async def _run_loop(self):
        await self.app.rpc.enable()
        tracker = LastFMTracker(config.username, config.api_key, config.api_secret)

        while not self.app.exit_event.is_set():
            if self.app.config_needs_reload:
                self._handle_config_reload(tracker)

            is_forced = self.app.update_event.is_set()
            self.app.update_event.clear()

            try:
                wait_time = await self._process_cycle(tracker, is_forced)
                await self._responsive_sleep(wait_time)
            except APIKeyError as e:
                await self.app.handle_api_error(e)
                await self._wait_for_fix()
            except DiscordError as e:
                logger.warning(f"Discord error: {e}. Disabling RPC...")
                await self.app.rpc.disable()
                await self._responsive_sleep(10.0)
            except (AppNetworkError, LastFMError) as e:
                logger.warning(f"Provider error: {e}. Retrying...")
                await self._responsive_sleep(5.0)
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                await self._responsive_sleep(5.0)

    def _handle_config_reload(self, tracker: LastFMTracker):
        logger.info(messenger("config_reloading", config.username))
        tracker.refresh_network(config.username, config.api_key, config.api_secret)
        self._scraper.username = config.username
        self.app.config_needs_reload = False

    async def _process_cycle(self, tracker, is_forced):
        """Executes a single fetch-and-update step."""
        # Fetch current track
        current_track, info = (
            await asyncio.to_thread(tracker.now_playing)
            if not is_forced or not self._cached_track
            else self._cached_track
        )

        if not info:
            await self._handle_idle_state()
            return project.UPDATE_INTERVAL

        # Fetch metadata and then cache track
        user_state, lib_data = await self._fetch_metadata(current_track, info)
        self._cached_track = (current_track, info)

        if user_state:
            await self._handle_active_track(current_track, info, user_state, lib_data, is_forced)
            return project.TRACK_CHECK_INTERVAL

        return project.UPDATE_INTERVAL

    async def _fetch_metadata(self, track_obj, info: TrackInfo):
        """Retrieves user stats with simple object-based caching."""
        if self._cached_track and self._cached_track[0] == track_obj and self._cached_metadata[0]:
            return self._cached_metadata

        user_state, lib_data = await asyncio.gather(
            self._scraper.get_user_state(), self._scraper.get_library_data(info.artist, info.title)
        )
        self._cached_metadata = (user_state, lib_data)
        return user_state, lib_data

    async def _handle_active_track(self, track_obj, info: TrackInfo, user_state, lib_data, is_forced):
        """Processes and updates UI/RPC for an active track."""
        # Clean mapping logic belonging to service layer
        info.artist_scrobbles = lib_data.get("artist_count", 0)
        info.track_scrobbles = lib_data.get("track_count", 0)

        # Update App UI State
        display_text = messenger("now_playing", f"{info.artist} - {info.title}")
        self.app.update_status_display(display_text, rpc_connected=self.app.rpc.is_connected)

        # Update RPC status
        await self.app.rpc.update_status(
            track_obj, info, config.username, user_state, lib_data, config.rpc, force=is_forced
        )

    async def _handle_idle_state(self):
        self._cached_track = None
        self._cached_metadata = (None, None)
        self.app.update_status_display(messenger("no_track"), rpc_connected=self.app.rpc.is_connected)
        await self.app.rpc.clear_status()

    async def _responsive_sleep(self, seconds):
        for _ in range(int(seconds * 2)):
            if self.app.update_event.is_set() or self.app.exit_event.is_set():
                break
            await asyncio.sleep(0.5)

    async def _wait_for_fix(self):
        """Block loop until user updates settings."""
        while not self.app.update_event.is_set() and not self.app.exit_event.is_set():
            await asyncio.sleep(1.0)
