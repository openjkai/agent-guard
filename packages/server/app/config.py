"""Application settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://agentguard:agentguard@localhost:5432/agentguard"
    redis_url: str = "redis://localhost:6379/0"
    agentguard_api_key: str = "dev-change-me"
    artifacts_dir: str = ".agentguard/server-artifacts"
    celery_task_always_eager: bool = False
    repo_root: str = "."
    cors_origins: str = "http://localhost:3000"

    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
