from constants.project import DEFAULT_AVATAR_ID
from helpers.request_utils import get_response, get_dom
from helpers.string_utils import get_removal
from helpers.url_utils import url_encoder
from pypresence import Presence
import datetime
import os

class DiscordRPC:
    def __init__(self, client_id):
        self.RPC = Presence(client_id)
        self._enabled = False
        self._disabled = True
        self.start_time = None
        self.last_track = None

    def enable(self):
        """
        Connects to Discord if not already connected.
        
        Checks if the connection to Discord is not already enabled.
        If not, establishes the connection, prints a confirmation message, and 
        updates the instance state variables accordingly.
        """
        if not self._enabled:
            self.RPC.connect()  # Establish the connection to Discord
            print('Connected with Discord')
            self._enabled = True
            self._disabled = False

    def disable(self):
        """
        Disconnects from Discord due to inactivity on Last.fm.
        
        Checks if the connection to Discord is not already disabled.
        If not, clears the current RPC state, closes the connection, prints a 
        confirmation message, and updates the instance state variables accordingly.
        """
        if not self._disabled:
            self.RPC.clear()  # Clear the current RPC state
            self.RPC.close()  # Close the connection to Discord
            print('Disconnected from Discord due to inactivity on Last.fm')
            self._disabled = True
            self._enabled = False

    def update_status(self, track, title, artist, album, time_remaining, username, artwork):
        """
        for _ in [track, title, artist, album, time_remaining, username, artwork]:
            print(_)
        """

        if len(title) < 2:
            title = title + ' '

        if self.last_track == track:
            # if the track is the same as the last track, don't update the status
            pass
        else:
            # if the track is different, update the status
            album_bool = album is not None
            time_remaining_bool = time_remaining > 0
            if time_remaining_bool:
                time_remaining = float(str(time_remaining)[0:3])

            print(f'Album: {album_bool:5}: {album}')
            print(f'Time Remaining: {time_remaining_bool}: {time_remaining}')
            print("Now Playing: " + track)

            self.start_time = datetime.datetime.now().timestamp()
            self.last_track = track
            track_artist_album = f'{artist} - {album}'

            rpcButtons = [
            {"label": "View Track", "url": str(f"https://www.last.fm/tr/user/{username}/library/music/{url_encoder(artist)}/_/{url_encoder(title)}")},
            {"label": "Search on YouTube Music", "url": str(f"https://music.youtube.com/search?q={url_encoder(album)}")}
        #{"label": "Search on Spotify", "url": str(f"https://open.spotify.com/search/{url_encoder(album)}")}
        #{"label": "View Track", "url": str(f"https://www.last.fm/music/{url_encoder(artist)}/{url_encoder(title)}")}
        #{"label": "View Last.fm Profile", "url": str(f"https://www.last.fm/user/{username}")}
            ]

            user_data = get_user_data(username)
            #print(json.dumps(user_data, indent=2))

            user_display_name = user_data["display_name"]
            scrobbles, artists, loved_tracks = user_data["header_status"] # unpacking

            library_data = get_library_data(username, artist, title)
            #print(json.dumps(library_data, indent=2))

            rpc_small_image = user_data["avatar_url"]
            artist_count = library_data["artist_count"]

            large_image_lines = {}
            small_image_lines = {
                'name':         f"{user_display_name} (@{username})",
                "scrobbles":    f'Scrobbles: {scrobbles}',
                "artists":      f'Artists: {artists}',
                "loved_tracks": f'Loved Tracks: {loved_tracks}'}

            # artwork
            if artwork == None:
                # if there is no artwork, use the default one
                now = datetime.datetime.now()
                #day: false, night: true
                is_day = now.hour >= 18 or now.hour < 9 
                artwork = 'https://i.imgur.com/GOVbNaF.png' if is_day else 'https://i.imgur.com/kvGS4Pa.png'
                large_image_lines['theme'] = f"{'Night' if is_day else 'Day'} Mode Cover"
            else: pass

            if artist_count:
                # if the artist is in the library
                track_count = library_data["track_count"]
                large_image_lines["artist_scrobbles"] = f'Scrobbles: {artist_count}/{track_count}' if track_count else f'Scrobbles: {artist_count}'
            else:
                large_image_lines['first_time'] = f'First time listening!'

            # line process
            rpc_small_image_text = ''
            rpc_large_image_text = ''
            line_limit = 26
            xchar = ' '

            print(len(large_image_lines), large_image_lines)
            for line_key in small_image_lines:
                line = f'{small_image_lines[line_key]} '
                line_suffix = "" if len(line) > 20 else (line_limit - len(line) - sum(_.isupper() for _ in line))*xchar
                rpc_small_image_text += f'{line}{line_suffix} '

            for line_key in large_image_lines:
                line = f'{large_image_lines[line_key]} '
                if len(large_image_lines) == 1: rpc_large_image_text = line
                else:
                    """line_suffix = "" if len(line) > 20 else (line_limit - len(line) - sum(_.isupper() for _ in line))*xchar
                    rpc_large_image_text += f'{line}{line_suffix} '"""
                    rpc_large_image_text += f'{line}{(line_limit - len(line) - sum(_.isupper() for _ in line))*xchar} '

            # if the text is too long, cut it
            if len(rpc_small_image_text) > 128:
                rpc_small_image_text = rpc_small_image_text.replace(xchar,'')
            if len(rpc_large_image_text) > 128:
                rpc_large_image_text = rpc_large_image_text.replace(xchar,'')

            update_assets = {
                'details': title,
                'buttons': rpcButtons,
                'small_image': rpc_small_image,
                'small_text': rpc_small_image_text,
                'large_text': rpc_large_image_text,
                # situation-dependent assets
                'large_image': 'artwork' if not time_remaining_bool and not album_bool else artwork,
                'state': track_artist_album if time_remaining_bool and not album_bool else artist,
                'end': time_remaining + self.start_time if time_remaining_bool else None}

            if time_remaining_bool:
                if album_bool: print('Updating status with album, time remaining.')
                else: print('Updating status without album, time remaining.')
            else:
                if album_bool: print('Updating status with album, no time remaining')
                else: print('Updating status without album, no time remaining')
            try:
                self.RPC.update(**update_assets)
            except Exception as e:
                print('x', e)


