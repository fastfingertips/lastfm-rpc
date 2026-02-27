import os

import yaml
from loguru import logger
from pydantic import BaseModel, Field

from utils.paths import get_project_root

logger = logger.bind(name="config")


class UserConfig(BaseModel):
    """User-specific settings."""

    username: str = Field(default="", alias="USERNAME")


class ApiConfig(BaseModel):
    """API credentials."""

    key: str = Field(default="", alias="KEY")
    secret: str = Field(default="", alias="SECRET")


class AppSettingsConfig(BaseModel):
    """Application-level settings."""

    lang: str = Field(default="en-US", alias="LANG")


class RpcDisplayConfig(BaseModel):
    """RPC display preferences."""

    show_scrobbles: bool = Field(default=True, alias="SHOW_SCROBBLES")
    show_artists: bool = Field(default=True, alias="SHOW_ARTISTS")
    show_loved: bool = Field(default=True, alias="SHOW_LOVED")
    show_small_image: bool = Field(default=True, alias="SHOW_SMALL_IMAGE")
    use_custom_profile_image: bool = Field(default=True, alias="USE_CUSTOM_PROFILE_IMAGE")
    use_default_icon: bool = Field(default=False, alias="USE_DEFAULT_ICON")
    use_lastfm_icon: bool = Field(default=False, alias="USE_LASTFM_ICON")
    show_username: bool = Field(default=True, alias="SHOW_USERNAME")
    show_artist_scrobbles_large: bool = Field(default=True, alias="SHOW_ARTIST_SCROBBLES_LARGE")
    focus_artist: bool = Field(default=True, alias="FOCUS_ARTIST")

    # Templates
    details_template: str = Field(default="{title}", alias="DETAILS_TEMPLATE")
    state_template: str = Field(default="{artist} - {album}", alias="STATE_TEMPLATE")


class AppConfig(BaseModel):
    """Root configuration model representing config.yaml structure."""

    user: UserConfig = Field(default_factory=UserConfig, alias="USER")
    api: ApiConfig = Field(default_factory=ApiConfig, alias="API")
    app: AppSettingsConfig = Field(default_factory=AppSettingsConfig, alias="APP")
    rpc: RpcDisplayConfig = Field(default_factory=RpcDisplayConfig, alias="RPC")

    model_config = {"populate_by_name": True}

    # Shortcut properties for backward compatibility
    @property
    def username(self) -> str:
        return self.user.username

    @property
    def api_key(self) -> str:
        return self.api.key

    @property
    def api_secret(self) -> str:
        return self.api.secret

    @property
    def app_lang(self) -> str:
        return self.app.lang

    def is_complete(self) -> bool:
        """Checks if the configuration has all required values and no placeholders."""
        if not all([self.username, self.api_key, self.api_secret]):
            return False
        return not ("<" in self.username or "<" in self.api_key)


class ConfigManager:
    """
    Manages application configuration, including loading, saving, and
    providing access to settings and translations.
    """

    def __init__(self, config_path: str | None = None, translations_dir: str | None = None):
        root = get_project_root()
        self.config_path = config_path or os.path.join(root, "config.yaml")
        self.translations_dir = translations_dir or os.path.join(root, "translations")
        self._config = AppConfig()
        self.translations: dict[str, str] = {}

    # Shortcut properties delegating to AppConfig
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
    def rpc(self) -> RpcDisplayConfig:
        return self._config.rpc

    def load(self):
        """Loads configuration from YAML file and initializes translations."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}

            # Pydantic handles validation and defaults automatically
            self._config = AppConfig.model_validate(raw)

            # Load translations based on language
            self.translations = self._load_translations(self.app_lang)

            logger.info(f"Configuration and translations ({self.app_lang}) loaded successfully.")
        except FileNotFoundError:
            logger.warning(f"Config file not found at {self.config_path}, using defaults.")
            self._config = AppConfig()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    def save(self, username: str = None, api_key: str = None, api_secret: str = None, lang: str = None) -> bool:
        """Saves current configuration to the YAML file."""
        if username is not None:
            self._config.user.username = username
        if api_key is not None:
            self._config.api.key = api_key
        if api_secret is not None:
            self._config.api.secret = api_secret
        if lang is not None:
            self._config.app.lang = lang

        try:
            # Use Pydantic's model_dump with by_alias=True to get the YAML-friendly structure
            config_dict = self._config.model_dump(by_alias=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

            # Reload translations in case language changed
            self.translations = self._load_translations(self.app_lang)

            logger.info("Configuration saved and reloaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False

    def get_all_config(self) -> tuple[str, str, str, str]:
        """Returns the primary configuration values as a tuple."""
        return self.username, self.api_key, self.api_secret, self.app_lang

    def is_complete(self) -> bool:
        """Delegates completeness check to the Pydantic model."""
        return self._config.is_complete()

    def _load_translations(self, lang: str) -> dict[str, str]:
        """Load translations from a YAML file based on language code."""
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


# ── Global Config Instance ───────────────────────────────
config = ConfigManager()
config.load()
