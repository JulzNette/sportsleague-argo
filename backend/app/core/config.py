"""
Centralized application configuration, loaded from environment variables / .env.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = (
        "postgresql+psycopg2://sportsleague_user:sportsleague_pass@localhost:5432/sportsleague_db"
    )
    JWT_SECRET_KEY: str = "change-this-to-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120
    ENVIRONMENT: str = "local"

    PROJECT_NAME: str = "Sports League Management API"
    API_V1_PREFIX: str = "/api/v1"

    # Email (SMTP). When SMTP_HOST is unset (e.g. during a class demo), the
    # email service falls back to logging the "sent" message instead of sending,
    # so the feature never errors without real credentials.
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None

    # Brevo transactional HTTP API (works over port 443, which Render's free
    # tier allows even though raw SMTP/587 is blocked). When BREVO_API_KEY is
    # set, the email service prefers this over SMTP.
    BREVO_API_KEY: str | None = None
    BREVO_FROM_EMAIL: str | None = None

    # Browser origins allowed to call the API (JSON array in env), e.g.
    # CORS_ORIGINS=["https://sportsleague-frontend.vercel.app"]
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8020"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
