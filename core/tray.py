import sys
import threading

from loguru import logger
from PIL import Image
from pystray import Icon

import constants.project as project
from core.config import config
from core.tray_menu import TrayMenuFactory
from utils.dialogs import ask_config_gui, show_error
from utils.i18n import messenger
from utils.paths import get_asset_path
from utils.urls import open_url

logger = logger.bind(name="app")


class TrayManager:
    """Manages the system tray icon and UI interactions."""

    def __init__(self, app):
        self.app = app
        self.menu_factory = TrayMenuFactory(self)
        self.icon = self.setup_tray_icon()
        self._settings_open = False

    def load_icon(self):
        """Loads the application icon."""
        icon_path = get_asset_path("last_fm.png")
        try:
            return Image.open(icon_path)
        except Exception as e:
            logger.error(f"Failed to load tray icon: {e}")
            show_error(messenger("err"), messenger("err_assets"))
            sys.exit(1)

    def setup_tray_icon(self):
        """Initializes the pystray Icon."""
        return Icon(project.APP_NAME, icon=self.load_icon(), title=project.APP_NAME, menu=self.menu_factory.create())

    def open_profile(self, icon, item):
        """Opens Last.fm profile."""
        url = project.LASTFM_USER_URL.format(username=config.username)
        open_url(url)
        logger.info(f"Opened profile: {url}")

    def open_settings(self, icon, item):
        """Opens settings GUI in a separate thread."""
        if self._settings_open:
            return

        self._settings_open = True
        logger.info("Opening settings GUI.")

        def on_save(new_vals):
            # Modular delegate: Tray doesn't know HOW to save, it just calls config and app
            success = config.save(
                new_vals.get("USER", {}).get("USERNAME"),
                new_vals.get("API", {}).get("KEY"),
                new_vals.get("API", {}).get("SECRET"),
                new_vals.get("APP", {}).get("LANG"),
                auto_start=new_vals.get("APP", {}).get("AUTO_START"),
                rpc_config=new_vals.get("RPC"),
            )
            if success:
                self.app.reload_config()
                return True
            return False

        def run_gui():
            try:
                ask_config_gui(config.data, on_save)
            finally:
                self._settings_open = False

        threading.Thread(target=run_gui, daemon=True).start()

    def refresh(self):
        """Rebuilds the menu and refreshes the icon."""
        if self.icon:
            self.icon.menu = self.menu_factory.create()

    def update_title(self, title):
        """Updates hover tooltip."""
        if self.icon:
            self.icon.title = f"{project.APP_NAME}\n{title}"

    def notify(self, message, title=None):
        """Shows system notification."""
        if self.icon:
            self.icon.notify(message, title or project.APP_NAME)

    def run(self, setup_callback):
        self.icon.run(setup=setup_callback)

    def stop(self):
        self.icon.stop()
