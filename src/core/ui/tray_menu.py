from pystray import Menu, MenuItem

from core.config import config
from utils.app.i18n import messenger
from utils.core.clock import format_time


class TrayMenuFactory:
    def __init__(self, tray_manager):
        self.tm = tray_manager
        self.app = tray_manager.app

    def create(self):
        """Builds the complete tray menu tree."""
        dynamic_items = []

        # 1. Update Notification
        is_available, ver_name, url = self.app.latest_update
        if is_available:
            from utils.net.urls import open_url

            dynamic_items.append(MenuItem(messenger("update_available", ver_name), lambda i, item: open_url(url)))
            dynamic_items.append(Menu.SEPARATOR)

        # 2. Status & User Items
        status_items = [
            MenuItem(messenger("user", config.username), self.tm.open_profile),
            MenuItem(lambda item: self.app.current_track_name, None, enabled=False),
            MenuItem(self._get_dynamic_artist_stats, None, enabled=False),
            MenuItem(self._get_dynamic_discord_status, None, enabled=False),
            Menu.SEPARATOR,
        ]

        # 3. Configuration Sub-Menus
        config_menus = [
            MenuItem(messenger("menu_small_image_options"), self._setup_small_image_menu()),
            MenuItem(messenger("menu_large_image_options"), self._setup_large_image_menu()),
            Menu.SEPARATOR,
        ]

        # 4. Main Actions
        actions = [
            MenuItem(messenger("menu_settings"), self.tm.open_settings),
            MenuItem(
                messenger("menu_auto_start"), self.app.toggle_auto_start, checked=lambda item: config.auto_start_enabled
            ),
            MenuItem(messenger("menu_check_updates"), self.app.check_updates_manual),
            MenuItem(messenger("debug_mode"), self.app.toggle_debug, checked=lambda item: self.app.debug_enabled),
            MenuItem(messenger("exit"), self.app.exit_app),
        ]

        return Menu(*dynamic_items, *status_items, *config_menus, *actions)

    def _setup_small_image_menu(self):
        """Builds sub-menu for Small Image configuration."""
        return Menu(
            MenuItem(
                messenger("menu_show_small_image"),
                lambda i: self.app.toggle_display_option("show_small_image"),
                checked=lambda i: config.rpc.show_small_image,
            ),
            Menu.SEPARATOR,
            MenuItem(
                messenger("menu_use_custom_profile_image"),
                lambda i: self.app.set_small_image_option("use_custom_profile_image"),
                checked=lambda i: config.rpc.use_custom_profile_image,
                enabled=lambda i: config.rpc.show_small_image,
            ),
            MenuItem(
                messenger("menu_use_default_icon"),
                lambda i: self.app.set_small_image_option("use_default_icon"),
                checked=lambda i: config.rpc.use_default_icon,
                enabled=lambda i: config.rpc.show_small_image,
            ),
            MenuItem(
                messenger("menu_use_lastfm_icon"),
                lambda i: self.app.set_small_image_option("use_lastfm_icon"),
                checked=lambda i: config.rpc.use_lastfm_icon,
                enabled=lambda i: config.rpc.show_small_image,
            ),
            MenuItem(
                "Use Custom URL",
                lambda i: self.app.set_small_image_option("use_custom_small_image"),
                checked=lambda i: config.rpc.use_custom_small_image,
                enabled=lambda i: config.rpc.show_small_image,
            ),
            Menu.SEPARATOR,
            MenuItem(
                messenger("menu_show_username"),
                lambda i: self.app.toggle_display_option("show_username"),
                checked=lambda i: config.rpc.show_username,
                enabled=lambda i: (
                    config.rpc.show_small_image and config.rpc.show_small_text and not config.rpc.use_custom_small_text
                ),
            ),
            MenuItem(
                messenger("menu_show_scrobbles"),
                lambda i: self.app.toggle_display_option("show_scrobbles"),
                checked=lambda i: config.rpc.show_scrobbles,
                enabled=lambda i: (
                    config.rpc.show_small_image and config.rpc.show_small_text and not config.rpc.use_custom_small_text
                ),
            ),
            MenuItem(
                messenger("menu_show_artists"),
                lambda i: self.app.toggle_display_option("show_artists"),
                checked=lambda i: config.rpc.show_artists,
                enabled=lambda i: (
                    config.rpc.show_small_image and config.rpc.show_small_text and not config.rpc.use_custom_small_text
                ),
            ),
            MenuItem(
                messenger("menu_show_loved"),
                lambda i: self.app.toggle_display_option("show_loved"),
                checked=lambda i: config.rpc.show_loved,
                enabled=lambda i: (
                    config.rpc.show_small_image and config.rpc.show_small_text and not config.rpc.use_custom_small_text
                ),
            ),
            MenuItem(
                "No Text",
                lambda i: self.app.toggle_display_option("show_small_text"),
                checked=lambda i: not config.rpc.show_small_text,
                enabled=lambda i: config.rpc.show_small_image and not config.rpc.use_custom_small_text,
            ),
            MenuItem(
                "Use Custom Text",
                lambda i: self.app.toggle_display_option("use_custom_small_text"),
                checked=lambda i: config.rpc.use_custom_small_text,
                enabled=lambda i: config.rpc.show_small_image,
            ),
        )

    def _setup_large_image_menu(self):
        """Builds sub-menu for Large Image configuration."""
        return Menu(
            MenuItem(
                messenger("menu_show_artist_scrobbles"),
                lambda i: self.app.set_large_text_mode("scrobbles"),
                checked=lambda i: config.rpc.show_large_text and config.rpc.show_artist_scrobbles_large,
                enabled=lambda i: not config.rpc.use_custom_large_text,
            ),
            MenuItem(
                messenger("menu_show_album_name"),
                lambda i: self.app.set_large_text_mode("album"),
                checked=lambda i: config.rpc.show_large_text and not config.rpc.show_artist_scrobbles_large,
                enabled=lambda i: not config.rpc.use_custom_large_text,
            ),
            MenuItem(
                "No Text",
                lambda i: self.app.set_large_text_mode("off"),
                checked=lambda i: not config.rpc.show_large_text,
                enabled=lambda i: not config.rpc.use_custom_large_text,
            ),
            MenuItem(
                "Use Custom Text",
                lambda i: self.app.toggle_display_option("use_custom_large_text"),
                checked=lambda i: config.rpc.use_custom_large_text,
            ),
            Menu.SEPARATOR,
            MenuItem(
                "Use Custom URL",
                lambda i: self.app.toggle_display_option("use_custom_large_image"),
                checked=lambda i: config.rpc.use_custom_large_image,
            ),
        )

    def _get_dynamic_discord_status(self, item):
        is_connected = self.app.rpc.is_connected
        if is_connected and self.app.rpc.connection_time:
            time_str = format_time(self.app.rpc.connection_time)
            status_detail = messenger("connected_with_time", time_str)
        else:
            status_detail = messenger("connected") if is_connected else messenger("disconnected")
        return messenger("discord_status", status_detail)

    def _get_dynamic_artist_stats(self, item):
        if self.app.rpc.current_artist:
            count = self.app.rpc.artist_scrobbles if self.app.rpc.artist_scrobbles is not None else "..."
            return messenger("artist_scrobbles", [self.app.rpc.current_artist, count])
        if self.app.current_track_name != messenger("no_track"):
            return messenger("stats_loading")
        return messenger("stats_idle")
