"""Monthly LLM budget protection."""
import time

from fastapi import HTTPException

from app.storage import StateStore


PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006


class CostGuard:
    def __init__(self, store: StateStore, monthly_budget_usd: float):
        self.store = store
        self.monthly_budget_usd = monthly_budget_usd

    def check_budget(self, user_id: str) -> None:
        usage = self.get_usage(user_id)
        if usage["cost_usd"] >= self.monthly_budget_usd:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Monthly budget exceeded",
                    "used_usd": usage["cost_usd"],
                    "budget_usd": self.monthly_budget_usd,
                    "resets_at": "first day of next UTC month",
                },
            )

    def record_usage(self, user_id: str, input_tokens: int, output_tokens: int) -> dict:
        usage = self.get_usage(user_id)
        usage["input_tokens"] += input_tokens
        usage["output_tokens"] += output_tokens
        usage["requests"] += 1
        usage["cost_usd"] = round(
            (usage["input_tokens"] / 1000) * PRICE_PER_1K_INPUT_TOKENS
            + (usage["output_tokens"] / 1000) * PRICE_PER_1K_OUTPUT_TOKENS,
            6,
        )
        self.store.set_json(self._key(user_id), usage, ttl_seconds=45 * 24 * 3600)
        return usage

    def get_usage(self, user_id: str) -> dict:
        month = time.strftime("%Y-%m")
        return self.store.get_json(
            self._key(user_id),
            {
                "user_id": user_id,
                "month": month,
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "budget_usd": self.monthly_budget_usd,
            },
        )

    def _key(self, user_id: str) -> str:
        return f"cost:{time.strftime('%Y-%m')}:{user_id}"
