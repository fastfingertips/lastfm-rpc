import asyncio
from loguru import logger
import threading
import sys
import os

import constants.project as project
from utils.string_utils import messenger
from api.lastfm.models import TrackInfo
from api.lastfm.user.tracking import User
from api.discord.rpc import DiscordRPC
from core.tray import TrayManager

logger = logger.bind(name='app')

class App:
    def __init__(self):
        self.rpc = DiscordRPC()
        self.current_track_name = messenger('no_track')
        self._rpc_connected = False
        # Loguru doesn't use standard getEffectiveLevel. We'll use a local flag.
        self.debug_enabled = False 
        
        # Initialize flags and states
        self.config_needs_reload = False
        self.latest_update = (False, None, None)
        self.cached_track_data = None
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
        from utils.logging_config import setup_logging
        setup_logging(level=new_level)
        
        logger.info(f"Logging level set to: {new_level}")

    def toggle_display_option(self, option):
        """Toggles a display option for the Discord RPC."""
        current = getattr(self.rpc, option)
        setattr(self.rpc, option, not current)
        self.tray.refresh()
        logger.info(f"Toggled option '{option}' to {not current}. Triggering update.")
        # Trigger immediate update
        self.update_event.set()

    def set_small_image_option(self, option):
        """Sets the active small image source (Radio Button behavior)."""
        # Define mutually exclusive options
        options = ['use_custom_profile_image', 'use_default_icon', 'use_lastfm_icon']
        if option not in options:
            return

        # Disable all others, enable the selected one
        for opt in options:
            setattr(self.rpc, opt, opt == option)
        self.tray.refresh()
        logger.info(f"Set small image source to '{option}'. Triggering update.")
        self.update_event.set()

    def set_large_image_option(self, show_scrobbles):
        """Sets the mode for large image text (Radio Button behavior)."""
        # If show_scrobbles is True, we show scrobbles. If False, we fall back to Album Name.
        if self.rpc.show_artist_scrobbles_large == show_scrobbles:
            return
        self.rpc.show_artist_scrobbles_large = show_scrobbles
        self.tray.refresh()
        logger.info(f"Set large image mode to {'Scrobbles' if show_scrobbles else 'Album Name'}. Triggering update.")
        self.update_event.set()

    def _handle_active_track(self, current_track, info: TrackInfo, is_forced_update=False):
        """Handle the case where a track is playing."""
        formatted_track = f"{info.artist} - {info.title}"
        new_track_display = messenger('now_playing', formatted_track)
        
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
            current_track, info, project.USERNAME, force=is_forced_update
        )
        
        # 3. Refresh menu if changed
        if has_track_changed or has_conn_changed:
            self.tray.refresh()

    def _handle_no_track(self):
        """Handle the case where no track is playing."""
        if self.current_track_name != messenger('no_track') or self._rpc_connected != self.rpc.is_connected:
            self.current_track_name = messenger('no_track')
            self._rpc_connected = self.rpc.is_connected
            logger.info(f"Tray Update: No track detected | Discord: {self._rpc_connected}")
            self.tray.update_title(self.current_track_name)
        self.rpc.disable()
        self.tray.refresh()

    def run_rpc(self, loop):
        """Runs the RPC updater in a loop."""
        logger.info(messenger('starting_rpc'))
        asyncio.set_event_loop(loop)
        
        from api.lastfm.user.tracking import APIKeyError
        user = User(project.USERNAME)

        while True:
            # Check if config was reloaded via GUI
            if self.config_needs_reload:
                logger.info(f"Applying new configuration for user: {project.USERNAME}")
                user = User(project.USERNAME)
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
                self.current_track_name = messenger('api_error_status')
                self._rpc_connected = False
                self.rpc.disable()
                self.tray.update_title(self.current_track_name)
                self.tray.refresh()
                
                # Show tray notification first (ensure icon is seen)
                self.tray.notify(str(e), messenger('action_required'))
                
                # Ask the user if they want to open settings
                from tkinter import messagebox
                if messagebox.askyesno(messenger('err'), messenger('api_error_prompt', str(e))):
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
            self._handle_active_track(current_track, data, is_forced_update)
            return project.TRACK_CHECK_INTERVAL
        else:
            self._handle_no_track()
            self.cached_track_data = None
            return project.UPDATE_INTERVAL

    def check_updates_manual(self, icon, item):
        """Check for updates manually and show a message box."""
        from utils.update_checker import check_for_updates
        from tkinter import messagebox
        is_avail, ver_name, url = check_for_updates()
        if is_avail:
            self.latest_update = (is_avail, ver_name, url)
            self.tray.refresh()
            if messagebox.askyesno(messenger('menu_check_updates'), messenger('update_available', ver_name) + "\n\nDo you want to visit the download page?"):
                if url: import webbrowser; webbrowser.open(url)
        else:
            messagebox.showinfo(messenger('menu_check_updates'), messenger('update_not_found'))

    def trigger_startup_update_check(self):
        """Runs update check in a thread to not block startup."""
        def run_check():
            try:
                from utils.update_checker import check_for_updates
                is_avail, ver_name, url = check_for_updates()
                if is_avail:
                    self.latest_update = (is_avail, ver_name, url)
                    self.tray.refresh()
                    # Optional: Show notification if frozen
                    if getattr(sys, 'frozen', False):
                        self.tray.notify(messenger('update_available', ver_name))
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

