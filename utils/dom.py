"""HTML parsing and DOM manipulation utilities."""

import requests
from bs4 import BeautifulSoup


def get_dom(response: requests.Response) -> BeautifulSoup:
    """
    Parses the response content into a BeautifulSoup object.

    Args:
        response (requests.Response): The HTTP response object.

    Returns:
        BeautifulSoup: The parsed HTML content.
    """
    return BeautifulSoup(response.content, "html.parser")
