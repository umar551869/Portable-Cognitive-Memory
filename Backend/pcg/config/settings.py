from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./pcg.db"
    
    # LLM Providers
    llm_provider: Literal["openai", "gemini", "local"] = "local"
    fallback_llm_provider: str = "local"
    llm_max_retries: int = 3
    
    # Models
    embedding_model: str = "nomic-embed-text"
    embedding_version: str = "v1"
    
    openai_chat_model: str = "gpt-4-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_api_key: SecretStr | str = ""
    
    gemini_chat_model: str = "gemini-1.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_api_key: SecretStr | str = ""
    
    local_llm_url: str = "http://localhost:11434/v1"
    local_llm_model: str = "gemma3:4b"
    local_llm_fallback_model: str = ""
    local_embedding_model: str = "nomic-embed-text"
    
    # JWT / Auth
    jwt_secret: SecretStr | str = "local-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    
    # Graph / Processing
    embedding_dimension: int = 1536
    chunk_size: int = 2200
    chunk_overlap: int = 250
    deduplication_threshold: float = 0.90
    retrieval_top_k: int = 8
    graph_hops: int = 2
    
    log_level: str = "INFO"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def secret_value(self, value: SecretStr | str) -> str:
        if isinstance(value, SecretStr):
            return value.get_secret_value()
        return value


settings = Settings()
