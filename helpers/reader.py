import yaml
import sys

def load_yaml_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError:
        print(f"YAMLError: Error loading file {file_path}.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"FileNotFoundError: The file {file_path} was not found.")
        sys.exit(1)

def load_config(config_path="config.yaml"):
    config = load_yaml_file(config_path)
    try:
        username = config['USER']['USERNAME']
        api_key = config['API']['KEY']
        api_secret = config['API']['SECRET']
        app_lang = config['APP']['LANG']
        print("API key and secret key have been successfully loaded from the config file.")
        return username, api_key, api_secret, app_lang
    except KeyError as e:
        print(f"KeyError: Configuration file does not contain the key: {e}.")
        sys.exit(1)

def load_translations(app_lang, translations_path='translations/project.yaml'):
    translations = load_yaml_file(translations_path)
    try:
        language_translations = translations[app_lang]
        print('Translations have been successfully loaded from the file.')
        return language_translations
    except KeyError:
        print(f"KeyError: Translations file does not contain the specified language: {app_lang}.")
        sys.exit(1)