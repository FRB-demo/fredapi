"""Configuration management using pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    openai_api_key: Optional[str] = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_db_path: str = "./data/chroma_db"
    sqlite_db_path: str = "./data/metadata.db"
    download_path: str = "./data/downloads"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def get_llm_base_url(self) -> Optional[str]:
        """Return the effective LLM base URL."""
        if self.llm_base_url:
            return self.llm_base_url
        if self.llm_provider == "ollama":
            return "http://localhost:11434/v1"
        return None


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    return Settings()
