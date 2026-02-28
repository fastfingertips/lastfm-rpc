from pydantic import BaseModel, Field


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
    auto_start: bool = Field(default=False, alias="AUTO_START")


class RpcDisplayConfig(BaseModel):
    """RPC display preferences."""

    show_scrobbles: bool = Field(default=True, alias="SHOW_SCROBBLES")
    show_artists: bool = Field(default=True, alias="SHOW_ARTISTS")
    show_loved: bool = Field(default=True, alias="SHOW_LOVED")
    show_small_image: bool = Field(default=True, alias="SHOW_SMALL_IMAGE")
    show_small_text: bool = Field(default=True, alias="SHOW_SMALL_TEXT")
    use_custom_profile_image: bool = Field(default=True, alias="USE_CUSTOM_PROFILE_IMAGE")
    use_default_icon: bool = Field(default=False, alias="USE_DEFAULT_ICON")
    use_lastfm_icon: bool = Field(default=False, alias="USE_LASTFM_ICON")
    show_username: bool = Field(default=True, alias="SHOW_USERNAME")
    show_large_text: bool = Field(default=True, alias="SHOW_LARGE_TEXT")
    show_artist_scrobbles_large: bool = Field(default=False, alias="SHOW_ARTIST_SCROBBLES_LARGE")
    focus_artist: bool = Field(default=False, alias="FOCUS_ARTIST")
    use_custom_large_image: bool = Field(default=False, alias="USE_CUSTOM_LARGE_IMAGE")
    use_custom_large_text: bool = Field(default=False, alias="USE_CUSTOM_LARGE_TEXT")
    use_custom_small_image: bool = Field(default=False, alias="USE_CUSTOM_SMALL_IMAGE")
    use_custom_small_text: bool = Field(default=False, alias="USE_CUSTOM_SMALL_TEXT")
    details_template: str = Field(default="{title}", alias="DETAILS_TEMPLATE")
    state_template: str = Field(default="{artist}", alias="STATE_TEMPLATE")
    large_text_template: str = Field(default="{album}", alias="LARGE_TEXT_TEMPLATE")
    small_text_template: str = Field(default="{username} | {total_scrobbles} scrobbles", alias="SMALL_TEXT_TEMPLATE")
    large_image_template: str = Field(default="{artwork_url}", alias="LARGE_IMAGE_TEMPLATE")
    small_image_template: str = Field(default="{avatar_url}", alias="SMALL_IMAGE_TEMPLATE")
    button_1: str = Field(default="lastfm_track", alias="BUTTON_1")
    button_2: str = Field(default="youtube", alias="BUTTON_2")


class AppConfig(BaseModel):
    """Root configuration model representing config.yaml structure."""

    user: UserConfig = Field(default_factory=UserConfig, alias="USER")
    api: ApiConfig = Field(default_factory=ApiConfig, alias="API")
    app: AppSettingsConfig = Field(default_factory=AppSettingsConfig, alias="APP")
    rpc: RpcDisplayConfig = Field(default_factory=RpcDisplayConfig, alias="RPC")
    model_config = {"populate_by_name": True}

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

    @property
    def auto_start_enabled(self) -> bool:
        return self.app.auto_start

    def is_complete(self) -> bool:
        if not all([self.username, self.api_key, self.api_secret]):
            return False
        return not ("<" in self.username or "<" in self.api_key)
