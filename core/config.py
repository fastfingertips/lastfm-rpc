import logging
import os
import yaml
from typing import Dict, Any, Tuple
from utils.reader import load_yaml_file, load_translations

logger = logging.getLogger('config')

class ConfigManager:
    """
    Manages application configuration, including loading, saving, and 
    providing access to settings and translations.
    """
    
    def __init__(self, config_path: str = "config.yaml", translations_dir: str = "translations"):
        self.config_path = config_path
        self.translations_dir = translations_dir
        
        # Internal state
        self.username: str = ""
        self.api_key: str = ""
        self.api_secret: str = ""
        self.app_lang: str = "en-US"
        self.translations: Dict[str, str] = {}
        
        # Initial load
        self.load()

    def load(self):
        """Loads configuration from file and initializes translations."""
        try:
            config = load_yaml_file(self.config_path)
            
            # Extract values with defaults
            self.username = config.get('USER', {}).get('USERNAME', "")
            self.api_key = config.get('API', {}).get('KEY', "")
            self.api_secret = config.get('API', {}).get('SECRET', "")
            self.app_lang = config.get('APP', {}).get('LANG', 'en-US')
            
            # Load translations based on language
            self.translations = load_translations(self.app_lang, self.translations_dir)
            
            logger.info(f"Configuration and translations ({self.app_lang}) loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Fallback to defaults if needed, though load_yaml_file might sys.exit
            
    def save(self, username: str, api_key: str, api_secret: str, lang: str) -> bool:
        """
        Saves new configuration values to the YAML file.
        Returns True if successful, False otherwise.
        """
        new_config = {
            'USER': {'USERNAME': username},
            'API': {'KEY': api_key, 'SECRET': api_secret},
            'APP': {'LANG': lang}
        }
        
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True)
            
            # Update local state after saving
            self.username = username
            self.api_key = api_key
            self.api_secret = api_secret
            self.app_lang = lang
            
            # Reload translations in case language changed
            self.translations = load_translations(self.app_lang, self.translations_dir)
            
            logger.info("Configuration saved and reloaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False

    def get_all_config(self) -> Tuple[str, str, str, str]:
        """Returns the primary configuration values as a tuple."""
        return self.username, self.api_key, self.api_secret, self.app_lang

    def is_complete(self) -> bool:
        """Checks if the configuration is complete and not containing placeholders."""
        if not all([self.username, self.api_key, self.api_secret]):
            return False
        
        # Check for placeholders like <YOUR_KEY>
        if "<" in str(self.username) or "<" in str(self.api_key):
            return False
            
        return True
