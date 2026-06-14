import os
from functools import lru_cache


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        self.env = os.getenv("ENV", "development")
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        self.database_url = database_url
        self.cors_origins = self._parse_csv(os.getenv("CORS_ORIGINS", "*"))
        self.port = int(os.getenv("PORT", "8000"))
        self.seed_endpoint_enabled = self._parse_bool(
            os.getenv("SEED_ENDPOINT_ENABLED"),
            default=self.env.lower() != "production",
        )

    @staticmethod
    def _parse_csv(value: str) -> list[str]:
        if value.strip() == "*":
            return ["*"]

        return [item.strip() for item in value.split(",") if item.strip()]

    @staticmethod
    def _parse_bool(value: str | None, default: bool) -> bool:
        if value is None:
            return default

        return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
