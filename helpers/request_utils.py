from bs4 import BeautifulSoup
import requests
import time

def get_response(url):  # Get the response of the request
    """
    Connects to the specified URL and retries until a successful response is received.
    
    Args:
        url (str): The URL to send the request to.
    
    Returns:
        requests.Response: The response object from the request.
    """
    while True:
        response = requests.get(url)
        response_code = response.status_code
        
        if response_code in range(200, 299):
            return response
        else:
            print(response_code, url)
        time.sleep(2)

def get_dom(response) -> BeautifulSoup:
    """
    Parses the response content into a BeautifulSoup object.
    
    Args:
        response (requests.Response): The response object.
    
    Returns:
        BeautifulSoup: The parsed HTML content.
    """
    return BeautifulSoup(response.content, 'html.parser')
