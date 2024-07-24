import threading
import asyncio
import time

from pystray import Icon, Menu, MenuItem
from tkinter import messagebox
from PIL import Image

from api.lastfm.user.tracking import User
from api.discord.rpc import DiscordRPC

from helpers.string_utils import messenger

from libs.monitoring import logging
from libs.system import sys, os

from constants.project import USERNAME, APP_NAME

class App:
    def __init__(self):
        self.rpc = DiscordRPC()
        self.icon_tray = self.setup_tray_icon()
        self.loop = asyncio.new_event_loop()
        self.rpc_thread = threading.Thread(target=self.run_rpc, args=(self.loop,))
        self.rpc_thread.daemon = True

    def exit_app(self, icon, item):
        """Stops the system tray icon and exits the application."""
        logging.info("Exiting application.")
        icon.stop()
        sys.exit()

    def get_directory(self):
        """Returns the directory of the executable or script."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        elif __file__:
            return os.path.dirname(__file__)
        return ''

    def load_icon(self, directory):
        """Loads the application icon from the assets directory."""
        try:
            return Image.open(os.path.join(directory, "assets/last_fm.png"))
        except FileNotFoundError:
            messagebox.showerror(messenger('err'), messenger('err_assets'))
            sys.exit(1)

    def setup_tray_icon(self):
        """Sets up the system tray icon with menu options."""
        directory = self.get_directory()
        icon_img = self.load_icon(directory)
        menu_icon = Menu(
            MenuItem(messenger('user', USERNAME), None),
            Menu.SEPARATOR,
            MenuItem(messenger('exit'), self.exit_app)
        )
        return Icon(
            APP_NAME,
            icon=icon_img,
            title=APP_NAME,
            menu=menu_icon
        )

    def run_rpc(self, loop):
        """Runs the RPC updater in a loop."""
        logging.info(messenger('starting_rpc'))
        asyncio.set_event_loop(loop)
        user = User(USERNAME)

        while True:
            try:
                current_track, data = user.now_playing()
                if data:
                    title, artist, album, artwork, time_remaining = data
                    self.rpc.enable()
                    self.rpc.update_status(
                        str(current_track),
                        str(title),
                        str(artist),
                        str(album),
                        time_remaining,
                        USERNAME,
                        artwork
                    )
                    time.sleep(5)
                else:
                    self.rpc.disable()
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
            time.sleep(2)

    def run(self):
        """Starts the system tray application and RPC thread."""
        self.rpc_thread.start()
        self.icon_tray.run()

if __name__ == "__main__":
    app = App()
    app.run()