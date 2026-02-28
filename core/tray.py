import sys

from loguru import logger
from PIL import Image
from pystray import Icon, Menu, MenuItem

import constants.project as project
from core.config import config
from utils.clock import format_time
from utils.dialogs import ask_config_gui, show_error
from utils.i18n import messenger
from utils.paths import get_asset_path
from utils.urls import open_url

logger = logger.bind(name="app")


class TrayManager:
    def __init__(self, app):
        self.app = app
        self.icon = self.setup_tray_icon()
        self._settings_open = False

    def load_icon(self):
        """Loads the application icon from the assets directory."""
        icon_path = get_asset_path("last_fm.png")
        try:
            return Image.open(icon_path)
        except FileNotFoundError:
            show_error(messenger("err"), messenger("err_assets"))
            sys.exit(1)

    def setup_tray_icon(self):
        """Sets up the initial system tray icon."""
        icon_img = self.load_icon()

        return Icon(project.APP_NAME, icon=icon_img, title=project.APP_NAME, menu=self.setup_tray_menu())

    def setup_tray_menu(self):
        """Creates and returns the tray menu with dynamic items."""
        dynamic_items = []

        # ── 1. Update Notification ──────────────────────────────
        is_available, ver_name, url = self.app.latest_update
        if is_available:
            dynamic_items.append(MenuItem(messenger("update_available", ver_name), lambda icon, item: open_url(url)))
            dynamic_items.append(Menu.SEPARATOR)

        # ── 2. Primary Status & User Items ──────────────────────
        status_items = [
            MenuItem(messenger("user", config.username), self.open_profile),
            MenuItem(lambda item: self.app.current_track_name, None, enabled=False),
            MenuItem(self._get_dynamic_artist_stats, None, enabled=False),
            MenuItem(self._get_dynamic_discord_status, None, enabled=False),
            Menu.SEPARATOR,
        ]

        # ── 3. Configuration Sub-Menus ──────────────────────────
        config_menus = [
            MenuItem(messenger("menu_small_image_options"), self._setup_small_image_menu()),
            MenuItem(messenger("menu_large_image_options"), self._setup_large_image_menu()),
            Menu.SEPARATOR,
        ]

        # ── 4. Main Actions & App Controls ──────────────────────
        actions = [
            MenuItem(messenger("menu_settings"), self.open_settings),
            MenuItem(
                messenger("menu_auto_start"), self.app.toggle_auto_start, checked=lambda item: config.auto_start_enabled
            ),
            MenuItem(messenger("menu_check_updates"), self.app.check_updates_manual),
            MenuItem(messenger("debug_mode"), self.app.toggle_debug, checked=lambda item: self.app.debug_enabled),
            MenuItem(messenger("exit"), self.app.exit_app),
        ]

        return Menu(*dynamic_items, *status_items, *config_menus, *actions)

    def _setup_small_image_menu(self):
        """Builds the sub-menu for Small Image configuration."""
        return Menu(
            MenuItem(
                messenger("menu_show_small_image"),
                lambda item: self.app.toggle_display_option("show_small_image"),
                checked=lambda item: config.rpc.show_small_image,
            ),
            Menu.SEPARATOR,
            MenuItem(
                messenger("menu_use_custom_profile_image"),
                lambda item: self.app.set_small_image_option("use_custom_profile_image"),
                checked=lambda item: config.rpc.use_custom_profile_image,
                enabled=lambda item: config.rpc.show_small_image,  # type: ignore
            ),
            MenuItem(
                messenger("menu_use_default_icon"),
                lambda item: self.app.set_small_image_option("use_default_icon"),
                checked=lambda item: config.rpc.use_default_icon,
                enabled=lambda item: config.rpc.show_small_image,
            ),
            MenuItem(
                messenger("menu_use_lastfm_icon"),
                lambda item: self.app.set_small_image_option("use_lastfm_icon"),
                checked=lambda item: config.rpc.use_lastfm_icon,
                enabled=lambda item: config.rpc.show_small_image,
            ),
            MenuItem(
                "Use Custom URL",
                lambda item: self.app.set_small_image_option("use_custom_small_image"),
                checked=lambda item: config.rpc.use_custom_small_image,
                enabled=lambda item: config.rpc.show_small_image,
            ),
            Menu.SEPARATOR,
            MenuItem(
                messenger("menu_show_username"),
                lambda item: self.app.toggle_display_option("show_username"),
                checked=lambda item: config.rpc.show_username,
                enabled=lambda item: (
                    config.rpc.show_small_image and config.rpc.show_small_text and not config.rpc.use_custom_small_text
                ),
            ),
            MenuItem(
                messenger("menu_show_scrobbles"),
                lambda item: self.app.toggle_display_option("show_scrobbles"),
                checked=lambda item: config.rpc.show_scrobbles,
                enabled=lambda item: (
                    config.rpc.show_small_image and config.rpc.show_small_text and not config.rpc.use_custom_small_text
                ),
            ),
            MenuItem(
                messenger("menu_show_artists"),
                lambda item: self.app.toggle_display_option("show_artists"),
                checked=lambda item: config.rpc.show_artists,
                enabled=lambda item: (
                    config.rpc.show_small_image and config.rpc.show_small_text and not config.rpc.use_custom_small_text
                ),
            ),
            MenuItem(
                messenger("menu_show_loved"),
                lambda item: self.app.toggle_display_option("show_loved"),
                checked=lambda item: config.rpc.show_loved,
                enabled=lambda item: (
                    config.rpc.show_small_image and config.rpc.show_small_text and not config.rpc.use_custom_small_text
                ),
            ),
            MenuItem(
                "No Text",
                lambda item: self.app.toggle_display_option("show_small_text"),
                checked=lambda item: not config.rpc.show_small_text,
                enabled=lambda item: config.rpc.show_small_image and not config.rpc.use_custom_small_text,
            ),
            MenuItem(
                "Use Custom Text",
                lambda item: self.app.toggle_display_option("use_custom_small_text"),
                checked=lambda item: config.rpc.use_custom_small_text,
                enabled=lambda item: config.rpc.show_small_image,
            ),
        )

    def _setup_large_image_menu(self):
        """Builds the sub-menu for Large Image configuration."""
        return Menu(
            MenuItem(
                messenger("menu_show_artist_scrobbles"),
                lambda item: self.app.set_large_text_mode("scrobbles"),
                checked=lambda item: config.rpc.show_large_text and config.rpc.show_artist_scrobbles_large,
                enabled=lambda item: not config.rpc.use_custom_large_text,  # type: ignore
            ),
            MenuItem(
                messenger("menu_show_album_name"),
                lambda item: self.app.set_large_text_mode("album"),
                checked=lambda item: config.rpc.show_large_text and not config.rpc.show_artist_scrobbles_large,
                enabled=lambda item: not config.rpc.use_custom_large_text,
            ),
            MenuItem(
                "No Text",
                lambda item: self.app.set_large_text_mode("off"),
                checked=lambda item: not config.rpc.show_large_text,
                enabled=lambda item: not config.rpc.use_custom_large_text,
            ),
            MenuItem(
                "Use Custom Text",
                lambda item: self.app.toggle_display_option("use_custom_large_text"),
                checked=lambda item: config.rpc.use_custom_large_text,
            ),
            Menu.SEPARATOR,
            MenuItem(
                "Use Custom URL",
                lambda item: self.app.toggle_display_option("use_custom_large_image"),
                checked=lambda item: config.rpc.use_custom_large_image,
            ),
        )

    def _get_dynamic_discord_status(self, item):
        """Returns the current Discord status text for the menu."""
        is_connected = self.app.rpc.is_connected
        if is_connected and self.app.rpc.connection_time:
            time_str = format_time(self.app.rpc.connection_time)
            status_detail = messenger("connected_with_time", time_str)
        else:
            status_detail = messenger("connected") if is_connected else messenger("disconnected")
        return messenger("discord_status", status_detail)

    def _get_dynamic_artist_stats(self, item):
        """Returns the current artist scrobble stats for the menu."""
        if self.app.rpc.current_artist:
            count = self.app.rpc.artist_scrobbles if self.app.rpc.artist_scrobbles is not None else "..."
            return messenger("artist_scrobbles", [self.app.rpc.current_artist, count])

        # Fallback if track is detected but stats (artist name) not yet confirmed
        if self.app.current_track_name != messenger("no_track"):
            return messenger("stats_loading")
        return messenger("stats_idle")

    def open_profile(self, icon, item):
        """Opens the user's Last.fm profile in the default browser."""
        url = project.LASTFM_USER_URL.format(username=config.username)
        open_url(url)
        logger.info(f"Opened Last.fm profile: {url}")

    def open_settings(self, icon, item):
        """Opens the graphical settings window in a non-blocking thread."""
        import threading

        # Prevent multiple windows
        if self._settings_open:
            logger.warning("Settings window is already open.")
            return

        self._settings_open = True
        logger.info("Opening settings GUI.")

        # Access constants directly from module to get latest reloaded values
        current_vals = config.get_all_config()

        def save_and_reload(new_config):
            u = new_config.get("USER", {}).get("USERNAME")
            k = new_config.get("API", {}).get("KEY")
            s = new_config.get("API", {}).get("SECRET")
            lang = new_config.get("APP", {}).get("LANG")
            a = new_config.get("APP", {}).get("AUTO_START")
            rpc_data = new_config.get("RPC")

            if config.save(u, k, s, lang, auto_start=a, rpc_config=rpc_data):
                # Reload config to update all properties
                config.load()

                # Refresh UI and track
                self.app.current_track_name = messenger("no_track")
                self.app.config_needs_reload = True
                self.app.update_event.set()
                self.refresh()
                return True
            return False

        def run_gui():
            try:
                ask_config_gui(current_vals, save_and_reload)
            finally:
                self._settings_open = False

        # Launch in a background thread to keep tray responsive
        threading.Thread(target=run_gui, daemon=True).start()

    def refresh(self):
        """Refreshes the tray menu UI."""
        if self.icon:
            self.icon.menu = self.setup_tray_menu()

    def update_title(self, title):
        """Updates the tray icon hover title."""
        if self.icon:
            self.icon.title = f"{project.APP_NAME}\n{title}"

    def notify(self, message, title=None):
        """Show a system notification."""
        if self.icon:
            self.icon.notify(message, title or project.APP_NAME)

    def run(self, setup_callback):
        """Starts the system tray icons event loop."""
        self.icon.run(setup=setup_callback)

    def stop(self):
        """Stops the system tray icon."""
        self.icon.stop()
