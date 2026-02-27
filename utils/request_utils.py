import time

import requests
from bs4 import BeautifulSoup
from loguru import logger

from constants.project import MAX_RETRIES, RETRY_INTERVAL


def get_response(
    url: str, retry_interval: int = RETRY_INTERVAL, max_retries: int = MAX_RETRIES, timeout: int = 10
) -> requests.Response | None:
    """
    Connects to the specified URL and retries until a successful response is received or the max retries limit is reached.
    """
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            retries += 1
            if retries >= max_retries:
                logger.error(f"Failed to retrieve URL after {max_retries} retries: {url} | Error: {e}")
                break
            logger.warning(f"Request failed ({e}), retrying {retries}/{max_retries} in {retry_interval}s...")
            time.sleep(retry_interval)

    return None


def get_json(url: str, **kwargs) -> dict | None:
    """
    Helper to fetch JSON data from a URL using get_response.
    """
    response = get_response(url, **kwargs)
    if response and response.status_code == 200:
        try:
            return response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON from {url}: {e}")
    return None


def get_dom(response: requests.Response) -> BeautifulSoup:
    """
    Parses the response content into a BeautifulSoup object.

    Args:
        response (requests.Response): The response object.

    Returns:
        BeautifulSoup: The parsed HTML content.
    """
    return BeautifulSoup(response.content, "html.parser")
