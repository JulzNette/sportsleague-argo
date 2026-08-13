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

    # Browser origins allowed to call the API (JSON array in env), e.g.
    # CORS_ORIGINS=["https://sportsleague-frontend.vercel.app"]
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8020"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
