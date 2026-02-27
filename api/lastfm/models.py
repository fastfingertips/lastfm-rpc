from dataclasses import dataclass
from typing import Optional

@dataclass
class TrackInfo:
    """Represents a track's metadata retrieved from Last.fm."""
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    artwork_url: Optional[str] = None
    duration: int = 0  # in seconds
    is_loved: bool = False
    
    # Optional stats
    artist_scrobbles: Optional[int] = None
    track_scrobbles: Optional[int] = None

@dataclass
class UserState:
    """Represents the user's overall Last.fm account state."""
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Global stats
    total_scrobbles: int = 0
    total_artists: int = 0
    total_loved_tracks: int = 0
