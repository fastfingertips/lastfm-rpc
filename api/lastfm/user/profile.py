import os

from loguru import logger

from api.lastfm.models import UserState
from constants.project import DEFAULT_AVATAR_ID, LASTFM_USER_URL
from utils.request_utils import get_dom, get_response
from utils.string_utils import get_removal


def parse_user_display_name(page_content):
    """
    Parses the user's display name from the page content.

    Args:
        page_content (BeautifulSoup): The parsed HTML content.

    Returns:
        str: The user's display name.
    """
    try:
        display_name = page_content.find("span", {"class": "header-title-display-name"})
        return display_name.text.strip() if display_name else None
    except Exception as e:
        logger.error(f"Error parsing user display name: {e}")
        return None


def parse_user_avatar_url(page_content):
    """
    Parses the user's avatar URL from the page content.

    Args:
        page_content (BeautifulSoup): The parsed HTML content.

    Returns:
        str: The user's avatar URL or None if the default avatar.
    """
    try:
        user_avatar_url = page_content.find("meta", property="og:image")["content"]
        user_avatar_url = user_avatar_url.replace("/avatar170s", "")
        avatar_suffix = os.path.splitext(user_avatar_url)[1]
        user_avatar_url = user_avatar_url.replace(avatar_suffix, ".gif")
        if DEFAULT_AVATAR_ID in user_avatar_url:
            # "No Avatar (Last.fm default avatar)"
            return None
        return user_avatar_url
    except Exception as e:
        logger.error(f"Error parsing user avatar URL: {e}")
        return None


def parse_user_header_status(page_content):
    """
    Parses the user's header status from the page content.

    Args:
        page_content (BeautifulSoup): The parsed HTML content.

    Returns:
        list: A list of integers representing the user's header status.
    """

    header_status = [0, 0, 0]
    try:
        headers = page_content.find_all("div", {"class": "header-metadata-display"})
        for i in range(min(len(headers), 3)):
            cleaned_text = headers[i].text.strip()
            header_status[i] = int(get_removal(cleaned_text, ",", int))
    except Exception as e:
        logger.error(f"Error parsing user header status: {e}")
    return header_status


def get_user_data(username) -> UserState:
    """
    Retrieves the user data from their Last.fm profile page.

    Args:
        username (str): The Last.fm username.

    Returns:
        UserState: An object containing the user's display name, avatar URL, and header status.
    """
    USER_PROFILE_URL = LASTFM_USER_URL.format(username=username)

    response = get_response(USER_PROFILE_URL)
    state = UserState(username=username)

    if response.status_code in range(200, 299):
        dom = get_dom(response)
        state.display_name = parse_user_display_name(dom)
        state.avatar_url = parse_user_avatar_url(dom)

        headers = parse_user_header_status(dom)
        if len(headers) >= 3:
            state.total_scrobbles = headers[0]
            state.total_artists = headers[1]
            state.total_loved_tracks = headers[2]

        logger.debug(f"User data retrieved successfully for {username}")
        return state
    logger.error(f"Failed to retrieve user data for {username}, status code: {response.status_code}")
    return state
