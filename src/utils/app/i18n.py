"""Internationalization (i18n) and translation utilities."""

from loguru import logger

from utils.core.io import load_yaml
from utils.core.paths import get_translation_path, get_translations_dir

logger = logger.bind(name="i18n")


class TranslationManager:
    def __init__(self):
        self.translations: dict[str, str] = {}
        self.current_lang: str = "en-US"
        self.translations_dir = get_translations_dir()

    def load(self, lang: str):
        """Loads translations for the specified language."""
        self.current_lang = lang
        file_path = get_translation_path(lang)
        data = load_yaml(file_path)
        if data is None:
            logger.error(f"Translation file missing or invalid: {file_path}")
            self.translations = {}
            return

        self.translations = data
        logger.info(f"Translations for '{lang}' loaded.")

    def get(self, key: str, *args):
        """Retrieves and formats a translation."""
        try:
            translation = self.translations.get(key)
            if not translation:
                return f"[{key}]"

            if not args:
                return translation

            # Unpack if passed as a single collection
            actual_args = args[0] if len(args) == 1 and isinstance(args[0], (list, tuple)) else args
            return translation.format(*(str(arg) for arg in actual_args))
        except Exception as e:
            logger.error(f'Translation error for "{key}": {e}')
            return f"[{key}]"


# Singleton instance
i18n = TranslationManager()
messenger = i18n.get
