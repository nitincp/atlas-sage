"""Env-driven configuration. No defaults for model names — must be explicit."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    tier1_model: str = field(default_factory=lambda: _require("ATLAS_TIER1_MODEL"))
    tier2_model: str = field(default_factory=lambda: _require("ATLAS_TIER2_MODEL"))
    ollama_base: str = field(default_factory=lambda: os.getenv("ATLAS_OLLAMA_BASE", "http://localhost:11434"))
    lancedb_path: str = field(default_factory=lambda: os.getenv("ATLAS_LANCEDB_PATH", ".atlas_sage/db"))
    embed_model: str = field(default_factory=lambda: os.getenv("ATLAS_EMBED_MODEL", "BAAI/bge-m3"))
    skill_loop_limit: int = field(default_factory=lambda: int(os.getenv("ATLAS_SKILL_LOOP_LIMIT", "5")))

    def litellm_kwargs(self, tier: int) -> dict:
        """Return extra kwargs for litellm.completion for the given tier."""
        model = self.tier1_model if tier == 1 else self.tier2_model
        kwargs: dict = {"model": model}
        if model.startswith("ollama/"):
            kwargs["api_base"] = self.ollama_base
        return kwargs


def _require(var: str) -> str:
    value = os.getenv(var)
    if not value:
        raise EnvironmentError(
            f"{var} is not set. "
            "Set it to a LiteLLM model string, e.g.:\n"
            "  ollama/llama3.1:8b\n"
            "  claude-sonnet-4-6\n"
            "  gpt-4o\n"
            "See .env.example for full configuration reference."
        )
    return value
