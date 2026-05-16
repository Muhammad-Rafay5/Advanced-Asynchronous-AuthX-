import redis.asyncio as redis
import logging
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)


class BlacklistService:
    def __init__(self):
        # IMPORTANT: The _internal_blacklist set is process-local.
        # With gunicorn --workers > 1 and no Redis, each worker has a separate
        # blacklist. A token revoked in worker A will still be accepted by worker B.
        # Always run Redis in production. Only use the in-memory fallback for
        # single-process development or testing.
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self._use_redis = False  # Will be set to True only after a successful ping
        self._internal_blacklist = set()

    async def initialize(self):
        """Call this during app startup to verify Redis connectivity."""
        if not settings.USE_REDIS:
            self._use_redis = False
            logger.info("Redis disabled by config, using in-memory blacklist.")
            return

        try:
            # Short timeout for initial check to avoid startup hang
            await asyncio.wait_for(self.redis.ping(), timeout=1.0)
            self._use_redis = True
            logger.info("Redis blacklist service: connected.")
        except Exception as e:
            self._use_redis = False
            logger.warning(f"Redis connection failed, using in-memory fallback: {e}")

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
