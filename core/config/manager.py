import os
import yaml
from loguru import logger

from utils.paths import get_project_root
from .models import AppConfig, RpcDisplayConfig

logger = logger.bind(name="config")

class ConfigManager:
    def __init__(self, config_path: str | None = None):
        root = get_project_root()
        self.config_path = config_path or os.path.join(root, "config.yaml")
        self._config = AppConfig()

    @property
    def data(self) -> AppConfig:
        """Access the full configuration model."""
        return self._config

    # Shortcut properties for most used fields
    @property
    def username(self) -> str:
        return self._config.user.username

    @property
    def api_key(self) -> str:
        return self._config.api.key

    @property
    def api_secret(self) -> str:
        return self._config.api.secret

    @property
    def app_lang(self) -> str:
        return self._config.app.lang

    @property
    def auto_start_enabled(self) -> bool:
        return self._config.app.auto_start

    @property
    def rpc(self) -> RpcDisplayConfig:
        return self._config.rpc

    def load(self):
        """Loads configuration from YAML and triggers i18n reload."""
        from utils.i18n import i18n
        try:
            with open(self.config_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            self._config = AppConfig.model_validate(raw)
            i18n.load(self.app_lang)
            logger.info("Config & translations synced.")
        except FileNotFoundError:
            logger.warning(f"Config not found at {self.config_path}, using defaults.")
            self._config = AppConfig()
            i18n.load(self.app_lang)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def save(self, username=None, api_key=None, api_secret=None, lang=None, auto_start=None, rpc_config=None) -> bool:
        """Saves current state to YAML and refreshes i18n."""
        from utils.i18n import i18n
        
        if username is not None:
            self._config.user.username = username
        if api_key is not None:
            self._config.api.key = api_key
        if api_secret is not None:
            self._config.api.secret = api_secret
        if lang is not None:
            self._config.app.lang = lang
        if auto_start is not None:
            self._config.app.auto_start = auto_start
        
        if rpc_config:
            for key, value in rpc_config.items():
                if hasattr(self._config.rpc, key):
                    setattr(self._config.rpc, key, value)
        try:
            config_dict = self._config.model_dump(by_alias=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            i18n.load(self.app_lang)
            logger.info("Config saved & reloaded.")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    def is_complete(self) -> bool:
        """Business logic to check if configuration is ready for use."""
        u, k, s = self.username, self.api_key, self.api_secret
        if not all([u, k, s]):
            return False
        # Prevent default placeholder values from being considered 'complete'
        return not ("<" in u or "<" in k)

config = ConfigManager()
