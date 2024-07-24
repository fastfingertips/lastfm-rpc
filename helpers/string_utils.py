from constants.project import TRANSLATIONS

def messenger(key, f=None):
    try:
        return TRANSLATIONS[key].format(str(f)) if f else TRANSLATIONS[key]
    except Exception as e:
        raise Exception(f'Error in messenger: {e}')


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
        if return_type == int:
            inside_obj = int(inside_obj)
        elif return_type == float:
            inside_obj = float(inside_obj)

    # print(f'{inside_obj}: {type(inside_obj)}')
    return inside_obj