from base64 import decode
from pypresence import Presence
import datetime
import urllib.parse as parse
import requests
from bs4 import BeautifulSoup as bs 
import os

client_id = '702984897496875072'
RPC = Presence(client_id)
print(RPC)
already_enabled = False
already_disabled = True
start_time = None
LastTrack = None

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

def getHeaderStatus(profile_dom):
	headerStatus = [0, 0, 0]
	headers = profile_dom.find_all("div", {"class": "header-metadata-display"})
	for i in range(len(headers)):
		headerStatus[i] = headers[i].text.strip()
		headerStatus[i] = getRemoval(headerStatus[i],',', int) # {} içerisindeki {}'i kaldır ve {} olarak geri al.
	return headerStatus

def getUserInfos(userProfileUrl):
    while True:
        response = requests.get(userProfileUrl)
        responseCode = response.status_code
        
        if responseCode in range(200,299):
            pageContent = bs(response.content, 'html.parser')

            # Dpslay Name
            profileDisplayName = pageContent.find("span", {"class":"header-title-display-name"}) #display name
            
            # Avatar Url
            defaultAvatarId = "818148bf682d429dc215c1705eb27b98"
            #defaultImageUrl = ("https://lastfm.freetls.fastly.net/i/u/avatar170s/818148bf682d429dc215c1705eb27b98.png") 
            profileAvatarUrl = pageContent.find("meta", property="og:image")["content"] # find the profile avatar url
            profileAvatarUrl = profileAvatarUrl.replace("/avatar170s","") # remove the size of the avatar
            avatarSuffix = os.path.splitext(profileAvatarUrl)[1] # get the suffix of the avatar
            profileAvatarUrl = profileAvatarUrl.replace(avatarSuffix,".gif") # replace the suffix with .gif
            if defaultAvatarId in profileAvatarUrl:
                profileAvatarUrl = None # "No Avatar (Last.fm default avatar)"
            
            # Header Status
            headerStatus = getHeaderStatus(pageContent)

            return {"display_name": profileDisplayName.text.strip(),
                    "avatar_url": profileAvatarUrl,
                    "header_status" : headerStatus}

def getArtistInfo(username, artistName): # getting artist info from last.fm
    artistCountUrl = f'https://www.last.fm/user/{username}/library/music/+noredirect/{parse.quote(artistName)}?date_preset=ALL'
    response = requests.get(artistCountUrl)
    artistCountDom = bs(response.content, 'html.parser')
    artistCount = artistCountDom.find_all("p", {"class":"metadata-display"})[0].text
    return artistCount

def getTrackInfo(username, artistName, trackName):
    trackInfoUrl = f'https://www.last.fm/user/{username}/library/music/+noredirect/{parse.quote(artistName)}/_/{parse.quote(trackName)}?date_preset=ALL'
    response = requests.get(trackInfoUrl)
    trackInfoDom = bs(response.content, 'html.parser')
    trackInfo = trackInfoDom.find_all("p", {"class":"metadata-display"})[0].text
    return trackInfo

def enable_RPC():
    global already_enabled,already_disabled
    if already_enabled == False:
        RPC.connect()
        print('Connected with Discord')
        already_enabled = True
        already_disabled = False

def update_Status(track, title, artist, album, time_remaining, username, artwork):
    global start_time, LastTrack
    if len(title) < 2:
        title = title + ' '
    if LastTrack == track: #if the track is the same as the last track, don't update the status
        pass
    else: #if the track is different, update the status
        print("Now Playing: " + track)
        start_time = datetime.datetime.now().timestamp()
        LastTrack = track
        trackArtistAlbum = f'{artist} - {album}'
        time_remaining = str(time_remaining)[0:3]
        
        lastfmProfileButton = [
        {"label": "View Track", "url": str(f"https://www.last.fm/tr/user/{username}/library/music/{parse.quote(artist)}/_/{parse.quote(title)}")},
        {"label": "Search on Spotify" , "url": str(f"https://open.spotify.com/search/{parse.quote(album)}")}]
       #{"label": "View Track", "url": str(f"https://www.last.fm/music/{parse.quote(artist)}/{parse.quote(title)}")}
       #{"label": "View Last.fm Profile", "url": str(f"https://www.last.fm/user/{username}")}

        userPageUrl = f'https://www.last.fm/user/{username}'
        userInfos = getUserInfos(userPageUrl)
        rpcSmallImageText = f"{userInfos['display_name']} (@{username})"
        rpcSmallImage = userInfos["avatar_url"]
        
        # lineLimit = 34
        lineLimit = 26
        line1 = f'Scrobbles: {userInfos["header_status"][0]} '
        line1 += ((lineLimit - len(line1))*"•") + " "
        line2 = f'Artists: {userInfos["header_status"][1]} '
        line2 += ((lineLimit - len(line2))*"•") + " "
        line3 = f'Loved Tracks: {userInfos["header_status"][2]} '
        line3 += ((lineLimit - len(line3))*"•") + " "
        line4 = f"Artist's Scrobbles: {getArtistInfo(username, artist)}/{getTrackInfo(username, artist, title)} "
        line4 += ((lineLimit - len(line4))*"•") + " "

        #total = len(line1)+len(line2)+len(line3)+len(line4)
        
        rpcLargeImageText = f'{line1}{line2}{line3}{line4}'
        if artwork == None: artwork = "https://www.iconsdb.com/icons/preview/white/last-fm-xxl.png"
                
        if time_remaining != '0':
            if album != 'None':
                print(1)
                RPC.update(details=title, state=album, end=float(time_remaining)+start_time,
                    large_image=artwork, large_text=rpcLargeImageText,
                    small_image=rpcSmallImage, small_text=rpcSmallImageText,
                    buttons=lastfmProfileButton)
            else:
                print(2) # no album
                RPC.update(details=title, state=trackArtistAlbum, end=float(time_remaining)+start_time,
                    large_image=artwork, large_text=rpcLargeImageText,
                    small_image=rpcSmallImage, small_text=rpcSmallImageText,
                    buttons=lastfmProfileButton)
        else:
            if album != 'None':
                print(3) # no time remaining
                RPC.update(details=title, state=album,
                    large_image=artwork, large_text=rpcLargeImageText, 
                    small_image=rpcSmallImage, small_text=rpcSmallImageText,
                    buttons=lastfmProfileButton)
            else:
                print(4) # no time remaining and no album
                RPC.update(details=title, state=album,
                    large_image="artwork", large_text=rpcLargeImageText, 
                    small_image=rpcSmallImage, small_text=rpcSmallImageText,
                    buttons=lastfmProfileButton,)

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

