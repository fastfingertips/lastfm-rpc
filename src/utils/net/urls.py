import webbrowser
from urllib import parse

from loguru import logger


def url_encoder(text: str) -> str:
    """
    Encodes the given text for use in a URL.

    Args:
        text (str): The text to be URL-encoded.

    Returns:
        str: The URL-encoded text.
    """
    if not text:
        return ""
    return parse.quote(str(text), safe="")


def open_url(url: str):
    """
    Centrally handles opening a URL in the default web browser.
    """
    if not url:
        logger.warning("Attempted to open an empty URL.")
        return

    try:
        logger.info(f"Opening URL: {url}")
        webbrowser.open(url)
    except Exception as e:
        logger.error(f"Failed to open URL {url}: {e}")


def is_valid_uri(url: str) -> bool:
    """
    Checks if a URL is a syntactically valid URI with a scheme and netloc.
    Useful for ensuring APIs (like Discord's) won't reject the URL.
    """
    try:
        result = parse.urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False
