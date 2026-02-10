from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Caribou Coffee API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "changethis" # IN PROD: use env var
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # DATABASE
    POSTGRES_SERVER: str = "db" # docker service name
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "caribou"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Union[str, None] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Union[str, None], values: dict) -> AnyHttpUrl:
        if isinstance(v, str):
            return v
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"

    # EMAIL
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "your-email@gmail.com"
    SMTP_PASSWORD: str = "your-password"
    EMAILS_FROM_EMAIL: str = "noreply@caribou.com"
    EMAILS_FROM_NAME: str = "Caribou Coffee Report"
    
    class Config:
        env_file = ".env"

settings = Settings()
