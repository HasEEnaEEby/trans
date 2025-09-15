import json
import time
import hashlib
from typing import Any, Optional
from app.core.config import settings
from app.utils.logging import logger

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class Cache:
    def __init__(self, url: Optional[str], default_ttl: int) -> None:
        self.ttl = max(1, default_ttl)
        self.redis = None
        self.memory_store: dict[str, tuple[float, str]] = {}
        if url and redis is not None:
            try:
                self.redis = redis.from_url(url, decode_responses=True)
                self.redis.ping()
                logger.info("cache_redis_enabled")
            except Exception as exc:  # pragma: no cover
                logger.warning("cache_redis_failed", error=str(exc))
                self.redis = None
        else:
            logger.info("cache_memory_enabled")

    @staticmethod
    def hash_key(parts: list[str]) -> str:
        h = hashlib.sha256("|".join(parts).encode()).hexdigest()
        return f"cache:{h[:32]}"

    def get_json(self, key: str) -> Optional[Any]:
        if self.redis is not None:
            val = self.redis.get(key)
            return json.loads(val) if val else None
        entry = self.memory_store.get(key)
        if not entry:
            return None
        expires_at, payload = entry
        if time.time() > expires_at:
            del self.memory_store[key]
            return None
        return json.loads(payload)

    def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        payload = json.dumps(value)
        ttl = ttl or self.ttl
        if self.redis is not None:
            self.redis.setex(key, ttl, payload)
        else:
            self.memory_store[key] = (time.time() + ttl, payload)


cache = Cache(settings.redis_url, settings.cache_ttl_seconds)
