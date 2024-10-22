import aioredis
import json
import logging
from redis.exceptions import RedisError
from typing import Any
from datetime import datetime


class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.logger = logging.getLogger(__name__)

    async def get(self, key: str) -> Any:
        try:
            # Retrieve the data from Redis
            raw_data = await self.redis.get(key)
            if raw_data:
                try:
                    # Try to deserialize JSON (assume it's a dictionary)
                    return json.loads(raw_data)
                except (json.JSONDecodeError, TypeError):
                    # If it's not JSON, return the raw data
                    return raw_data
            return None
        except RedisError as e:
            self.logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, expiration: int = 3600):
        try:
            # Function to handle datetime serialization
            def default_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()  # Convert datetime to ISO 8601 string
                raise TypeError(
                    f"Object of type {obj.__class__.__name__} is not JSON serializable"
                )

            if isinstance(value, (dict, list)):
                # If the value is a dict or list, serialize it to JSON with a custom serializer
                json_value = json.dumps(value, default=default_serializer)
                await self.redis.set(key, json_value, ex=expiration)
            else:
                # For other types (e.g., strings, integers), store as-is
                await self.redis.set(key, str(value), ex=expiration)
        except RedisError as e:
            self.logger.error(f"Redis set error for key {key}: {e}")

    async def delete(self, key: str):
        try:
            await self.redis.delete(key)
        except RedisError as e:
            self.logger.error(f"Redis delete error for key {key}: {e}")

    # Distributed lock: acquire a lock for a given key
    async def acquire_lock(self, lock_key: str, timeout: int = 10) -> bool:
        try:
            # Using Redis' setnx to implement a lock (returns True if successful)
            is_locked = await self.redis.set(lock_key, "locked", ex=timeout, nx=True)
            return bool(is_locked)  # Return True if lock is acquired, False otherwise
        except RedisError as e:
            self.logger.error(f"Error acquiring lock for key {lock_key}: {e}")
            return False

    # Distributed lock: release a lock for a given key
    async def release_lock(self, lock_key: str):
        try:
            await self.redis.delete(lock_key)
        except RedisError as e:
            self.logger.error(f"Error releasing lock for key {lock_key}: {e}")
