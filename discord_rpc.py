import os
import time
import json
import random
import datetime
import requests
from base64 import decode
import urllib.parse as parse
from bs4 import BeautifulSoup
from pypresence import Presence

client_id = '702984897496875072'
RPC = Presence(client_id)
already_enabled = False
already_disabled = True
start_time = None
LastTrack = None

def urlEncoder(text):
    return parse.quote(text, safe='') # url encode the text

def getRemoval(inside_obj, find_obj=' ', return_type=None):
	if return_type == None:
		return_type = type(inside_obj)
    
	if type(inside_obj) != str: # int'de işlem yapılamaz
		inside_obj = str(inside_obj)
    
	if type(find_obj) != str:
		find_obj = str(find_obj)

	if find_obj in inside_obj:
		inside_obj = inside_obj.replace(find_obj,'')
		
	if return_type != type(inside_obj):
		if return_type == int:
			inside_obj = int(inside_obj)
		elif return_type == float:
			inside_obj = float(inside_obj)
	# print(f'{inside_obj}: {type(inside_obj)}')
	return inside_obj

def getResponse(url): # get the response of the request
    while True:
        response = requests.get(url)
        reponseCode = getResponseCode(response)
        print(reponseCode, url)
        if reponseCode in range(200,299): return response
        time.sleep(2)

def getResponseCode(response): # get the response code of the request
    return response.status_code

def getDom(response): return BeautifulSoup(response.content, 'html.parser')

def getUserInfos(username):
    userProfileUrl = f'https://www.last.fm/user/{username}'
    data = {}
    while True:
        response = getResponse(userProfileUrl)
        responseCode = getResponseCode(response)
        
        if responseCode in range(200,299):
            pageContent = getDom(response)

            # Dpslay Name
            def getDisplayName(dom): # get the display name of the user
                displayName = dom.find("span", {"class":"header-title-display-name"})
                displayName = displayName.text.strip()
                return displayName
            data["display_name"] = getDisplayName(pageContent)

            # Avatar Url
            def getAvatarUrl(dom): # get the avatar url of the user
                defaultAvatarId = "818148bf682d429dc215c1705eb27b98" # default avatar id
                defaultImageUrl = f"https://lastfm.freetls.fastly.net/i/u/avatar170s/{defaultAvatarId}.png" # default avatar url
                profileAvatarUrl = pageContent.find("meta", property="og:image")["content"] # find the profile avatar url
                profileAvatarUrl = profileAvatarUrl.replace("/avatar170s","") # remove the size of the avatar
                avatarSuffix = os.path.splitext(profileAvatarUrl)[1] # get the suffix of the avatar
                profileAvatarUrl = profileAvatarUrl.replace(avatarSuffix,".gif") # replace the suffix with .gif
                if defaultAvatarId in profileAvatarUrl:
                    profileAvatarUrl = None # "No Avatar (Last.fm default avatar)"
                return profileAvatarUrl
            data["avatar_url"] = getAvatarUrl(pageContent)

            # Header Status
            def getHeaderStatus(dom): # get the header status of the user
                headerStatus = [0, 0, 0]
                headers = dom.find_all("div", {"class": "header-metadata-display"})
                for i in range(len(headers)):
                    headerStatus[i] = headers[i].text.strip()
                    headerStatus[i] = getRemoval(headerStatus[i],',', int) # {} içerisindeki {}'i kaldır ve {} olarak geri al.
                return headerStatus
            data["header_status"] = getHeaderStatus(pageContent)

            return data

