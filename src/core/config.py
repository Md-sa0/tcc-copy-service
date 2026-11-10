from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "production", "test"] = "development"
    database_url: str = "postgresql+asyncpg://copy:copy_local@localhost:5432/copy"
    redis_url: str = "redis://localhost:6379/0"
    api_key: SecretStr = SecretStr("")
    settings_encryption_key: SecretStr = SecretStr("")
    prompt_version: str = "retail-v2"
    cache_ttl_seconds: int = Field(default=86400, ge=1, le=2592000)
    generation_timeout_seconds: int = Field(default=90, ge=5, le=240)
    cors_origins: list[str] = [
        "http://localhost:8080",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
    ]

    @model_validator(mode="after")
    def validate_environment(self):
        if self.app_env == "production":
            if len(self.api_key.get_secret_value()) < 32:
                raise ValueError("Produção exige API_KEY com pelo menos 32 caracteres")
            if "*" in self.cors_origins:
                raise ValueError("Produção exige origens CORS explícitas")
        return self

    @property
    def model_name(self) -> str:
        return "mock-deterministic-v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
