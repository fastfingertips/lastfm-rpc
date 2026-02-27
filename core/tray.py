import logging
import webbrowser
import sys
import os
from tkinter import messagebox
from pystray import Icon, Menu, MenuItem
from PIL import Image

import constants.project as project
from utils.string_utils import messenger

logger = logging.getLogger('app')

class TrayManager:
    def __init__(self, app):
        self.app = app
        self.icon = self.setup_tray_icon()
        self._settings_open = False

    def get_directory(self):
        """Returns the project root directory."""
        if getattr(sys, 'frozen', False):
            # If running as an executable
            return os.path.dirname(sys.executable)
        
        # When running as a script, get the parent of 'core' directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir)

    def load_icon(self, directory):
        """Loads the application icon from the assets directory."""
        try:
            return Image.open(os.path.join(directory, project.APP_ICON_PATH))
        except FileNotFoundError:
            messagebox.showerror(messenger('err'), messenger('err_assets'))
            sys.exit(1)

    def setup_tray_icon(self):
        """Sets up the initial system tray icon."""
        directory = self.get_directory()
        icon_img = self.load_icon(directory)
        
        return Icon(
            project.APP_NAME,
            icon=icon_img,
            title=project.APP_NAME,
            menu=self.setup_tray_menu()
        )

    def setup_tray_menu(self):
        """Creates and returns the tray menu with dynamic items."""
        dynamic_items = []
        
        # Add Update Item at the top if available
        is_available, ver_name, url = self.app.latest_update
        if is_available:
            dynamic_items.append(MenuItem(
                messenger('update_available', ver_name), 
                lambda icon, item: webbrowser.open(url) if url else None
            ))
            dynamic_items.append(Menu.SEPARATOR)

        return Menu(
            *dynamic_items,
            MenuItem(messenger('user', project.USERNAME), self.open_profile),
            MenuItem(lambda item: self.app.current_track_name, None, enabled=False),
            # Display stats item
            MenuItem(
                self._get_dynamic_artist_stats, 
                None, 
                enabled=False
            ),
            MenuItem(self._get_dynamic_discord_status, None, enabled=False),
            Menu.SEPARATOR,
            
            # Small Image Options
            MenuItem(messenger('menu_small_image_options'), Menu(
                MenuItem(messenger('menu_show_small_image'), lambda item: self.app.toggle_display_option('show_small_image'), checked=lambda item: self.app.rpc.show_small_image),
                Menu.SEPARATOR,
                MenuItem(messenger('menu_use_custom_profile_image'), lambda item: self.app.set_small_image_option('use_custom_profile_image'), checked=lambda item: self.app.rpc.use_custom_profile_image, enabled=self.app.rpc.show_small_image),
                MenuItem(messenger('menu_use_default_icon'), lambda item: self.app.set_small_image_option('use_default_icon'), checked=lambda item: self.app.rpc.use_default_icon, enabled=self.app.rpc.show_small_image),
                MenuItem(messenger('menu_use_lastfm_icon'), lambda item: self.app.set_small_image_option('use_lastfm_icon'), checked=lambda item: self.app.rpc.use_lastfm_icon, enabled=self.app.rpc.show_small_image),
                Menu.SEPARATOR,
                MenuItem(messenger('menu_show_username'), lambda item: self.app.toggle_display_option('show_username'), checked=lambda item: self.app.rpc.show_username, enabled=self.app.rpc.show_small_image),
                MenuItem(messenger('menu_show_scrobbles'), lambda item: self.app.toggle_display_option('show_scrobbles'), checked=lambda item: self.app.rpc.show_scrobbles, enabled=self.app.rpc.show_small_image),
                MenuItem(messenger('menu_show_artists'), lambda item: self.app.toggle_display_option('show_artists'), checked=lambda item: self.app.rpc.show_artists, enabled=self.app.rpc.show_small_image),
                MenuItem(messenger('menu_show_loved'), lambda item: self.app.toggle_display_option('show_loved'), checked=lambda item: self.app.rpc.show_loved, enabled=self.app.rpc.show_small_image)
            )),
            
            # Large Image Options
            MenuItem(messenger('menu_large_image_options'), Menu(
                MenuItem(messenger('menu_show_artist_scrobbles'), lambda item: self.app.set_large_image_option(True), checked=lambda item: self.app.rpc.show_artist_scrobbles_large),
                MenuItem(messenger('menu_show_album_name'), lambda item: self.app.set_large_image_option(False), checked=lambda item: not self.app.rpc.show_artist_scrobbles_large)
            )),
            
            Menu.SEPARATOR,
            MenuItem(messenger('menu_settings'), self.open_settings),
            MenuItem(messenger('menu_check_updates'), self.app.check_updates_manual),
            MenuItem(messenger('debug_mode'), self.app.toggle_debug, checked=lambda item: self.app.debug_enabled),
            MenuItem(messenger('exit'), self.app.exit_app)
        )

    def _get_dynamic_discord_status(self, item):
        """Returns the current Discord status text for the menu."""
        is_connected = self.app.rpc.is_connected
        if is_connected and self.app.rpc.connection_time:
            time_str = self.app.rpc.connection_time.strftime("%H:%M")
            status_detail = messenger('connected_with_time', time_str)
        else:
            status_detail = messenger('connected') if is_connected else messenger('disconnected')
        return messenger('discord_status', status_detail)

    def _get_dynamic_artist_stats(self, item):
        """Returns the current artist scrobble stats for the menu."""
        if self.app.rpc.current_artist:
            count = self.app.rpc.artist_scrobbles if self.app.rpc.artist_scrobbles is not None else "..."
            return messenger('artist_scrobbles', [self.app.rpc.current_artist, count])
        
        # Fallback if track is detected but stats (artist name) not yet confirmed
        if self.app.current_track_name != messenger('no_track'):
            return messenger('stats_loading')
        return messenger('stats_idle')

    def open_profile(self, icon, item):
        """Opens the user's Last.fm profile in the default browser."""
        url = project.LASTFM_USER_URL.format(username=project.USERNAME)
        webbrowser.open(url)
        logger.info(f"Opened Last.fm profile: {url}")

    def open_settings(self, icon, item):
        """Opens the graphical settings window in a non-blocking thread."""
        from utils.gui import ConfigGUI
        import threading
        
        # Prevent multiple windows
        if self._settings_open:
            logger.warning("Settings window is already open.")
            return
            
        self._settings_open = True
        logger.info("Opening settings GUI.")
        
        # Access constants directly from module to get latest reloaded values
        current_vals = (project.USERNAME, project.API_KEY, project.API_SECRET, project.APP_LANG)
        
        def save_and_reload(new_config):
            # Extract values from new_config dict
            u = new_config.get('USER', {}).get('USERNAME', project.USERNAME)
            k = new_config.get('API', {}).get('KEY', project.API_KEY)
            s = new_config.get('API', {}).get('SECRET', project.API_SECRET)
            l = new_config.get('APP', {}).get('LANG', project.APP_LANG)
            
            if project.config_manager.save(u, k, s, l):
                # Sync global variables in project.py
                project.reload_constants()
                
                # Refresh UI and track
                self.app.current_track_name = messenger('no_track')
                self.app.config_needs_reload = True
                self.refresh()
                return True
            return False

        def run_gui():
            try:
                gui = ConfigGUI(current_vals, save_and_reload)
                # Keep track of when it's closed
                def on_close():
                    self._settings_open = False
                    gui.root.quit()
                    gui.root.destroy()
                
                gui.root.protocol("WM_DELETE_WINDOW", on_close)
                gui.run()
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
