import redis.asyncio as redis
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class BlacklistService:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self._use_redis = False  # Will be set to True only after a successful ping
        self._internal_blacklist = set()

    async def initialize(self):
        """Call this during app startup to verify Redis connectivity."""
        try:
            await self.redis.ping()
            self._use_redis = True
            logger.info("Redis blacklist service: connected.")
        except Exception as e:
            self._use_redis = False
            logger.warning(f"Redis unavailable, using in-memory blacklist fallback: {e}")

    async def add(self, token_jti: str, expires_in_seconds: int):
        if self._use_redis:
            try:
                await self.redis.setex(token_jti, expires_in_seconds, "blacklisted")
                return
            except Exception as e:
                logger.error(f"Redis add error: {e}")
        self._internal_blacklist.add(token_jti)

    async def is_blacklisted(self, token_jti: str) -> bool:
        if self._use_redis:
            try:
                return await self.redis.exists(token_jti) > 0
            except Exception as e:
                logger.error(f"Redis check error, denying token to be safe: {e}")
                return True  # Fail-safe: deny if Redis is down
        return token_jti in self._internal_blacklist


blacklist_service = BlacklistService()
