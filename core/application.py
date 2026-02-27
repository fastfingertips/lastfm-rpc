import asyncio
import os
import sys
import threading

from loguru import logger

import constants.project as project
from api.discord.rpc import DiscordRPC
from api.lastfm.models import TrackInfo, UserState
from api.lastfm.user.tracking import User
from api.lastfm.user.library import get_library_data
from api.lastfm.user.profile import get_user_data
from core.config import config
from core.tray import TrayManager
from utils.dialogs import ask_yes_no, show_info
from utils.i18n import messenger
from utils.urls import open_url

logger = logger.bind(name="app")


class App:
    def __init__(self):
        self.rpc = DiscordRPC()
        self.current_track_name = messenger("no_track")
        self._rpc_connected = False
        # Loguru doesn't use standard getEffectiveLevel. We'll use a local flag.
        self.debug_enabled = False

        # Initialize flags and states
        self.config_needs_reload = False
        self.latest_update = (False, None, None)
        self.cached_track_data = None
        self.cached_user_data = None
        self.cached_library_data = None
        self.last_fetched_track = None
        self.update_event = threading.Event()

        # Initialize UI Manager
        self.tray = TrayManager(self)

        self.loop = asyncio.new_event_loop()
        self.rpc_thread = threading.Thread(target=self.run_rpc, args=(self.loop,))
        self.rpc_thread.daemon = True

    def exit_app(self, icon=None, item=None):
        """Cleanly exits the application."""
        logger.info("Exiting application.")
        self.rpc.disable()
        self.tray.stop()
        os._exit(0)

    def toggle_debug(self, icon, item):
        """Toggles between DEBUG and INFO logging levels."""
        self.debug_enabled = not self.debug_enabled
        new_level = "DEBUG" if self.debug_enabled else "INFO"

        # In loguru, we change the level by removing and re-adding handlers
        # but for simplicity in a desktop app, we can just use the bound logger's logic
        # or reconfiguration. Here we re-setup with the new level.
        from utils.logger import setup_logging

        setup_logging(level=new_level)

        logger.info(f"Logging level set to: {new_level}")

    def toggle_display_option(self, option):
        """Toggles a display option for the Discord RPC."""
        current = getattr(config.rpc, option)
        setattr(config.rpc, option, not current)
        config.save()
        self.tray.refresh()
        logger.info(f"Toggled option '{option}' to {not current}. Triggering update.")
        # Trigger immediate update
        self.update_event.set()

    def set_small_image_option(self, option):
        """Sets the active small image source (Radio Button behavior)."""
        options = ["use_custom_profile_image", "use_default_icon", "use_lastfm_icon"]
        if option not in options:
            return

        # Disable all others, enable the selected one
        for opt in options:
            setattr(config.rpc, opt, opt == option)
        
        config.save()
        self.tray.refresh()
        logger.info(f"Set small image source to '{option}'. Triggering update.")
        self.update_event.set()

    def set_large_image_option(self, show_scrobbles):
        """Sets the mode for large image text (Radio Button behavior)."""
        if config.rpc.show_artist_scrobbles_large == show_scrobbles:
            return
        config.rpc.show_artist_scrobbles_large = show_scrobbles
        config.save()
        self.tray.refresh()
        logger.info(f"Set large image mode to {'Scrobbles' if show_scrobbles else 'Album Name'}. Triggering update.")
        self.update_event.set()

    def _perform_rpc_cycle(self, user, is_forced_update):
        """
        Executes a single cycle of the RPC update process.
        Returns the wait time for the next cycle.
        """
        # If forced update and we have cached data, reuse it without polling Last.fm
        if is_forced_update and self.cached_track_data:
            current_track, data = self.cached_track_data
        else:
            # Normal poll cycle
            current_track, data = user.now_playing()
            if data:
                self.cached_track_data = (current_track, data)

        if data:
            # Fetch additional metadata (User stats, library scrobbles)
            user_state, lib_data = self._get_metadata_with_cache(current_track, data.artist, data.title)
            if user_state and lib_data:
                self._handle_active_track(current_track, data, user_state, lib_data, is_forced_update)
            return project.TRACK_CHECK_INTERVAL

        self._handle_no_track()
        self.cached_track_data = None
        return project.UPDATE_INTERVAL

    def _get_metadata_with_cache(self, track_obj, artist, title) -> tuple[UserState | None, dict | None]:
        """Fetch user and library data with caching logic."""
        if self.last_fetched_track == track_obj and self.cached_user_data and self.cached_library_data:
            logger.debug(f"Using cached Last.fm stats for {track_obj}")
            return self.cached_user_data, self.cached_library_data

        user_state = get_user_data(config.username)
        if not user_state:
            logger.error(f"User data not found for {config.username}")
            return None, None

        library_data = get_library_data(config.username, artist, title)

        # Update cache
        self.last_fetched_track = track_obj
        self.cached_user_data = user_state
        self.cached_library_data = library_data

        return user_state, library_data

    def _handle_active_track(self, current_track, info: TrackInfo, user_state: UserState, lib_data: dict, is_forced_update=False):
        """Handle the case where a track is playing."""
        formatted_track = f"{info.artist} - {info.title}"
        new_track_display = messenger("now_playing", formatted_track)

        # 1. IMMEDIATE UI UPDATE
        self.rpc.enable()

        has_track_changed = self.current_track_name != new_track_display
        has_conn_changed = self._rpc_connected != self.rpc.is_connected

        if has_track_changed or has_conn_changed:
            self.current_track_name = new_track_display
            self._rpc_connected = self.rpc.is_connected
            logger.info(f"Status: {self.current_track_name} | Discord: {self._rpc_connected}")
            self.tray.update_title(new_track_display)
        else:
            logger.debug(f"Polling: {formatted_track}")

        # 2. HEAVY DATA UPDATE
        self.rpc.update_status(
            current_track, info, config.username, user_state, lib_data, force=is_forced_update
        )

        # 3. Refresh menu if changed
        if has_track_changed or has_conn_changed:
            self.tray.refresh()

    def _handle_no_track(self):
        """Handle the case where no track is playing."""
        if self.current_track_name != messenger("no_track") or self._rpc_connected != self.rpc.is_connected:
            self.current_track_name = messenger("no_track")
            self._rpc_connected = self.rpc.is_connected
            logger.info(f"Tray Update: No track detected | Discord: {self._rpc_connected}")
            self.tray.update_title(self.current_track_name)
        self.rpc.disable()
        self.tray.refresh()

    def run_rpc(self, loop):
        """Runs the RPC updater in a loop."""
        logger.info(messenger("starting_rpc"))
        asyncio.set_event_loop(loop)

        from core.exceptions import APIKeyError

        user = User(config.username)

        while True:
            # Check if config was reloaded via GUI
            if self.config_needs_reload:
                logger.info(f"Applying new configuration for user: {config.username}")
                user = User(config.username)
                self.config_needs_reload = False

            # Check if this iteration was triggered by an event (settings change)
            is_forced_update = self.update_event.is_set()
            self.update_event.clear()

            try:
                wait_time = self._perform_rpc_cycle(user, is_forced_update)
                # Wait for next cycle or till an event is set
                if self.update_event.wait(wait_time):
                    continue
            except APIKeyError as e:
                logger.critical(f"Stopping RPC loop due to API Key issue: {e}")

                # Update UI state
                self.current_track_name = messenger("api_error_status")
                self._rpc_connected = False
                self.rpc.disable()
                self.tray.update_title(self.current_track_name)
                self.tray.refresh()

                # Show tray notification first (ensure icon is seen)
                self.tray.notify(str(e), messenger("action_required"))

                # Ask the user if they want to open settings
                if ask_yes_no(messenger("err"), messenger("api_error_prompt", str(e))):
                    # Call open_settings from the tray manager
                    self.tray.open_settings(None, None)

                # Stop the loop and wait for event (like settings save) to restart or stay idle
                logger.info("RPC loop is now idle. Waiting for configuration change...")
                self.update_event.wait()
                continue
            except Exception as e:
                logger.error(f"Unexpected error in RPC loop: {e}", exc_info=True)
                # Small cooldown after failure
                self.update_event.wait(5)


    def check_updates_manual(self, icon, item):
        """Check for updates manually in a non-blocking way."""

        def run_manual_check():
            from utils.updater import check_for_updates

            is_avail, ver_name, url = check_for_updates()

            if is_avail:
                self.latest_update = (is_avail, ver_name, url)
                self.tray.refresh()
                if (
                    ask_yes_no(
                        messenger("menu_check_updates"),
                        messenger("update_available", ver_name) + "\n\nDo you want to visit the download page?",
                    )
                    and url
                ):
                    open_url(url)
            else:
                show_info(messenger("menu_check_updates"), messenger("update_not_found"))

        threading.Thread(target=run_manual_check, daemon=True).start()

    def trigger_startup_update_check(self):
        """Runs update check in a thread to not block startup."""

        def run_check():
            try:
                from utils.updater import check_for_updates

                is_avail, ver_name, url = check_for_updates()
                if is_avail:
                    self.latest_update = (is_avail, ver_name, url)
                    self.tray.refresh()
                    # Optional: Show notification if frozen
                    if getattr(sys, "frozen", False):
                        self.tray.notify(messenger("update_available", ver_name))
            except Exception as e:
                logger.debug(f"Background update check failed: {e}")

        threading.Thread(target=run_check, daemon=True).start()

    def _on_setup(self, icon):
        """Callback to start backend tasks once the icon is running."""
        import time

        try:
            # Explicitly ensure icon is visible and give Windows a moment to register it
            icon.visible = True
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Initial icon setup notice: {e}")

        # Start the background thread
        logger.info("Starting RPC background thread...")
        self.rpc_thread.start()

        # Check for updates
        self.trigger_startup_update_check()

    def run(self):
        """Starts the system tray application."""
        logger.info("Starting application UI...")
        try:
            self.tray.run(setup_callback=self._on_setup)
        except Exception as e:
            logger.error(f"Application failed: {e}", exc_info=True)
