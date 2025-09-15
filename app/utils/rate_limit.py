import time
from typing import Optional
from fastapi import HTTPException, Request
from app.core.config import settings
from app.utils.logging import logger

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class RateLimiter:
    def __init__(self, redis_url: Optional[str], rpm: int) -> None:
        self.rpm = max(1, rpm)
        self.period = 60
        self.redis = None
        self.memory_store: dict[str, list[float]] = {}
        if redis_url and redis is not None:
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                self.redis.ping()
                logger.info("rate_limit_redis_enabled")
            except Exception as exc:  # pragma: no cover
                logger.warning("rate_limit_redis_failed", error=str(exc))
                self.redis = None
        else:
            logger.info("rate_limit_memory_enabled")

    def _key(self, identifier: str) -> str:
        return f"rl:{identifier}"

    def check(self, identifier: str) -> None:
        now = time.time()
        window_start = now - self.period
        if self.redis is not None:
            key = self._key(identifier)
            p = self.redis.pipeline(True)
            p.zremrangebyscore(key, 0, window_start)
            p.zcard(key)
            res = p.execute()
            current = res[1] if isinstance(res, list) else 0
            if current >= self.rpm:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            p = self.redis.pipeline(True)
            p.zadd(key, {str(now): now})
            p.expire(key, self.period)
            p.execute()
        else:
            bucket = self.memory_store.setdefault(identifier, [])
            # remove old entries
            i = 0
            for ts in bucket:
                if ts >= window_start:
                    break
                i += 1
            if i:
                del bucket[:i]
            if len(bucket) >= self.rpm:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            bucket.append(now)


rate_limiter = RateLimiter(settings.redis_url, settings.rate_limit_rpm)


async def rate_limit_dep(request: Request) -> None:
    ident = request.client.host if request.client else "anonymous"
    auth = request.headers.get("authorization")
    if auth:
        ident = auth[-32:]
    rate_limiter.check(ident)
