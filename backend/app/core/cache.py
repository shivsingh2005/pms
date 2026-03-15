import json
from typing import Any
from app.config import get_settings

settings = get_settings()

_redis_client: Any | None = None


async def get_redis_client() -> Any | None:
    global _redis_client
    if _redis_client is None:
        try:
            from redis.asyncio import Redis

            _redis_client = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client


async def cache_get(key: str) -> Any | None:
    client = await get_redis_client()
    if not client:
        return None
    value = await client.get(key)
    if value is None:
        return None
    return json.loads(value)


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    client = await get_redis_client()
    if not client:
        return
    await client.set(key, json.dumps(value), ex=ttl or settings.CACHE_TTL_SECONDS)
