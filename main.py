import os
import sys
import time
import asyncio
import threading
import logging
from PIL import Image
from tkinter import messagebox
from pystray import Icon, Menu, MenuItem as item

from helpers.string_utils import messenger
from api.discord.rpc import DiscordRPC
from api.lastfm.user.tracking import User
from constants.project import USERNAME

# Configure logging
logging.basicConfig(level=logging.INFO)

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
            item(messenger('user', USERNAME), None),
            Menu.SEPARATOR,
            item(messenger('exit'), self.exit_app)
        )
        return Icon(
            'Last.fm Discord Rich Presence',
            icon=icon_img,
            title="Last.fm Discord Rich Presence",
            menu=menu_icon
        )

    def run_rpc(self, loop):
        """Runs the RPC updater in a loop."""
        logging.info(messenger('starting_rpc'))
        asyncio.set_event_loop(loop)
        user = User(USERNAME)

        while True:
            try:
                data = user.now_playing()
                if data:
                    current_track, title, artist, album, artwork, time_remaining = data
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
                else:
                    self.rpc.disable()
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
            time.sleep(1)  # Adjust this if necessary to avoid excessive CPU usage

    def run(self):
        """Starts the system tray application and RPC thread."""
        self.rpc_thread.start()
        self.icon_tray.run()

if __name__ == "__main__":
    app = App()
    app.run()
