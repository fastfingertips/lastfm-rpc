from dataclasses import dataclass


@dataclass
class TrackInfo:
    """Represents a track's metadata retrieved from Last.fm."""

    title: str | None = None
    artist: str | None = None
    album: str | None = None
    artwork_url: str | None = None
    duration: int = 0  # in seconds
    is_loved: bool = False

    # Optional stats
    artist_scrobbles: int | None = None
    track_scrobbles: int | None = None


@dataclass
class UserState:
    """Represents the user's overall Last.fm account state."""

    username: str
    display_name: str | None = None
    avatar_url: str | None = None

    # Global stats
    total_scrobbles: int = 0
    total_artists: int = 0
    total_loved_tracks: int = 0
