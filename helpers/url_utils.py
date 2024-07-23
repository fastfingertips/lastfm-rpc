from urllib import parse

def url_encoder(text: str) -> str:
    """
    Encodes the given text for use in a URL.
    
    Args:
        text (str): The text to be URL-encoded.
    
    Returns:
        str: The URL-encoded text.
    """
    return parse.quote(text, safe='')