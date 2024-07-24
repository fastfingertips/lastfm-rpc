from helpers.request_utils import get_response, get_dom
from helpers.string_utils import get_removal
from helpers.url_utils import url_encoder

def get_library_data(username, artist_name, track_name) -> dict:

    USER_LIBRARY_URL = f'https://www.last.fm/user/{username}/library'
    # + ?date_preset=ALL (login req)
    USER_LIBRARY_ARTIST_URL = "/".join([USER_LIBRARY_URL, "music", "+noredirect", url_encoder(artist_name)])
    USER_LIBRARY_TRACK_URL = "/".join([USER_LIBRARY_URL, "music", "+noredirect", url_encoder(artist_name), "_", url_encoder(track_name)])

    def parse_count(dom):
        data = dom.find_all("p", {"class":"metadata-display"})
        if data:
            # if there is no artist info, return 0
            data = data[0].text if len(data) != 0 else '0' 
            data = get_removal(data,',', int)
        else:
            data = 0

        return data

    data = {
         'artist_count': parse_count(get_dom(get_response(USER_LIBRARY_ARTIST_URL))),
         'track_count': parse_count(get_dom(get_response(USER_LIBRARY_TRACK_URL)))
         }

    return data