import os

import yaml
from loguru import logger
from pydantic import BaseModel, Field

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


class AppConfig(BaseModel):
    """Root configuration model representing config.yaml structure."""

    user: UserConfig = Field(default_factory=UserConfig, alias="USER")
    api: ApiConfig = Field(default_factory=ApiConfig, alias="API")
    app: AppSettingsConfig = Field(default_factory=AppSettingsConfig, alias="APP")

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

    def __init__(self, config_path: str = "config.yaml", translations_dir: str = "translations"):
        self.config_path = config_path
        self.translations_dir = translations_dir
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

    def save(self, username: str, api_key: str, api_secret: str, lang: str) -> bool:
        """Saves new configuration values to the YAML file."""
        self._config = AppConfig(
            USER=UserConfig(USERNAME=username),
            API=ApiConfig(KEY=api_key, SECRET=api_secret),
            APP=AppSettingsConfig(LANG=lang),
        )

        # Convert to YAML-friendly dict using aliases
        config_dict = {
            "USER": {"USERNAME": self.username},
            "API": {"KEY": self.api_key, "SECRET": self.api_secret},
            "APP": {"LANG": self.app_lang},
        }

        try:
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
