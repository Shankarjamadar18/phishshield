from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "PhishShield API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://phishshield:phishshield@localhost:5432/phishshield"
    cors_origins: str = "http://localhost:8080,http://localhost:5173"
    # Optional regex for hosted frontends, e.g. https://.*\\.lovable\\.app
    cors_origin_regex: str | None = None
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
