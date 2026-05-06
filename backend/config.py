from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str | None
    deepseek_base_url: str
    deepseek_model: str
    agent_temperature: float
    agent_max_tokens: int

    @property
    def has_api_key(self) -> bool:
        return bool(self.deepseek_api_key and self.deepseek_api_key != "your_api_key_here")


def load_settings(model_override: str | None = None) -> Settings:
    load_dotenv()
    api_key = _clean_env_value(os.getenv("DEEPSEEK_API_KEY"))
    base_url = _clean_env_value(os.getenv("DEEPSEEK_BASE_URL")) or "https://api.deepseek.com"
    model = _clean_env_value(model_override) or _clean_env_value(os.getenv("DEEPSEEK_MODEL")) or "deepseek-v4-flash"
    return Settings(
        deepseek_api_key=api_key,
        deepseek_base_url=base_url,
        deepseek_model=model,
        agent_temperature=float(os.getenv("AGENT_TEMPERATURE", "0.3")),
        agent_max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "4096")),
    )


def _clean_env_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().strip('"').strip("'").strip()
    return cleaned or None
