from urllib import parse
import webbrowser
from loguru import logger

def url_encoder(text: str) -> str:
    """
    Encodes the given text for use in a URL.
    
    Args:
        text (str): The text to be URL-encoded.
    
    Returns:
        str: The URL-encoded text.
    """
    return parse.quote(text, safe='')

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