"""Internationalization (i18n) and translation utilities."""

import os

import yaml
from loguru import logger

from utils.paths import get_project_root

logger = logger.bind(name="i18n")


class TranslationManager:
    def __init__(self):
        self.translations: dict[str, str] = {}
        self.current_lang: str = "en-US"
        self.translations_dir = os.path.join(get_project_root(), "translations")

    def load(self, lang: str):
        """Loads translations for the specified language."""
        self.current_lang = lang
        file_path = os.path.join(self.translations_dir, f"{lang}.yaml")
        try:
            with open(file_path, encoding="utf-8") as f:
                self.translations = yaml.safe_load(f) or {}
            logger.info(f"Translations for '{lang}' loaded.")
        except FileNotFoundError:
            logger.error(f"Translation file missing: {file_path}")
            self.translations = {}
        except Exception as e:
            logger.error(f"Failed to load translations ({lang}): {e}")
            self.translations = {}

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
