import os
import json
import datetime
from pypresence import Presence
from helpers.request_utils import get_response, get_dom
from helpers.string_utils import get_removal
from helpers.url_utils import url_encoder

client_id = '702984897496875072'
RPC = Presence(client_id)
enabled = False
disabled = True
start_time = None
last_track = None

def get_user_data(username):
    user_profile_url = f'https://www.last.fm/user/{username}'

    while True:
        response = get_response(user_profile_url)
        if response.status_code in range(200,299):
            # Display Name
            def parse_user_display_name(page_content): # get the display name of the user
                display_name = page_content.find("span", {"class":"header-title-display-name"})
                display_name = display_name.text.strip()
                return display_name

            # Avatar Url
            def parse_user_avatar_url(page_content): # get the avatar url of the user
                defaultAvatarId = "818148bf682d429dc215c1705eb27b98" # default avatar id
                defaultImageUrl = f"https://lastfm.freetls.fastly.net/i/u/avatar170s/{defaultAvatarId}.png" # default avatar url
                profileAvatarUrl = page_content.find("meta", property="og:image")["content"] # find the profile avatar url
                profileAvatarUrl = profileAvatarUrl.replace("/avatar170s","") # remove the size of the avatar
                avatarSuffix = os.path.splitext(profileAvatarUrl)[1] # get the suffix of the avatar
                profileAvatarUrl = profileAvatarUrl.replace(avatarSuffix,".gif") # replace the suffix with .gif
                if defaultAvatarId in profileAvatarUrl:
                    profileAvatarUrl = None # "No Avatar (Last.fm default avatar)"
                return profileAvatarUrl

            # Header Status
            def parse_user_header_status(page_content): # get the header status of the user
                headerStatus = [0, 0, 0]
                headers = page_content.find_all("div", {"class": "header-metadata-display"})
                for i in range(len(headers)):
                    headerStatus[i] = headers[i].text.strip()
                    headerStatus[i] = get_removal(headerStatus[i],',', int) # {} içerisindeki {}'i kaldır ve {} olarak geri al.
                return headerStatus

            dom = get_dom(response)
            data = {
                "display_name": parse_user_display_name(dom),
                "avatar_url": parse_user_avatar_url(dom),
                "header_status": parse_user_header_status(dom)
            }

            return data

def get_library_data(username, artistName, trackName):

    # get artist info
    def parse_artist_count(dom):
        data = dom.find_all("p", {"class":"metadata-display"})
        if bool(data):
            data = data[0].text if len(data) != 0 else '0' # if there is no artist info, return 0
        else: # empty list
            print('Arist info is empty list')
            data = 0
        return data

    # get track info
    def parse_track_count(dom):
        data = dom.find_all("p", {"class":"metadata-display"})
        if bool(data):
            data = data[0].text if len(data) != 0 else '0' # if there is no track info, return 0
        else: # empty list
            print('Track info is empty list')
            data = 0
        return data

    user_library_url = f'https://www.last.fm/user/{username}/library/music'
    libs = {
        "artists_url" : f'{user_library_url}/+noredirect/{url_encoder(artistName)}', # + ?date_preset=ALL (login req)
        "tracks_url" : f'{user_library_url}/+noredirect/{url_encoder(artistName)}/_/{url_encoder(trackName)}' # + ?date_preset=ALL (login req)
        }
    data = {}

    for url in libs:
        response = get_response(libs[url])
        dom = get_dom(response)

        if libs[url] == libs["artists_url"]: # if the url is the artist url
            artist_count = parse_artist_count(dom)
            data["artist_count"] = get_removal(artist_count,',', int)
            # print(f'{artistName}: {data["artist_count"]}')
        elif libs[url] == libs["tracks_url"]: # if the url is the track url
            track_count = parse_track_count(dom)
            data["track_count"] = get_removal(track_count,',', int)
            # print(f'{artistName} - {trackName}: {data["track_count"]}')
        else:
            print("This url is not supported:", libs[url])

    return data

