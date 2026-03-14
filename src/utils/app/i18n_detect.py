import locale
import os

from loguru import logger

logger = logger.bind(name="i18n_detect")

SUPPORTED_LANGUAGES = ["en-US", "es-ES", "tr-TR"]


def detect_system_language() -> str:
    """Detects the current system language and maps it to a supported app language."""
    try:
        # On Windows, locale.getdefaultlocale() usually returns something like ('tr_TR', 'cp1254')
        # Although deprecated, it's still widely available and works well for this purpose.
        # Fallback to 'en-US' if anything goes wrong.
        lang_code, _ = locale.getdefaultlocale()

        if not lang_code:
            # Try environment variables as a backup
            lang_code = os.environ.get("LANG") or os.environ.get("LANGUAGE")

        if not lang_code:
            return "en-US"

        # Standardize format (e.g., tr_TR -> tr-TR, tr -> tr-TR)
        lang_code = lang_code.replace("_", "-")

        # Check for direct matches
        for supported in SUPPORTED_LANGUAGES:
            if lang_code.lower() == supported.lower():
                return supported

        # Check for partial matches (e.g., 'tr' matches 'tr-TR')
        base_lang = lang_code.split("-")[0].lower()
        for supported in SUPPORTED_LANGUAGES:
            if supported.lower().startswith(base_lang):
                logger.debug(f"Guessed language {supported} from system locale {lang_code}")
                return supported

    except Exception as e:
        logger.warning(f"Failed to detect system language: {e}")

    return "en-US"
