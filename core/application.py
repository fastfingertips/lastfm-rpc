import os
import sys
import threading
import winreg

from loguru import logger

import constants.project as project
from api.discord.rpc import DiscordRPC
from core.config import config
from core.tray import TrayManager
from services.sync_service import SyncService
from utils.dialogs import ask_yes_no, show_info
from utils.i18n import messenger
from utils.urls import open_url

logger = logger.bind(name="app")


class App:
    def __init__(self):
        self.rpc = DiscordRPC()
        self.current_track_name = messenger("no_track")
        self._rpc_connected = False
        # Loguru uses custom level logic; using local flag for simplicity.
        self.debug_enabled = False

        # Initialize flags and states
        self.config_needs_reload = False
        self.latest_update = (False, None, None)
        self.update_event = threading.Event()
        self.exit_event = threading.Event()

        # Initialize UI Manager
        self.tray = TrayManager(self)

        # Initialize Sync Service
        self.sync_service = SyncService(self)

        self.rpc_thread = threading.Thread(target=self.sync_service.start)
        self.rpc_thread.daemon = True

    def exit_app(self, icon=None, item=None):
        """Cleanly exits the application."""
        logger.info("Exiting application...")
        self.exit_event.set()
        from contextlib import suppress

        # Give the thread a moment to close connections
        with suppress(Exception):
            self.rpc_thread.join(timeout=2.0)
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

    def reload_config(self):
        """Refreshes application state after a configuration change."""
        config.load()
        self.current_track_name = messenger("no_track")
        self.config_needs_reload = True
        self.update_event.set()
        self.tray.refresh()
        logger.info("Application state reloaded after config change.")

    async def handle_api_error(self, e):
        """Processes a fatal API error (e.g. wrong key) by updating UI and notifying user."""
        logger.critical(f"Stopping RPC loop due to API Key issue: {e}")

        # Update UI state
        self.current_track_name = messenger("api_error_status")
        self._rpc_connected = False
        await self.rpc.disable()
        self.tray.update_title(self.current_track_name)
        self.tray.refresh()

        # Show tray notification
        self.tray.notify(str(e), messenger("action_required"))

        # Ask the user if they want to open settings
        from utils.dialogs import ask_yes_no

        if ask_yes_no(messenger("err"), messenger("api_error_prompt", str(e))):
            self.tray.open_settings(None, None)

    def _finalize_config_change(self, log_msg):
        """Helper to save config, refresh UI, and trigger a background sync update."""
        config.save()
        self.tray.refresh()
        if log_msg:
            logger.info(log_msg)
        # Trigger immediate update in the background thread
        self.update_event.set()

    def toggle_display_option(self, option):
        """Toggles a display option for the Discord RPC."""
        current = getattr(config.rpc, option)
        setattr(config.rpc, option, not current)
        self._finalize_config_change(f"Toggled option '{option}' to {not current}.")

    def set_small_image_option(self, option):
        """Sets the active small image source (Radio Button behavior)."""
        options = ["use_custom_profile_image", "use_default_icon", "use_lastfm_icon", "use_custom_small_image"]
        if option not in options:
            return

        # Disable all others, enable the selected one
        for opt in options:
            setattr(config.rpc, opt, opt == option)

        self._finalize_config_change(f"Set small image source to '{option}'.")

    def set_large_text_mode(self, mode):
        """Sets the mode for large image text (Radio Button behavior).
        Modes: 'scrobbles', 'album', 'off'
        """
        if mode == "scrobbles":
            config.rpc.show_large_text = True
            config.rpc.show_artist_scrobbles_large = True
        elif mode == "album":
            config.rpc.show_large_text = True
            config.rpc.show_artist_scrobbles_large = False
        elif mode == "off":
            config.rpc.show_large_text = False

        self._finalize_config_change(f"Set large text mode to '{mode}'.")

    def toggle_auto_start(self, icon=None, item=None):
        """Toggles Windows auto-start registry key."""
        current = config.get_all_config().app.auto_start
        new_state = not current

        app_name = project.APP_NAME
        if getattr(sys, "frozen", False):
            # Running as bundled executable (Nuitka)
            app_path = f'"{sys.executable}"'
        else:
            # Running as script
            app_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
            if new_state:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                logger.info(f"Auto-start enabled: {app_path}")
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    logger.info("Auto-start disabled.")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)

            # Save and refresh
            config.get_all_config().app.auto_start = new_state
            self._finalize_config_change(f"Auto-start toggled to {new_state}")
        except Exception as e:
            logger.error(f"Failed to toggle auto-start: {e}")

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
