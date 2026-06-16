import redis.asyncio as aioredis
import logging
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            max_connections=100,
            decode_responses=True,
            socket_keepalive=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
    return _redis_pool


class BlacklistService:
    def __init__(self):
        self._use_redis = False
        self._internal_blacklist = set()

    async def initialize(self):
        if not settings.USE_REDIS:
            self._use_redis = False
            logger.info("Redis disabled by config, using in-memory blacklist.")
            return

        try:
            r = await get_redis()
            await asyncio.wait_for(r.ping(), timeout=1.0)
            self._use_redis = True
            logger.info("Redis blacklist service: connected.")
        except Exception as e:
            self._use_redis = False
            logger.warning(f"Redis connection failed, using in-memory fallback: {e}")

    async def add(self, token_jti: str, expires_in_seconds: int):
        if self._use_redis:
            try:
                r = await get_redis()
                await r.setex(f"blacklist:{token_jti}", expires_in_seconds, "blacklisted")
                return
            except Exception as e:
                logger.error(f"Redis add error: {e}")
        self._internal_blacklist.add(token_jti)

    async def is_blacklisted(self, token_jti: str) -> bool:
        if self._use_redis:
            try:
                r = await get_redis()
                return await r.exists(f"blacklist:{token_jti}") > 0
            except Exception as e:
                logger.error(f"Redis check error, denying token to be safe: {e}")
                return True  # Fail-safe: deny if Redis is down
        return token_jti in self._internal_blacklist


blacklist_service = BlacklistService()
