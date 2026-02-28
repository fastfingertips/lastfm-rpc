import re

from loguru import logger

logger = logger.bind(name="utils")


def get_removal(inside_obj, find_obj=" ", return_type=None):
    """
    Removes occurrences of `find_obj` from `inside_obj` and converts the result to the specified type if needed.

    Args:
        inside_obj (str, int, or float): The object from which occurrences will be removed.
        find_obj (str, optional): The object to remove from `inside_obj`. Defaults to a space character.
        return_type (type, optional): The type to convert the result to. If None, the original type of `inside_obj` is used.

    Returns:
        str, int, or float: The modified `inside_obj`, with `find_obj` removed and converted to `return_type` if specified.
    """

    # -- TYPE AND STR CHECK

    if return_type is None:
        return_type = type(inside_obj)

    # Ensure inside_obj is a string for processing
    if not isinstance(inside_obj, str):
        inside_obj = str(inside_obj)

    # Ensure find_obj is a string
    if not isinstance(find_obj, str):
        find_obj = str(find_obj)

    # -- PROCESS

    # Remove occurrences of find_obj from inside_obj
    if find_obj in inside_obj:
        inside_obj = inside_obj.replace(find_obj, "")

    # Convert inside_obj to the specified type if needed
    if not isinstance(inside_obj, return_type):
        if return_type is int:
            inside_obj = int(inside_obj)
        elif return_type is float:
            inside_obj = float(inside_obj)

    # print(f'{inside_obj}: {type(inside_obj)}')
    return inside_obj


def parse_integer(text: str) -> int | None:
    """
    Extracts the first sequence of digits and commas from a string and converts it to an integer.
    Example: "1,234 scrobbles" -> 1234
    """
    if not text:
        return None
    match = re.search(r"([\d,.]+)", text)
    if match:
        try:
            # We use get_removal to handle commas and type conversion
            return int(get_removal(match.group(1), ",", int))
        except (ValueError, TypeError):
            pass
    return None


def format_placeholders(template: str, placeholders: dict) -> str:
    """
    Safely formats a template string containing {key} placeholders using the provided dictionary.
    Unmatched placeholders are left as-is.
    """
    if not template:
        return ""
    try:

        def replace(match) -> str:
            key = match.group(1)
            # If key exists in placeholders, use its value (ensure it's a string)
            if key in placeholders:
                val = placeholders[key]
                return str(val) if val is not None else ""
            # Fallback to original text if key not found
            return match.group(0)

        return re.sub(r"\{(\w+)\}", replace, template)
    except Exception as e:
        logger.error(f"Error formatting template placeholders: {e}")
        return template
