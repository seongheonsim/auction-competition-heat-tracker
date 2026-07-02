from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    app_password_hash: str = ""
    session_secret: str = "dev-secret"
    imminent_days: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
