"""12-factor configuration: every runtime value comes from environment variables."""
import logging
import os
from dataclasses import dataclass, field


def _bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: _bool_env("DEBUG"))
    instance_id: str = field(default_factory=lambda: os.getenv("INSTANCE_ID", ""))

    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Production AI Agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))

    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))

    agent_api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", "dev-key-change-me"))
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "dev-jwt-secret"))
    allowed_origins: list[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
            if origin.strip()
        ]
    )

    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    )
    monthly_budget_usd: float = field(
        default_factory=lambda: float(
            os.getenv("MONTHLY_BUDGET_USD", os.getenv("DAILY_BUDGET_USD", "10.0"))
        )
    )

    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", ""))

    def validate(self):
        logger = logging.getLogger(__name__)
        if self.environment == "production":
            if self.agent_api_key == "dev-key-change-me":
                raise ValueError("AGENT_API_KEY must be set in production")
            if self.jwt_secret == "dev-jwt-secret":
                raise ValueError("JWT_SECRET must be set in production")
            if not self.redis_url:
                raise ValueError("REDIS_URL must be set in production for stateless operation")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY is not set; using mock LLM")
        return self


settings = Settings().validate()
