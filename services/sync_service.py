import asyncio

from loguru import logger

import constants.project as project
from api.discord.exceptions import DiscordError
from api.lastfm.exceptions import APIKeyError, LastFMError
from api.lastfm.models import TrackInfo, UserState
from api.lastfm.user.scraper import LastFMScraper
from api.lastfm.user.tracking import LastFMTracker
from core.config import config
from core.exceptions import AppNetworkError
from utils.i18n import messenger

logger = logger.bind(name="sync")


class SyncService:
    """Handles the background synchronization loop with Last.fm and Discord."""

    def __init__(self, app):
        self.app = app
        self.cached_track_data = None
        self.last_fetched_track = None
        self.cached_user_data = None
        self.cached_library_data = None
        self.scraper = LastFMScraper(config.username)

    def start(self):
        """Runs the async RPC updater within a thread."""
        logger.info(messenger("starting_rpc"))

        # Start async worker loop using asyncio.run
        try:
            asyncio.run(self._run_loop())
        except Exception as e:
            logger.error(f"Fatal error in async loop: {e}")

    async def _run_loop(self):  # noqa: C901

        # Connect to Discord within the event loop
        await self.app.rpc.enable()

        tracker = LastFMTracker(config.username)

        try:
            while not self.app.exit_event.is_set():
                # Check if config was reloaded via GUI
                if self.app.config_needs_reload:
                    logger.info(f"Applying new configuration for user: {config.username}")
                    tracker.refresh_network(config.username)
                    self.scraper.username = config.username
                    self.app.config_needs_reload = False

                # Check if this iteration was triggered by an event (settings change)
                is_forced_update = self.app.update_event.is_set()
                self.app.update_event.clear()

                try:
                    wait_time = await self._perform_rpc_cycle(tracker, is_forced_update)
                    await self._wait_responsive(wait_time)

                except APIKeyError as e:
                    await self.app.handle_api_error(e)
                    # Loop stays idle waiting for update_event (triggered by settings save)
                    while not self.app.update_event.is_set() and not self.app.exit_event.is_set():
                        await asyncio.sleep(1.0)
                    continue

                except DiscordError as e:
                    logger.warning(f"Discord RPC error: {e}. Will retry in next cycle.")
                    # Fallback: application keeps running, just Discord status fails
                    await self.app.rpc.disable()

                except AppNetworkError as e:
                    logger.warning(f"Connection issue: {e}. Retrying after cooldown...")
                    # Optional: notify tray about connection issues

                except LastFMError as e:
                    logger.warning(f"Last.fm data error: {e}. Retrying...")

                except Exception as e:
                    logger.error(f"Unexpected error in RPC loop: {e}", exc_info=True)

                await self._wait_responsive(5.0)  # Cooldown after error or cycle
        finally:
            logger.info("Closing Scraper and Discord connection...")
            await self.scraper.close()
            await self.app.rpc.disable()

    async def _perform_rpc_cycle(self, tracker, is_forced_update):
        """
        Executes a single cycle of the RPC update process.
        Returns the wait time for the next cycle.
        """
        if is_forced_update and self.cached_track_data:
            current_track, data = self.cached_track_data
        else:
            current_track, data = await asyncio.to_thread(tracker.now_playing)
            if data:
                self.cached_track_data = (current_track, data)

        if data:
            user_state, lib_data = await self._get_metadata_with_cache(current_track, data.artist, data.title)
            if user_state and lib_data:
                await self._handle_active_track(current_track, data, user_state, lib_data, is_forced_update)
            return project.TRACK_CHECK_INTERVAL

        await self._handle_no_track()
        self.cached_track_data = None
        return project.UPDATE_INTERVAL

    async def _get_metadata_with_cache(self, track_obj, artist, title) -> tuple[UserState | None, dict | None]:
        """Fetch user and library data with caching logic."""
        if self.last_fetched_track == track_obj and self.cached_user_data and self.cached_library_data:
            logger.debug(f"Using cached Last.fm stats for {track_obj}")
            return self.cached_user_data, self.cached_library_data

        user_state, library_data = await asyncio.gather(
            self.scraper.get_user_state(), self.scraper.get_library_data(artist, title)
        )

        if not user_state:
            logger.error(f"User data not found for {config.username}")
            return None, None

        # Update cache
        self.last_fetched_track = track_obj
        self.cached_user_data = user_state
        self.cached_library_data = library_data

        return user_state, library_data

    async def _wait_responsive(self, seconds: float):
        """Waits for a given time but remains responsive to exit/update events."""
        for _ in range(int(seconds * 2)):
            if self.app.update_event.is_set() or self.app.exit_event.is_set():
                break
            await asyncio.sleep(0.5)

    async def _update_app_state(self, new_display_name, log_prefix="Status"):
        """Udpates application tracking state and refreshes UI if changed."""
        has_changed = (
            self.app.current_track_name != new_display_name or self.app._rpc_connected != self.app.rpc.is_connected
        )

        if has_changed:
            self.app.current_track_name = new_display_name
            self.app._rpc_connected = self.app.rpc.is_connected
            logger.info(f"{log_prefix}: {self.app.current_track_name} | Discord: {self.app._rpc_connected}")
            self.app.tray.update_title(new_display_name)
            self.app.tray.refresh()
            return True
        return False

    async def _handle_active_track(
        self, current_track, info: TrackInfo, user_state: UserState, lib_data: dict, is_forced_update=False
    ):
        """Handle the case where a track is playing."""
        formatted_track = f"{info.artist} - {info.title}"
        new_track_display = messenger("now_playing", formatted_track)

        if not await self._update_app_state(new_track_display):
            logger.debug(f"Polling: {formatted_track}")

        # Heavy data update
        await self.app.rpc.update_status(
            current_track, info, config.username, user_state, lib_data, force=is_forced_update
        )

    async def _handle_no_track(self):
        """Handle the case where no track is playing."""
        await self._update_app_state(messenger("no_track"), log_prefix="Tray Update")
        await self.app.rpc.clear_status()
