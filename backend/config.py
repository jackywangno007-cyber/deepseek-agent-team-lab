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
    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_model=model_override or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        agent_temperature=float(os.getenv("AGENT_TEMPERATURE", "0.3")),
        agent_max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "4096")),
    )
