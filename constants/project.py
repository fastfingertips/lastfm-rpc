from helpers.reader import load_config, load_translations

USERNAME, API_KEY, API_SECRET, APP_LANG = load_config()

CLIENT_ID = '702984897496875072'
APP_NAME = "Last.fm Discord Rich Presence"
TRANSLATIONS = load_translations(APP_LANG)
DEFAULT_AVATAR_ID = "818148bf682d429dc215c1705eb27b98"
DEFAULT_AVATAR_URL = f"https://lastfm.freetls.fastly.net/i/u/avatar170s/{DEFAULT_AVATAR_ID}.png"