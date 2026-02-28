import os

import yaml
from loguru import logger

from utils.paths import get_project_root

from .models import AppConfig, RpcDisplayConfig

logger = logger.bind(name="config")


class ConfigManager:
    def __init__(self, config_path: str | None = None, translations_dir: str | None = None):
        root = get_project_root()
        self.config_path = config_path or os.path.join(root, "config.yaml")
        self.translations_dir = translations_dir or os.path.join(root, "translations")
        self._config = AppConfig()
        self.translations: dict[str, str] = {}

    @property
    def username(self) -> str:
        return self._config.username

    @property
    def api_key(self) -> str:
        return self._config.api_key

    @property
    def api_secret(self) -> str:
        return self._config.api_secret

    @property
    def app_lang(self) -> str:
        return self._config.app_lang

    @property
    def auto_start_enabled(self) -> bool:
        return self._config.app.auto_start

    @property
    def rpc(self) -> RpcDisplayConfig:
        return self._config.rpc

    @property
    def details_template(self) -> str:
        return self._config.rpc.details_template

    @property
    def state_template(self) -> str:
        return self._config.rpc.state_template

    def load(self):
        try:
            with open(self.config_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            self._config = AppConfig.model_validate(raw)
            self.translations = self._load_translations(self.app_lang)
            logger.info(f"Configuration and translations ({self.app_lang}) loaded successfully.")
        except FileNotFoundError:
            logger.warning(f"Config file not found at {self.config_path}, using defaults.")
            self._config = AppConfig()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    def save(self, username=None, api_key=None, api_secret=None, lang=None, auto_start=None, rpc_config=None) -> bool:
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
            self.translations = self._load_translations(self.app_lang)
            logger.info("Configuration saved and reloaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False

    def get_all_config(self) -> AppConfig:
        return self._config

    def is_complete(self) -> bool:
        return self._config.is_complete()

    def _load_translations(self, lang: str) -> dict[str, str]:
        file_path = os.path.join(self.translations_dir, f"{lang}.yaml")
        try:
            with open(file_path, encoding="utf-8") as f:
                translations = yaml.safe_load(f) or {}
            logger.info(f"Translations for '{lang}' loaded successfully from {file_path}")
            return translations
        except FileNotFoundError:
            logger.error(f"Translation file not found: {file_path}")
            return {}
        except Exception as e:
            logger.error(f"Could not load translations for language: {lang} - {e}")
            return {}


config = ConfigManager()
config.load()
