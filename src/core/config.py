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
    gemini_api_key: SecretStr = SecretStr("")
    llm_provider: Literal["gemini", "mock"] = "mock"
    gemini_model: str = "gemini-2.5-flash"
    prompt_version: str = "retail-v1"
    cache_ttl_seconds: int = Field(default=86400, ge=1, le=2592000)
    generation_timeout_seconds: int = Field(default=90, ge=5, le=240)
    retry_attempts: int = Field(default=3, ge=1, le=5)
    retry_base_seconds: float = Field(default=1, ge=0, le=10)
    cors_origins: list[str] = ["http://localhost:8080", "http://localhost:5173"]

    @model_validator(mode="after")
    def validate_environment(self):
        if self.llm_provider == "gemini" and not self.gemini_api_key.get_secret_value():
            raise ValueError("GEMINI_API_KEY obrigatória para LLM_PROVIDER=gemini")
        if self.app_env == "production":
            if len(self.api_key.get_secret_value()) < 32:
                raise ValueError("Produção exige API_KEY com pelo menos 32 caracteres")
            if self.llm_provider != "gemini":
                raise ValueError("Produção exige LLM_PROVIDER=gemini")
            if "*" in self.cors_origins:
                raise ValueError("Produção exige origens CORS explícitas")
        return self

    @property
    def model_name(self) -> str:
        return self.gemini_model if self.llm_provider == "gemini" else "mock-deterministic-v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
