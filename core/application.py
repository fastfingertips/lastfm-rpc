import threading

from loguru import logger

from api.discord.rpc import DiscordRPC
from core.config import config
from core.tray import TrayManager
from services.sync_service import SyncService
from utils.autostart import toggle_autostart
from utils.dialogs import ask_yes_no, show_info
from utils.i18n import messenger
from utils.logger import setup_logging
from utils.urls import open_url

logger = logger.bind(name="app")


class App:
    """The central application orchestrator."""

    def __init__(self):
        self.rpc = DiscordRPC()
        self.current_track_name = messenger("no_track")
        self._rpc_connected = False
        self.debug_enabled = False

        # State management
        self.config_needs_reload = False
        self.latest_update = (False, None, None)
        self.update_event = threading.Event()
        self.exit_event = threading.Event()

        # Component Initialization
        self.tray = TrayManager(self)
        self.sync_service = SyncService(self)
        self.rpc_thread = threading.Thread(target=self.sync_service.start, daemon=True)

    def reload_config(self):
        """Refreshes everything after config update."""
        config.load()
        self.current_track_name = messenger("no_track")
        self.config_needs_reload = True
        self.update_event.set()
        self.tray.refresh()
        logger.info("Application reloaded.")

    def toggle_debug(self, icon, item):
        self.debug_enabled = not self.debug_enabled
        new_level = "DEBUG" if self.debug_enabled else "INFO"
        setup_logging(level=new_level)
        logger.info(f"Log level: {new_level}")

    def toggle_display_option(self, option):
        """Toggles a boolean RPC setting."""
        val = not getattr(config.rpc, option)
        config.update_rpc(option, val)
        self.update_event.set()
        self.tray.refresh()

    def set_small_image_option(self, option):
        """Radio behavior for small image source."""
        opts = ["use_custom_profile_image", "use_default_icon", "use_lastfm_icon", "use_custom_small_image"]
        for opt in opts:
            setattr(config.rpc, opt, opt == option)
        config.save_now()
        self.update_event.set()
        self.tray.refresh()

    def set_large_text_mode(self, mode):
        """Radio behavior for large image text."""
        if mode == "scrobbles":
            config.rpc.show_large_text, config.rpc.show_artist_scrobbles_large = True, True
        elif mode == "album":
            config.rpc.show_large_text, config.rpc.show_artist_scrobbles_large = True, False
        else:  # off
            config.rpc.show_large_text = False
        config.save_now()
        self.update_event.set()
        self.tray.refresh()

    def toggle_auto_start(self, icon=None, item=None):
        new_state = not config.auto_start_enabled
        if toggle_autostart(new_state):
            config.data.app.auto_start = new_state
            config.save_now()
            self.tray.refresh()

    async def handle_api_error(self, e):
        """Processes a fatal API error (e.g. wrong key) by updating UI and notifying user."""
        logger.critical(f"Stopping RPC loop due to API Key issue: {e}")
        self.update_status_display(messenger("api_error_status"), rpc_connected=False)
        await self.rpc.disable()
        self.tray.notify(str(e), messenger("action_required"))

        if ask_yes_no(messenger("err"), messenger("api_error_prompt", str(e))):
            self.tray.open_settings(None, None)

    def update_status_display(self, new_status, rpc_connected=None):
        """Standardized way to update the app's track status and refresh tray."""
        if rpc_connected is not None:
            self._rpc_connected = rpc_connected

        if self.current_track_name != new_status:
            self.current_track_name = new_status
            self.tray.update_title(new_status)
            self.tray.refresh()
            logger.info(f"Status Update: {new_status} | Discord: {self._rpc_connected}")

    def check_updates_manual(self, icon, item):
        def run():
            from utils.updater import check_for_updates

            is_avail, ver, url = check_for_updates()
            if is_avail:
                self.latest_update = (is_avail, ver, url)
                self.tray.refresh()
                if ask_yes_no(messenger("menu_check_updates"), messenger("update_available", ver)) and url:
                    open_url(url)
            else:
                show_info(messenger("menu_check_updates"), messenger("update_not_found"))

        threading.Thread(target=run, daemon=True).start()

    def _on_setup(self, icon):
        import time

        icon.visible = True
        time.sleep(0.5)
        self.rpc_thread.start()
        # Startup update check
        self._trigger_update_check()

    def _trigger_update_check(self):
        def run():
            from utils.updater import check_for_updates

            is_avail, ver, url = check_for_updates()
            if is_avail:
                self.latest_update = (is_avail, ver, url)
                self.tray.refresh()
                self.tray.notify(messenger("update_available", ver))

        threading.Thread(target=run, daemon=True).start()

    def run(self):
        self.tray.run(setup_callback=self._on_setup)

    def exit_app(self, icon=None, item=None):
        self.exit_event.set()
        import os

        os._exit(0)
