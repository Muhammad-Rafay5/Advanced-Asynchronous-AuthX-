import redis.asyncio as redis
from app.core.config import settings


class BlacklistService:
    def __init__(self):
        try:
            self.redis = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
            self._use_redis = True
        except Exception:
            self._use_redis = False
            self._internal_blacklist = set()

    async def add(self, token_jti: str, expires_in_seconds: int):
        if self._use_redis:
            try:
                await self.redis.setex(token_jti, expires_in_seconds, "blacklisted")
            except Exception:
                pass
        else:
            self._internal_blacklist.add(token_jti)

    async def is_blacklisted(self, token_jti: str) -> bool:
        if self._use_redis:
            try:
                return await self.redis.exists(token_jti) > 0
            except Exception:
                return False
        return token_jti in self._internal_blacklist


blacklist_service = BlacklistService()
