import os
import sys
import tkinter
import asyncio
import threading
from PIL import Image
from tkinter import messagebox
from pystray import Icon, Menu, MenuItem as item

from helpers.string_utils import messenger
from api.discord_rpc_api import DiscordRPC
from api.lastfm_api import LastFmUser

from constants.project import (
    API_SECRET,
    CLIENT_ID,
    USERNAME,
    API_KEY
)

rpc = DiscordRPC(CLIENT_ID)
rpc_state = True

def toggle_rpc(Icon, item):
    global rpc_state
    rpc_state = not item.checked

def exit(Icon, item):
    icon_tray.stop()

if getattr(sys, 'frozen', False):
    directory = os.path.dirname(sys.executable)
elif __file__:
    directory = os.path.dirname(__file__)

image_dir = os.path.join(directory, "assets/icon.png")

root = tkinter.Tk()
root.withdraw()

try: 
    icon_img = Image.open(image_dir)
except FileNotFoundError as identifier:
    messagebox.showerror(messenger('err'), messenger('err_assets'))

print(messenger('fm_user_msg', USERNAME))
User = LastFmUser(API_KEY, API_SECRET, USERNAME)

menu_icon = Menu(
    item(messenger('user', USERNAME), None),
    item(messenger('enable_rpc'),toggle_rpc, checked=lambda item: rpc_state),
    Menu.SEPARATOR,
    item(messenger('exit'), exit))

icon_tray = Icon(
    'Last.fm Discord Rich Presence',
    icon=icon_img,
    title="Last.fm Discord Rich Presence",
    menu=menu_icon)

def app(loop):
    print(messenger('starting_rpc'))
    asyncio.set_event_loop(loop)
    while True:
        if rpc_state:
            data = User.now_playing()
            if data:
                current_track, title, artist, album, artwork, time_remaining = data
                rpc.enable()
                rpc.update_status(
                    str(current_track),
                    str(title),
                    str(artist),
                    str(album),
                    time_remaining,
                    USERNAME,
                    artwork
                    )
                continue
        rpc.disable()

loop = asyncio.new_event_loop()

rpc_thread = threading.Thread(target=app, args=(loop,))
rpc_thread.daemon = True
rpc_thread.start()

icon_tray.run()
