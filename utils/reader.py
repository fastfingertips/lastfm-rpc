import sys
import os
from typing import Dict

import yaml
from loguru import logger

def load_yaml_file(file_path: str) -> dict:
    """
    Load a YAML file and return its contents as a dictionary.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}
    except yaml.YAMLError:
        logger.error(f"Error loading YAML file: {file_path}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

def load_translations(app_lang: str, translations_dir: str) -> Dict[str, str]:
    """
    Load the translations from a specific file based on the language code.
    """
    file_path = os.path.join(translations_dir, f"{app_lang}.yaml")
    
    try:
        translations = load_yaml_file(file_path)
        logger.info(f"Translations for '{app_lang}' loaded successfully from {file_path}")
        return translations
    except Exception:
        logger.error(f"Could not load translations for language: {app_lang}")
        sys.exit(1)
