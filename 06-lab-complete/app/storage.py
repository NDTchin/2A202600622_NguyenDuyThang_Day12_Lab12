"""Small Redis abstraction with local fallback for development."""
import json
from datetime import datetime, timezone

import redis


class StateStore:
    def __init__(self, redis_url: str = ""):
        self._memory: dict[str, object] = {}
        self._redis = None
        self.mode = "memory"
        if redis_url:
            try:
                self._redis = redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
                self.mode = "redis"
            except redis.RedisError:
                self._redis = None
                self.mode = "memory"

    def ping(self) -> bool:
        if not self._redis:
            return self.mode == "memory"
        try:
            return bool(self._redis.ping())
        except redis.RedisError:
            return False

    def get_json(self, key: str, default):
        if self._redis:
            raw = self._redis.get(key)
            return json.loads(raw) if raw else default
        return self._memory.get(key, default)

    def set_json(self, key: str, value, ttl_seconds: int | None = None) -> None:
        if self._redis:
            payload = json.dumps(value)
            if ttl_seconds:
                self._redis.setex(key, ttl_seconds, payload)
            else:
                self._redis.set(key, payload)
            return
        self._memory[key] = value

    def load_history(self, user_id: str) -> list[dict]:
        return self.get_json(f"history:{user_id}", [])

    def append_history(self, user_id: str, role: str, content: str) -> list[dict]:
        history = self.load_history(user_id)
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        history = history[-20:]
        self.set_json(f"history:{user_id}", history, ttl_seconds=24 * 3600)
        return history
