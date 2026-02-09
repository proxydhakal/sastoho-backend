"""
Application settings with environment-aware config.
- ENVIRONMENT=development -> PostgreSQL, DEBUG default True, relaxed CORS
- ENVIRONMENT=production -> MySQL, DEBUG default False, strict CORS/cookies
"""
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    # ---------- Environment ----------
    ENVIRONMENT: str = "development"  # "development" | "production"
    DEBUG: bool = True  # Set to False in production (.env: DEBUG=false)

    PROJECT_NAME: str = "E-Commerce API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---------- Cookie (production: secure, HTTPS) ----------
    COOKIE_ACCESS_TOKEN_NAME: str = "access_token"
    COOKIE_REFRESH_TOKEN_NAME: str = "refresh_token"
    COOKIE_SECURE: bool = False  # Set True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"
    COOKIE_HTTPONLY: bool = True
    COOKIE_PATH: str = "/"

    # ---------- PostgreSQL (development) ----------
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: Optional[str] = None

    # ---------- MySQL (production) ----------
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_SERVER: Optional[str] = None
    MYSQL_PORT: int = 3306
    MYSQL_DB: Optional[str] = None

    REDIS_URL: str = "redis://localhost:6379/0"

    # ---------- Email ----------
    EMAIL_HOST: str = "localhost"
    EMAIL_PORT: int = 587
    EMAIL_HOST_USER: str = ""
    EMAIL_HOST_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@example.com"

    FRONTEND_URL: str = "http://localhost:5173"
    API_URL: str = "http://localhost:8000"

    # ---------- Stripe ----------
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ---------- Uploads & static ----------
    UPLOAD_DIR: str = "uploads"

    # ---------- CORS (comma-separated origins; production: set to your frontend URL(s)) ----------
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8090,http://127.0.0.1:5173,http://localhost:3000,https://sastoho.store,https://www.sastoho.store"

    # ---------- Logging ----------
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def DATABASE_URL(self) -> str:
        if self.is_production:
            if not all([self.MYSQL_USER, self.MYSQL_PASSWORD, self.MYSQL_SERVER, self.MYSQL_DB]):
                raise ValueError(
                    "When ENVIRONMENT=production set MYSQL_USER, MYSQL_PASSWORD, MYSQL_SERVER, MYSQL_DB in .env"
                )
            return URL.create(
                "mysql+aiomysql",
                username=self.MYSQL_USER,
                password=self.MYSQL_PASSWORD,
                host=self.MYSQL_SERVER,
                port=self.MYSQL_PORT,
                database=self.MYSQL_DB,
            ).render_as_string(hide_password=False)
        # Development: PostgreSQL
        if not all([self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_SERVER, self.POSTGRES_DB]):
            raise ValueError(
                "When ENVIRONMENT=development set POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_DB in .env"
            )
        return URL.create(
            "postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