def get_user_data(username) -> dict:

    USER_PROFILE_URL = f'https://www.last.fm/user/{username}'

    def parse_user_display_name(page_content):
                # get the display name of the user
                display_name = page_content.find("span", {"class":"header-title-display-name"})
                display_name = display_name.text.strip()
                return display_name

    def parse_user_avatar_url(page_content):
        # get the avatar url of the user
        # find the profile avatar url
        user_avatar_url = page_content.find("meta", property="og:image")["content"]
        # remove the size of the avatar
        user_avatar_url = user_avatar_url.replace("/avatar170s","")
        # get the suffix of the avatar
        avatar_suffix = os.path.splitext(user_avatar_url)[1]
        # replace the suffix with .gif
        user_avatar_url = user_avatar_url.replace(avatar_suffix, ".gif")
        if DEFAULT_AVATAR_ID in user_avatar_url:
            # "No Avatar (Last.fm default avatar)"
            user_avatar_url = None
        return user_avatar_url

    def parse_user_header_status(page_content):
        # get the header status of the user
        header_status = [0, 0, 0]
        headers = page_content.find_all("div", {"class": "header-metadata-display"})
        for i in range(len(headers)):
            header_status[i] = headers[i].text.strip()
            # {} içerisindeki {}'i kaldır ve {} olarak geri al.
            header_status[i] = get_removal(header_status[i],',', int)
        return header_status

    while True:
        response = get_response(USER_PROFILE_URL)
        if response.status_code in range(200,299):

            dom = get_dom(response)
            data = {
                "display_name": parse_user_display_name(dom),
                "avatar_url": parse_user_avatar_url(dom),
                "header_status": parse_user_header_status(dom)
            }

            return data

def get_library_data(username, artist_name, track_name) -> dict:

    USER_LIBRARY_URL = f'https://www.last.fm/user/{username}/library'
    # + ?date_preset=ALL (login req)
    USER_LIBRARY_ARTIST_URL = "/".join([USER_LIBRARY_URL, "music", "+noredirect", url_encoder(artist_name)])
    USER_LIBRARY_TRACK_URL = "/".join([USER_LIBRARY_URL, "music", "+noredirect", url_encoder(artist_name), "_", url_encoder(track_name)])

    def parse_count(dom):
        data = dom.find_all("p", {"class":"metadata-display"})
        if bool(data):
            # if there is no artist info, return 0
            data = data[0].text if len(data) != 0 else '0' 
            data = get_removal(data,',', int)
        else:
            # empty list
            print('Arist info is empty list')
            data = 0

        return data

    data = {
         'artist_count': parse_count(get_dom(get_response(USER_LIBRARY_ARTIST_URL))),
         'track_count': parse_count(get_dom(get_response(USER_LIBRARY_TRACK_URL)))
         }

    return data