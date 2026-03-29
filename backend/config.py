from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MarketMind AI"
    app_version: str = "1.0.0"
    postgres_url: str = "sqlite:///./marketmind.db"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    vector_store_path: str = "./storage/faiss"
    news_api_key: str | None = None
    elevenlabs_api_key: str | None = None
    use_gtts_fallback: bool = True
    frontend_api_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def vector_store_dir(self) -> Path:
        path = Path(self.vector_store_path)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()