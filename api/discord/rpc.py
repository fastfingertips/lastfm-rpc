from loguru import logger
from pypresence.presence import AioPresence

from api.discord.exceptions import DiscordError
from api.discord.payload import build_rpc_payload
from api.lastfm.models import TrackInfo, UserState
from constants.project import CLIENT_ID, RPC_SYNC_OFFSET
from utils.clock import now, now_timestamp

logger = logger.bind(name="rpc")


class DiscordRPC:
    def __init__(self):
        self.RPC = None
        self._enabled = False
        self._disabled = True
        self.start_time = None
        self.last_track = None
        self.connection_time = None
        self.current_artist = None
        self.artist_scrobbles = 0

    @property
    def is_connected(self):
        return self._enabled and not self._disabled

    async def _connect(self):
        if not self._enabled:
            try:
                if self.RPC is None:
                    self.RPC = AioPresence(CLIENT_ID)

                await self.RPC.connect()
                self.connection_time = now()
                logger.info("Connected with Discord (Async)")
                self._enabled = True
                self._disabled = False
            except Exception as e:
                logger.error(f"Error connecting to Discord: {e}")
                raise DiscordError(f"Failed to connect to Discord: {e}") from e

    async def _disconnect(self):
        if not self._disabled and self.RPC:
            try:
                await self.RPC.clear()
                self.RPC.close()
            except Exception as e:
                logger.debug(f"Disconnect notice: {e}")
            self.connection_time = None
            self.last_track = None
            self.current_artist = None
            self.artist_scrobbles = None
            logger.info("Disconnected from Discord")
            self._disabled = True
            self._enabled = False

    async def enable(self):
        await self._connect()

    async def disable(self):
        await self._disconnect()

    async def clear_status(self):
        if self.is_connected and self.RPC:
            try:
                await self.RPC.clear()
                self.last_track = None
                self.current_artist = None
                self.artist_scrobbles = None
                logger.debug("Cleared Discord RPC status")
            except Exception as e:
                logger.error(f"Error clearing RPC status: {e}")
                await self._disconnect()

    async def update_status(
        self,
        track_obj,
        info: TrackInfo,
        username: str,
        user_state: UserState,
        lib_data: dict,
        rpc_config,
        force=False,
    ):
        if not info or not info.title:
            return

        if self.last_track == track_obj and self.current_artist is not None and not force:
            return

        if self.last_track != track_obj:
            self.start_time = now_timestamp() - RPC_SYNC_OFFSET

        self.last_track = track_obj
        self.current_artist = info.artist
        self.artist_scrobbles = info.artist_scrobbles

        # Build payload using the external builder
        payload = build_rpc_payload(info, username, user_state, lib_data, self.start_time, rpc_config)

        await self._send_rpc_update(payload)

    async def _send_rpc_update(self, payload):
        if self.RPC:
            try:
                # Clean up None values
                clean_payload = {k: v for k, v in payload.items() if v is not None}
                logger.debug(f"RPC Update: {clean_payload.get('details')} | {clean_payload.get('state')}")
                await self.RPC.update(**clean_payload)
            except Exception as e:
                logger.error(f"Error updating RPC: {e}")
                await self._disconnect()
                raise DiscordError(f"Failed to update RPC: {e}") from e
