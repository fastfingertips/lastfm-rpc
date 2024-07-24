from libs.web_requests import requests
from libs.scrapers import BeautifulSoup
from libs.monitoring import logging
import time

def get_response(url: str, retry_interval: int = 2, max_retries: int = 10) -> requests.Response:
    """
    Connects to the specified URL and retries until a successful response is received or the max retries limit is reached.
    
    Args:
        url (str): The URL to send the request to.
        retry_interval (int): The time interval (in seconds) between retries. Default is 2 seconds.
        max_retries (int): The maximum number of retries before giving up. Default is 10 retries.
    
    Returns:
        requests.Response: The response object from the request.
    
    Raises:
        requests.RequestException: If the request fails after the specified number of retries.
    """
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            retries += 1
            logging.warning(f"Request failed ({e}), retrying {retries}/{max_retries} in {retry_interval} seconds...")
            time.sleep(retry_interval)
    
    logging.error(f"Failed to retrieve URL after {max_retries} retries: {url}")
    raise requests.RequestException(f"Failed to retrieve URL after {max_retries} retries: {url}")

def get_dom(response: requests.Response) -> BeautifulSoup:
    """
    Parses the response content into a BeautifulSoup object.
    
    Args:
        response (requests.Response): The response object.
    
    Returns:
        BeautifulSoup: The parsed HTML content.
    """
    return BeautifulSoup(response.content, 'html.parser')