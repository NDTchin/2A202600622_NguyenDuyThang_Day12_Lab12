"""Redis-backed sliding-window rate limiter."""
import time

from fastapi import HTTPException

from app.storage import StateStore


class RateLimiter:
    def __init__(self, store: StateStore, max_requests: int, window_seconds: int = 60):
        self.store = store
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def check(self, user_id: str) -> dict:
        now = time.time()
        key = f"rate:{user_id}"
        timestamps = self.store.get_json(key, [])
        timestamps = [ts for ts in timestamps if ts >= now - self.window_seconds]

        if len(timestamps) >= self.max_requests:
            retry_after = max(1, int(timestamps[0] + self.window_seconds - now) + 1)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": self.max_requests,
                    "window_seconds": self.window_seconds,
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(retry_after),
                },
            )

        timestamps.append(now)
        self.store.set_json(key, timestamps, ttl_seconds=self.window_seconds)
        return {
            "limit": self.max_requests,
            "remaining": self.max_requests - len(timestamps),
        }
