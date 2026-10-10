"""Application settings loaded from environment variables / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Traffic Safety Monitor"
    database_url: str = "sqlite:///./traffic.db"
    api_key: str = "demo-key-change-me"


settings = Settings()
