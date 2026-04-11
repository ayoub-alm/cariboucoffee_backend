from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Caribou Coffee API"
    API_V1_STR: str = "/api/v1"

    # JWT — MUST be set via SECRET_KEY env var in production
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # 2 hours

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # ── Database ──────────────────────────────────────────────────────────────
    POSTGRES_SERVER: str = "db"   # Docker service name; override via env
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str        # Required — set in .env
    POSTGRES_DB: str = "caribou"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Union[str, None] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Union[str, None], values: dict) -> str:
        if isinstance(v, str):
            return v
        return (
            f"postgresql+asyncpg://"
            f"{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}"
            f"@{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}"
            f"/{values.get('POSTGRES_DB')}"
        )

    # ── Email ─────────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str               # Required — set in .env
    SMTP_PASSWORD: str           # Required — set in .env
    EMAILS_FROM_EMAIL: str       # Required — set in .env
    EMAILS_FROM_NAME: str = "Caribou Coffee Report"

    # ── Frontend ──────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:4200"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"   # silently skip any env vars not declared above


settings = Settings()
