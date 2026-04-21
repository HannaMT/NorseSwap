"""
LEARN: Application settings (from .env)
========================================
Same idea as dotenv in Node: load env vars into one place.
We use Pydantic BaseSettings so values are validated and typed.
"""
from dotenv import load_dotenv
load_dotenv()


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MAIL_USERNAME: str = "placeholder"
    MAIL_PASSWORD: str = "placeholder"
    MAIL_FROM: str = "info@campusloop.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "CampusLoop"
    CLOUDINARY_CLOUD_NAME: str = "placeholder"
    CLOUDINARY_API_KEY: str = "placeholder"
    CLOUDINARY_API_SECRET: str = "placeholder"
    STRIPE_SECRET_KEY: str = "placeholder"
    STRIPE_PUBLISHABLE_KEY: str = "placeholder"
    STRIPE_WEBHOOK_SECRET: str = "placeholder"
    STRIPE_PLATFORM_FEE_PERCENT: int = 5
    STRIPE_CURRENCY: str = "usd"
    STRIPE_API_VERSION: str = "2026-02-20"
    STRIPE_API_URL: str = "https://api.stripe.com/v1"
    STRIPE_API_KEY: str = "placeholder"
    STRIPE_API_SECRET: str = "placeholder"
    STRIPE_API_SECRET: str = "placeholder"
    # App
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    CLIENT_URL: str = "http://localhost:3000"
    # Database (async PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://localhost/campusloop_db"
    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