def getLibraryInfo(username, artistName, trackName):
    libraryUrl = f'https://www.last.fm/user/{username}/library/music'
    libs = {
        "artists_url" : f'{libraryUrl}/+noredirect/{urlEncoder(artistName)}', # + ?date_preset=ALL (login req)
        "tracks_url" : f'{libraryUrl}/+noredirect/{urlEncoder(artistName)}/_/{urlEncoder(trackName)}' # + ?date_preset=ALL (login req)
        }

    data = {}
    for url in libs:
        response = getResponse(libs[url])
        pageContent = getDom(response)
        if libs[url] == libs["artists_url"]: # if the url is the artist url
            def getArtistInfo(dom):
                artistInfo = dom.find_all("p", {"class":"metadata-display"})
                if bool(artistInfo):
                    artistInfo = artistInfo[0].text if len(artistInfo) != 0 else '0' # if there is no artist info, return 0   
                else: # empty list
                    print('Arist info is empty list')
                    artistInfo = 0
                return artistInfo
            artistCount = getArtistInfo(pageContent)
            data["artist_count"] = getRemoval(artistCount,',', int)
            # print(f'{artistName}: {data["artist_count"]}')
        elif libs[url] == libs["tracks_url"]: # if the url is the track url
            def getTrackInfo(dom):
                trackInfo = dom.find_all("p", {"class":"metadata-display"})
                if bool(trackInfo):
                    trackInfo = trackInfo[0].text if len(trackInfo) != 0 else '0' # if there is no track info, return 0
                else: # empty list
                    print('Track info is empty list')
                    trackInfo = 0
                return trackInfo
            trackCount = getTrackInfo(pageContent)
            data["track_count"] = getRemoval(trackCount,',', int)
            # print(f'{artistName} - {trackName}: {data["track_count"]}')
        else: print("This url is not supported:", libs[url])

    return data

def enable_RPC():
    global already_enabled, already_disabled
    if already_enabled == False:
        RPC.connect()
        print('Connected with Discord')
        already_enabled = True
        already_disabled = False

def update_Status(track, title, artist, album, time_remaining, username, artwork):
    # print name and value
    for f in [track, title, artist, album, time_remaining, username, artwork]:
        print(f)
    global start_time, LastTrack
    if len(title) < 2: title = title + ' '
    if LastTrack == track: pass # if the track is the same as the last track, don't update the status
    else: # if the track is different, update the status
        albumBool = album is not None
        timeRemainingBool = time_remaining > 0
        if timeRemainingBool:
            time_remaining = str(time_remaining)[0:3]
        
        print(f'Album: {albumBool:5}: {album}')
        print(f'Time Remaining: {timeRemainingBool}: {time_remaining}')
       
        print("Now Playing: " + track)
        start_time = datetime.datetime.now().timestamp()
        LastTrack = track
        trackArtistAlbum = f'{artist} - {album}'

        rpcButtons = [
        {"label": "View Track", "url": str(f"https://www.last.fm/tr/user/{username}/library/music/{urlEncoder(artist)}/_/{urlEncoder(title)}")},
        {"label": "Search on Spotify" , "url": str(f"https://open.spotify.com/search/{urlEncoder(album)}")}]
       #{"label": "View Track", "url": str(f"https://www.last.fm/music/{urlEncoder(artist)}/{urlEncoder(title)}")}
       #{"label": "View Last.fm Profile", "url": str(f"https://www.last.fm/user/{username}")}

        userInfos = getUserInfos(username)

        displayName = userInfos["display_name"]
        scrobbles, artists, lovedTracks = userInfos["header_status"] # unpacking

        print(json.dumps(userInfos, indent=2))
        libraryInfos = getLibraryInfo(username, artist, title)
        print(json.dumps(libraryInfos, indent=2))

        rpcSmallImage = userInfos["avatar_url"]

        smallImageLines = {
            'name':         f"{displayName} (@{username})",
            "scrobbles":    f'Scrobbles: {scrobbles}',
            "artists":      f'Artists: {artists}',
            "loved_tracks": f'Loved Tracks: {lovedTracks}'
            }

        largeImageLines = {}
        artistCount = libraryInfos["artist_count"]

        # artwork
        if artwork == None: # if there is no artwork, use the default one
            now = datetime.datetime.now()
            isDay = now.hour >= 18 or now.hour < 9  #day: false, night: true
            artwork = 'https://i.imgur.com/GOVbNaF.png' if isDay else 'https://i.imgur.com/kvGS4Pa.png'
            largeImageLines['theme'] = f"{'Night' if isDay else 'Day'} Mode Cover"
        else: pass

        if artistCount: # if the artist is in the library
            trackCount = libraryInfos["track_count"]
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

def disable_RPC():
    global already_enabled
    global already_disabled
    if already_disabled == False:
        RPC.clear()
        RPC.close()
        print('Disconnected from Discord due to inactivity on Last.fm')
        already_disabled = True
        already_enabled = False

def disconnect():
    global already_enabled
    global already_disabled
    if already_disabled == False:
        RPC.clear()
        RPC.close()
        print('Disconnected from Discord')
        already_disabled = True
        already_enabled = False
