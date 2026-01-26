import logging
import aiohttp
import asyncio
from typing import Literal

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages the connection status between the Bot and the Core API.
    Handles health checks and determines the operating mode (API vs STANDALONE).
    """

    def __init__(self, api_base_url: str | None, force_standalone: bool = False):
        self.api_base_url = api_base_url
        self.force_standalone = force_standalone
        self.mode: Literal["API", "STANDALONE"] = "STANDALONE"
        self._session: aiohttp.ClientSession | None = None
        self._last_check = 0
        
        # Initial state determination
        if not self.api_base_url or self.force_standalone:
            self.mode = "STANDALONE"
            logger.info(f"ConnectionManager initialized in PERMANENT STANDALONE mode (Force: {force_standalone}, URL: {api_base_url})")
        else:
            self.mode = "API" # Optimistic start
            logger.info(f"ConnectionManager initialized. Target API: {api_base_url}")

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def check_health(self) -> bool:
        """
        Pings the Core API to check if it's reachable.
        Updates self.mode accordingly.
        Returns True if API is healthy, False otherwise.
        """
        if self.force_standalone or not self.api_base_url:
            self.mode = "STANDALONE"
            return False

        try:
            session = await self.get_session()
            async with session.get(f"{self.api_base_url}/health", timeout=2.0) as resp:
                if resp.status == 200:
                    if self.mode != "API":
                        logger.info("✅ ORA Core API connection restored. Switching to API mode.")
                    self.mode = "API"
                    return True
                else:
                    logger.warning(f"⚠️ ORA Core API returned status {resp.status}. Switching to STANDALONE mode.")
                    self.mode = "STANDALONE"
                    return False
        except Exception as e:
            if self.mode != "STANDALONE":
                logger.error(f"❌ Failed to connect to ORA Core API ({e}). Switching to STANDALONE mode.")
            self.mode = "STANDALONE"
            return False

    async def close(self):
        if self._session:
            await self._session.close()

    @property
    def is_standalone(self) -> bool:
        return self.mode == "STANDALONE"
