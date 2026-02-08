from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

class Settings(BaseSettings):
    PROJECT_NAME: str = "E-Commerce API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # HTTP-only cookie auth (best practice: tokens not in JS)
    COOKIE_ACCESS_TOKEN_NAME: str = "access_token"
    COOKIE_REFRESH_TOKEN_NAME: str = "refresh_token"
    COOKIE_SECURE: bool = False  # True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"  # lax for same-site + top-level nav; strict for strict
    COOKIE_HTTPONLY: bool = True
    COOKIE_PATH: str = "/"

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    REDIS_URL: str

    # Email
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_HOST_USER: str
    EMAIL_HOST_PASSWORD: str
    FROM_EMAIL: str

    # Frontend URL (for password reset, email verification, etc.)
    FRONTEND_URL: str = "http://localhost:5173"

    # Stripe
    STRIPE_API_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    # File Uploads
    UPLOAD_DIR: str = "uploads"

    # API base URL (for constructing full image URLs in emails, e.g. logo)
    API_URL: str = "http://localhost:8000"

    @property
    def DATABASE_URL(self) -> str:
        # Construct URL safely
        return URL.create(
            "postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env"
    )

settings = Settings()
