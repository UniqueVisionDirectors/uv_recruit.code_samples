from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/app"
    id_strategy: Literal["problem", "stage1", "stage2"] = "problem"
    worker_id: int = 0


@lru_cache
def get_settings() -> Settings:
    return Settings()
