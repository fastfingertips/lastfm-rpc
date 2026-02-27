from loguru import logger
import os
import yaml
from typing import Dict, Any, Tuple
from utils.reader import load_yaml_file, load_translations

logger = logger.bind(name='config')

from dataclasses import dataclass, asdict

@dataclass
class AppConfig:
    """Dataclass to hold application configuration with type safety."""
    username: str = ""
    api_key: str = ""
    api_secret: str = ""
    app_lang: str = "en-US"

class ConfigManager:
    """
    Manages application configuration, including loading, saving, and 
    providing access to settings and translations.
    """
    
    def __init__(self, config_path: str = "config.yaml", translations_dir: str = "translations"):
        self.config_path = config_path
        self.translations_dir = translations_dir
        
        # Internal state using a dataclass
        self._data = AppConfig()
        self.translations: Dict[str, str] = {}
        
        # Initial load
        self.load()

    @property
    def username(self) -> str: return self._data.username
    @property
    def api_key(self) -> str: return self._data.api_key
    @property
    def api_secret(self) -> str: return self._data.api_secret
    @property
    def app_lang(self) -> str: return self._data.app_lang

    def load(self):
        """Loads configuration from file and initializes translations."""
        try:
            config_dict = load_yaml_file(self.config_path)
            
            # Populate dataclass
            self._data = AppConfig(
                username=config_dict.get('USER', {}).get('USERNAME', ""),
                api_key=config_dict.get('API', {}).get('KEY', ""),
                api_secret=config_dict.get('API', {}).get('SECRET', ""),
                app_lang=config_dict.get('APP', {}).get('LANG', 'en-US')
            )
            
            # Load translations based on language
            self.translations = load_translations(self.app_lang, self.translations_dir)
            
            logger.info(f"Configuration and translations ({self.app_lang}) loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            
    def save(self, username: str, api_key: str, api_secret: str, lang: str) -> bool:
        """
        Saves new configuration values to the YAML file.
        Returns True if successful, False otherwise.
        """
        # Update local dataclass first
        self._data = AppConfig(username, api_key, api_secret, lang)
        
        new_config = {
            'USER': {'USERNAME': self.username},
            'API': {'KEY': self.api_key, 'SECRET': self.api_secret},
            'APP': {'LANG': self.app_lang}
        }
        
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True)
            
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
