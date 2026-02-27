from loguru import logger
import constants.project as project

logger = logger.bind(name='utils')

def messenger(key, *args):
    """
    Retrieves a translation and formats it with provided arguments.
    Supports both variadic arguments and a single list/tuple collection.
    """
    try:
        if not args:
            return project.TRANSLATIONS[key]
        
        # Unpack if passed as a single collection
        actual_args = args[0] if len(args) == 1 and isinstance(args[0], (list, tuple)) else args
        return project.TRANSLATIONS[key].format(*(str(arg) for arg in actual_args))
    except (KeyError, IndexError, ValueError, TypeError) as e:
        logger.error(f'Translation error for key "{key}": {e}')
        return f"[{key}]"
    except Exception as e:
        logger.error(f'Unexpected error in messenger: {e}')
        return f"[{key}]"


def get_removal(inside_obj, find_obj=' ', return_type=None):
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
        inside_obj = inside_obj.replace(find_obj, '')

    # Convert inside_obj to the specified type if needed
    if not isinstance(inside_obj, return_type):
        if return_type is int:
            inside_obj = int(inside_obj)
        elif return_type is float:
            inside_obj = float(inside_obj)

    # print(f'{inside_obj}: {type(inside_obj)}')
    return inside_obj