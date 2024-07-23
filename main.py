import os
import sys
import time
import yaml
import tkinter
import asyncio
import threading
import discord_rpc
from PIL import Image
from tkinter import messagebox
from lastfm_api import LastFmUser
from pystray import Icon, Menu, MenuItem as item

rpc_state = True

with open('config.yaml', 'r', encoding='utf-8') as config_file:
    try:
        config = yaml.safe_load(config_file)
        username = config['USER']['USERNAME']
        app_lang = config['APP']['LANG']
        print(f'Your username has been successfully set as {username}.')
    except yaml.YAMLError:
        print("YAMLError: Error loading configuration file.")
        sys.exit(1)
    except KeyError:
        print("KeyError: Configuration file does not contain the specified key.")
        sys.exit(1)

with open('translations.yaml', 'r', encoding='utf-8') as translations_file:
    try:
        translations = yaml.safe_load(translations_file)[app_lang]
        print('Translations have been successfully loaded from file.')
    except yaml.YAMLError:
        print("YAMLError: Error loading translations file.")
        sys.exit(1)

def msg(m, f=None):
    try:
        if f is None:
            return translations[m]
        else:
            return translations[m].format(str(f))
    except Exception as e:
        print(e)

def toggle_rpc(Icon, item):
    global rpc_state
    rpc_state = not item.checked


def exit(Icon, item):
    icon_tray.stop()

if getattr(sys, 'frozen', False):
    directory = os.path.dirname(sys.executable)
elif __file__:
    directory = os.path.dirname(__file__)

imageDir = os.path.join(directory, "assets/icon.png")

root = tkinter.Tk()
root.withdraw()

try: 
    icon_img = Image.open(imageDir)
except FileNotFoundError as identifier:
    messagebox.showerror(msg('err'), msg('err_assets'))

print(msg('fm_user_msg', username))
User = LastFmUser(username, 2)

menu_icon = Menu(
    item(msg('user', username), None),
    item(msg('enable_rpc'),toggle_rpc, checked=lambda item: rpc_state),
    Menu.SEPARATOR,
    item(msg('exit'), exit))

icon_tray = Icon(
    'Last.fm Discord Rich Presence',
    icon=icon_img,
    title="Last.fm Discord Rich Presence",
    menu=menu_icon)

def RPCFunction(loop):
    print(msg('starting_rpc'))
    asyncio.set_event_loop(loop)
    while True:
        if rpc_state == True:
            User.now_playing()
        else:
            discord_rpc.disable()
            time.sleep(2)

loop = asyncio.new_event_loop()
RPCThread = threading.Thread(target=RPCFunction, args=(loop,))

RPCThread.daemon = True
RPCThread.start()

icon_tray.run()
