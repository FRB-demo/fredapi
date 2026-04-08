"""Unit tests for configuration module."""

import os

import pytest

from app.config import Settings


@pytest.mark.unit
class TestConfig:
    def test_default_values(self):
        """Test that defaults are set correctly."""
        settings = Settings(
            _env_file=None,  # Don't load .env for testing
        )
        assert settings.llm_provider == "openai"
        assert settings.llm_model == "gpt-4o-mini"
        assert settings.embedding_model == "all-MiniLM-L6-v2"
        assert settings.chroma_db_path == "./data/chroma_db"
        assert settings.sqlite_db_path == "./data/metadata.db"
        assert settings.download_path == "./data/downloads"

    def test_env_var_override(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        monkeypatch.setenv("LLM_MODEL", "llama3")
        monkeypatch.setenv("CHROMA_DB_PATH", "/custom/chroma")

        settings = Settings(_env_file=None)
        assert settings.llm_provider == "ollama"
        assert settings.llm_model == "llama3"
        assert settings.chroma_db_path == "/custom/chroma"

    def test_get_llm_base_url_explicit(self):
        """Test explicit base URL is returned."""
        settings = Settings(
            llm_base_url="http://custom:8080/v1",
            _env_file=None,
        )
        assert settings.get_llm_base_url() == "http://custom:8080/v1"

    def test_get_llm_base_url_ollama_default(self):
        """Test Ollama default base URL."""
        settings = Settings(
            llm_provider="ollama",
            _env_file=None,
        )
        assert settings.get_llm_base_url() == "http://localhost:11434/v1"

    def test_get_llm_base_url_openai_default(self):
        """Test OpenAI returns None (uses SDK default)."""
        settings = Settings(
            llm_provider="openai",
            _env_file=None,
        )
        assert settings.get_llm_base_url() is None

    def test_openai_api_key_optional(self):
        """API key should be optional (may use Ollama)."""
        settings = Settings(_env_file=None)
        assert settings.openai_api_key is None
