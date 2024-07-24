import yaml
import sys
import logging
from typing import Tuple, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_yaml_file(file_path: str) -> dict:
    """
    Load a YAML file and return its contents as a dictionary.
    
    :param file_path: Path to the YAML file.
    :return: Contents of the YAML file as a dictionary.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError:
        logging.error(f"Error loading YAML file: {file_path}")
        sys.exit(1)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        sys.exit(1)

def load_config(config_path: str = "config.yaml") -> Tuple[str, str, str, str]:
    """
    Load the configuration file and return the required values.
    
    :param config_path: Path to the configuration YAML file.
    :return: A tuple containing username, API key, API secret, and app language.
    """
    config = load_yaml_file(config_path)
    try:
        username = config['USER']['USERNAME']
        api_key = config['API']['KEY']
        api_secret = config['API']['SECRET']
        app_lang = config['APP']['LANG']
        logging.info("API key and secret key have been successfully loaded from the config file.")
        return username, api_key, api_secret, app_lang
    except KeyError as e:
        logging.error(f"Configuration file missing key: {e}")
        sys.exit(1)

def load_translations(app_lang: str, translations_path: str = 'translations/project.yaml') -> Dict[str, str]:
    """
    Load the translations file and return the translations for the specified language.
    
    :param app_lang: Language code for the translations.
    :param translations_path: Path to the translations YAML file.
    :return: A dictionary containing translations for the specified language.
    """
    translations = load_yaml_file(translations_path)
    try:
        language_translations = translations[app_lang]
        logging.info('Translations have been successfully loaded from the file.')
        return language_translations
    except KeyError:
        logging.error(f"Translations file missing specified language: {app_lang}")
        sys.exit(1)
