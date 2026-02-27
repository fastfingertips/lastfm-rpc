"""Internationalization (i18n) and translation utilities."""

from loguru import logger

from core.config import config

logger = logger.bind(name="i18n")


def messenger(key, *args):
    """
    Retrieves a translation and formats it with provided arguments.
    Supports both variadic arguments and a single list/tuple collection.
    """
    try:
        if not args:
            return config.translations.get(key, f"[{key}]")

        # Unpack if passed as a single collection
        actual_args = args[0] if len(args) == 1 and isinstance(args[0], (list, tuple)) else args

        translation = config.translations.get(key)
        if not translation:
            return f"[{key}]"

        return translation.format(*(str(arg) for arg in actual_args))
    except (KeyError, IndexError, ValueError, TypeError) as e:
        logger.error(f'Translation error for key "{key}": {e}')
        return f"[{key}]"
    except Exception as e:
        logger.error(f"Unexpected error in messenger: {e}")
        return f"[{key}]"
