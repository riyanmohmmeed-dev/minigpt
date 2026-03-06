"""Configuration from environment."""

from __future__ import annotations

import os


class Settings:
    """App settings from env."""

    vllm_base_url: str = os.environ.get("VLLM_BASE_URL", "http://localhost:8000")
    """Base URL of vLLM server (e.g. http://localhost:8000). vLLM exposes /v1/chat/completions."""

    enable_storage: bool = os.environ.get("ENABLE_CHAT_HISTORY", "true").lower() in ("true", "1", "yes")
    """Whether to enable SQLite chat history."""

    storage_path: str = os.environ.get("CHAT_HISTORY_DB", "backend/chat_history.db")
    """Path to SQLite DB for chat history."""


settings = Settings()