def update_status(track, title, artist, album, time_remaining, username, artwork):
    # print name and value
    for f in [track, title, artist, album, time_remaining, username, artwork]:
        print(f)
    global start_time, last_track
    if len(title) < 2: title = title + ' '
    if last_track == track: pass # if the track is the same as the last track, don't update the status
    else: # if the track is different, update the status
        albumBool = album is not None
        timeRemainingBool = time_remaining > 0
        if timeRemainingBool:
            time_remaining = str(time_remaining)[0:3]
        
        print(f'Album: {albumBool:5}: {album}')
        print(f'Time Remaining: {timeRemainingBool}: {time_remaining}')
        print("Now Playing: " + track)

        start_time = datetime.datetime.now().timestamp()
        last_track = track
        trackArtistAlbum = f'{artist} - {album}'

        rpcButtons = [
        {"label": "View Track",
         "url": str(f"https://www.last.fm/tr/user/{username}/library/music/{url_encoder(artist)}/_/{url_encoder(title)}")},
        {"label": "Search on Spotify",
         "url": str(f"https://open.spotify.com/search/{url_encoder(album)}")}]
       #{"label": "View Track",
       # "url": str(f"https://www.last.fm/music/{url_encoder(artist)}/{url_encoder(title)}")}
       #{"label": "View Last.fm Profile",
       # "url": str(f"https://www.last.fm/user/{username}")}

        user_data = get_user_data(username)

        user_display_name = user_data["display_name"]
        scrobbles, artists, loved_tracks = user_data["header_status"] # unpacking

        print(json.dumps(user_data, indent=2))
        library_data = get_library_data(username, artist, title)
        print(json.dumps(library_data, indent=2))

        rpcSmallImage = user_data["avatar_url"]

        smallImageLines = {
            'name':         f"{user_display_name} (@{username})",
            "scrobbles":    f'Scrobbles: {scrobbles}',
            "artists":      f'Artists: {artists}',
            "loved_tracks": f'Loved Tracks: {loved_tracks}'
            }

        largeImageLines = {}
        artistCount = library_data["artist_count"]

        # artwork
        if artwork == None: # if there is no artwork, use the default one
            now = datetime.datetime.now()
            isDay = now.hour >= 18 or now.hour < 9  #day: false, night: true
            artwork = 'https://i.imgur.com/GOVbNaF.png' if isDay else 'https://i.imgur.com/kvGS4Pa.png'
            largeImageLines['theme'] = f"{'Night' if isDay else 'Day'} Mode Cover"
        else: pass

        if artistCount: # if the artist is in the library
            trackCount = library_data["track_count"]
            largeImageLines["artist_scrobbles"] = f'Scrobbles: {artistCount}/{trackCount}' if trackCount else f'Scrobbles: {artistCount}'
        else:
            largeImageLines['first_time'] = f'First time listening!'

        # line process
        rpcSmallImageText = ''
        rpcLargeImageText = ''
        lineLimit = 26
        xchar = ' '

        print(len(largeImageLines), largeImageLines)
        for line_key in smallImageLines:
            line = f'{smallImageLines[line_key]} '
            lineSuffix = "" if len(line) > 20 else (lineLimit - len(line) - sum(_.isupper() for _ in line))*xchar
            rpcSmallImageText += f'{line}{lineSuffix} '

        for line_key in largeImageLines:
            line = f'{largeImageLines[line_key]} '
            if len(largeImageLines) == 1: rpcLargeImageText = line
            else:
                """lineSuffix = "" if len(line) > 20 else (lineLimit - len(line) - sum(_.isupper() for _ in line))*xchar
                rpcLargeImageText += f'{line}{lineSuffix} '"""
                rpcLargeImageText += f'{line}{(lineLimit - len(line) - sum(_.isupper() for _ in line))*xchar} '

         # if the text is too long, cut it
        if len(rpcSmallImageText) > 128: rpcSmallImageText = rpcSmallImageText.replace(xchar,'')
        if len(rpcLargeImageText) > 128: rpcLargeImageText = rpcLargeImageText.replace(xchar,'')

        updateAssets = {
            'details': title,
            'buttons': rpcButtons,
            'small_image': rpcSmallImage,
            'small_text': rpcSmallImageText,
            'large_text': rpcLargeImageText,
            # situation-dependent assets
            'large_image': 'artwork' if not timeRemainingBool and not albumBool else artwork,
            'state': trackArtistAlbum if timeRemainingBool and not albumBool else artist,
            'end': float(time_remaining)+start_time if timeRemainingBool else None}

        if timeRemainingBool:
            if albumBool: print('Updating status with album, time remaining.')
            else: print('Updating status without album, time remaining.')
        else:
            if albumBool: print('Updating status with album, no time remaining')
            else: print('Updating status without album, no time remaining')
        try:
            RPC.update(**updateAssets)
        except Exception as e:
            print('x', e)


def enable():
    """
    Connects to Discord if not already connected.
    
    This function checks if the connection to Discord is not already enabled.
    If not, it establishes the connection, prints a confirmation message, and 
    updates the global state variables accordingly.
    """
    global enabled, disabled
    if not enabled:
        RPC.connect()  # Establish the connection to Discord
        print('Connected with Discord')
        enabled = True
        disabled = False

def disable():
    """
    Disconnects from Discord due to inactivity on Last.fm.
    
    This function checks if the connection to Discord is not already disabled.
    If not, it clears the current RPC state, closes the connection, prints a 
    confirmation message, and updates the global state variables accordingly.
    """
    global enabled, disabled
    if not disabled:
        RPC.clear()  # Clear the current RPC state
        RPC.close()  # Close the connection to Discord
        print('Disconnected from Discord due to inactivity on Last.fm')
        disabled = True
        enabled = False