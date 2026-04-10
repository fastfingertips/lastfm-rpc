import asyncio
import os

from loguru import logger

from constants.project import DEFAULT_AVATAR_ID, LASTFM_LIBRARY_URL, LASTFM_USER_URL
from lastfm.models import UserState
from utils.core.strings import parse_integer
from utils.net.http import async_fetch
from utils.net.urls import url_encoder

logger = logger.bind(name="lastfm_scraper")


class LastFMScraper:
    """Manages web scraping logic for Last.fm using the Scrapling framework."""

    def __init__(self, username: str):
        self.username = username
        self.profile_url = LASTFM_USER_URL.format(username=username)
        self.library_url = LASTFM_LIBRARY_URL.format(username=username)

    async def close(self):
        """Clean up resources if necessary."""
        pass

    async def get_user_state(self) -> UserState:
        """Retrieves general user profile data (scrobbles, avatar, etc.)."""
        state = UserState(username=self.username)
        try:
            response = await async_fetch(self.profile_url)
            if not response or response.status not in range(200, 300):
                logger.error(
                    f"Failed to fetch profile for {self.username}, status: {getattr(response, 'status', 'N/A')}"
                )
                return state

            # Scrapling response allows direct CSS selection
            state.display_name = response.css("span.header-title-display-name::text").get()

            # Avatar parsing
            avatar_node = response.css("meta[property='og:image']::attr(content)").get()
            if avatar_node:
                url = avatar_node.replace("/avatar170s", "")
                ext = os.path.splitext(url)[1]
                url = url.replace(ext, ".gif")
                state.avatar_url = None if DEFAULT_AVATAR_ID in url else url

            # Parsing stats from the header metadata safely
            metadata_items = response.css("li.header-metadata-item")
            for item in metadata_items:
                title = item.css(".header-metadata-title::text").get("").strip().lower()
                value_node = item.css(".header-metadata-display")
                if not value_node:
                    continue

                # Combine all text within the display node to avoid missing nested tags
                all_text = "".join(value_node.css("*::text").getall()).strip()
                if not all_text:
                    continue

                try:
                    count = parse_integer(all_text)
                    if count is not None:
                        if "scrobble" in title:
                            state.total_scrobbles = count
                        elif "artist" in title:
                            state.total_artists = count
                        elif "loved track" in title:
                            state.total_loved_tracks = count

                        logger.debug(f"Metadata Item - Title: '{title}', Raw: '{all_text}', Parsed: {count}")
                except Exception as e:
                    logger.warning(f"Unexpected error parsing stat for title '{title}': {e}")

            logger.debug(
                f"Final parsed stats for {self.username}: Scrobbles={state.total_scrobbles}, Artists={state.total_artists}, Loved={state.total_loved_tracks}"
            )
            return state
        except Exception as e:
            logger.error(f"Error scraping profile for {self.username} with Scrapling: {e}")
        return state

    async def get_library_data(self, artist_name: str, track_name: str) -> dict:
        """Retrieves per-track and per-artist scrobble counts from the user's library."""
        artist_url = "/".join([self.library_url, "music", "+noredirect", url_encoder(artist_name)])
        track_url = "/".join(
            [self.library_url, "music", "+noredirect", url_encoder(artist_name), "_", url_encoder(track_name)]
        )

        try:
            # Parallel fetching with Scrapling using class methods
            artist_resp, track_resp = await asyncio.gather(async_fetch(artist_url), async_fetch(track_url))

            return {
                "artist_count": self._parse_count(artist_resp),
                "track_count": self._parse_count(track_resp),
            }
        except Exception as e:
            logger.error(f"Error scraping library data for {self.username}: {e}")

        return {"artist_count": 0, "track_count": 0}

    def _parse_count(self, response) -> int:
        """Helper to parse scrobble count from metadata-display class."""
        if not response or response.status != 200:
            return 0

        # Look for the FIRST metadata-display paragraph
        nodes = response.css("p.metadata-display")
        if not nodes:
            logger.debug("No metadata-display node found on page.")
            return 0

        # Get only the text for the FIRST matched node
        all_text = "".join(nodes[0].css("*::text").getall()).strip()
        count = parse_integer(all_text) or 0

        # Determine the contextual title for logging purely for debug clarity
        title_context = "track_scrobbles" if "/_/" in response.url else "artist_scrobbles"
        logger.debug(f"Metadata Item - Title: '{title_context}', Raw: '{all_text}', Parsed: {count}")
        return count
