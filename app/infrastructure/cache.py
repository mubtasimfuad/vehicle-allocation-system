import aioredis
import json
import logging
from redis.exceptions import RedisError
from typing import Any
from datetime import datetime
import os


def get_cahce():
    REDIS_HOST = os.getenv("REDIS_HOST", "redis://localhost:6379")
    return RedisCache(REDIS_HOST)


class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.logger = logging.getLogger(__name__)

    async def get(self, key: str) -> Any:
        try:
            raw_data = await self.redis.get(key)
            if raw_data:
                try:
                    return json.loads(raw_data)
                except (json.JSONDecodeError, TypeError):
                    return raw_data
            return None
        except RedisError as e:
            self.logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, expiration: int = 3600):
        try:

            def default_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(
                    f"Object of type {obj.__class__.__name__} is not JSON serializable"
                )

            if isinstance(value, (dict, list)):
                json_value = json.dumps(value, default=default_serializer)
                await self.redis.set(key, json_value, ex=expiration)
            else:
                await self.redis.set(key, str(value), ex=expiration)
        except RedisError as e:
            self.logger.error(f"Redis set error for key {key}: {e}")

    async def delete(self, key: str):
        try:
            await self.redis.delete(key)
        except RedisError as e:
            self.logger.error(f"Redis delete error for key {key}: {e}")

    async def delete_pattern(self, pattern: str):
        """
        Delete all keys matching the given pattern.
        """
        try:
            # Use Redis 'scan' instead of 'keys' for better performance in production
            async for key in self.redis.scan_iter(match=pattern):
                await self.redis.delete(key)
            self.logger.info(f"Deleted keys matching pattern: {pattern}")
        except RedisError as e:
            self.logger.error(f"Redis delete pattern error for pattern {pattern}: {e}")

    async def acquire_lock(self, lock_key: str, timeout: int = 10) -> bool:
        try:
            is_locked = await self.redis.set(lock_key, "locked", ex=timeout, nx=True)
            return bool(is_locked)
        except RedisError as e:
            self.logger.error(f"Error acquiring lock for key {lock_key}: {e}")
            return False

    async def release_lock(self, lock_key: str):
        try:
            await self.redis.delete(lock_key)
        except RedisError as e:
            self.logger.error(f"Error releasing lock for key {lock_key}: {e}")
