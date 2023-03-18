import DiscordRPC as RPC
import pylast
import time
import yaml
import sys

with open('config.yaml', 'r', encoding='utf-8') as config_file:
    try:
        config = yaml.safe_load(config_file)
        API_KEY = config['API']['KEY']
        API_SECRET = config['API']['SECRET']
        APP_LANG = config['APP']['LANG']
        print("API key and secret key have been successfully loaded from config file.")
    except yaml.YAMLError:
        print("YAMLError: Error loading configuration file.")
        sys.exit(1)
    except KeyError:
        print("KeyError: Configuration file does not contain the specified key.")
        sys.exit(1)

with open('translations.yaml', 'r', encoding='utf-8') as translations_file:
    try:
        translations = yaml.safe_load(translations_file)[APP_LANG]
        print('Translations have been successfully loaded from file.')
    except yaml.YAMLError:
        print("YAMLError: Error loading translations file.")
        sys.exit(1)

network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)

class LastFmUser:
    def __init__(self, username, cooldown):
        self.username = username
        self.user = network.get_user(username)
        self.cooldown = cooldown

    def now_playing(self):
        current_track = None
        try:
            current_track = self.user.get_now_playing()
            pass
        except pylast.WSError:
            print(translations['pylast_ws_error'].format(str(self.cooldown)))
            pass
        except pylast.NetworkError:
            print(translations['pylast_network_error'])
            pass
        except pylast.MalformedResponseError:
            print(translations['pylast_malformed_reponse_error'])
            pass

        if current_track is not None:
            track = current_track
            try:
                album,time_remaining = None, 0
                album = track.get_album()
                title = track.get_title()
                artist = track.get_artist()
                artwork = album.get_cover_image()
                time_remaining = track.get_duration()
            except pylast.WSError:
                pass
            except pylast.NetworkError:
                print(translations['pylast_network_error'])
                pass
            RPC.enable_RPC()
            RPC.update_Status(str(track), str(title), str(artist), str(album), time_remaining, self.username, artwork)
            time.sleep(self.cooldown+8)
        else:
            print(translations['no_song'].format(str(self.cooldown)))
            RPC.disable_RPC()
        time.sleep(self.cooldown)