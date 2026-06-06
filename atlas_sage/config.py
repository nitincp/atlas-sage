"""Env-driven configuration.

Two env vars drive model selection:
  ATLAS_ORCHESTRATOR_MODEL  — all LLM calls: agent loop, routing, summaries (required)
  ATLAS_SKILL_MODEL         — one-time skill code generation per file type (optional, defaults to orchestrator)

Optional tuning:
  ATLAS_MAX_TOKENS          — max output tokens per LLM call (default 8192)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import litellm
from dotenv import load_dotenv

load_dotenv()

# Automatic retry with exponential backoff — handles transient rate limits across all providers.
litellm.num_retries = 3


@dataclass
class Config:
    orchestrator_model: str = field(default_factory=lambda: _require("ATLAS_ORCHESTRATOR_MODEL"))
    skill_model: str = field(
        default_factory=lambda: os.getenv("ATLAS_SKILL_MODEL") or _require("ATLAS_ORCHESTRATOR_MODEL")
    )
    max_tokens: int = field(default_factory=lambda: int(os.getenv("ATLAS_MAX_TOKENS", "8192")))
    ollama_base: str = field(default_factory=lambda: os.getenv("ATLAS_OLLAMA_BASE", "http://localhost:11434"))
    lancedb_path: str = field(default_factory=lambda: os.getenv("ATLAS_LANCEDB_PATH", ".atlas_sage/db"))
    embed_model: str = field(default_factory=lambda: os.getenv("ATLAS_EMBED_MODEL", "gemini/text-embedding-004"))
    skill_loop_limit: int = field(default_factory=lambda: int(os.getenv("ATLAS_SKILL_LOOP_LIMIT", "5")))

    def litellm_kwargs(self) -> dict:
        """Return litellm kwargs for the orchestrator model."""
        return self._kwargs_for(self.orchestrator_model)

    def skill_litellm_kwargs(self) -> dict:
        """Return litellm kwargs for skill code generation."""
        return self._kwargs_for(self.skill_model)

    def _kwargs_for(self, model: str) -> dict:
        kwargs: dict = {"model": model, "max_tokens": self.max_tokens}

        if model.startswith("ollama/"):
            kwargs["api_base"] = self.ollama_base

        if model.startswith("gemini/"):
            # Disable thinking tokens (expensive internal reasoning) and use flex routing
            # (best-effort tier — 50% cheaper on paid accounts, no-op on free tier).
            kwargs["extra_body"] = {
                "generation_config": {
                    "thinking_config": {"thinking_budget": 0},
                },
                "service_tier": "flex",
            }

        return kwargs


def _require(var: str) -> str:
    value = os.getenv(var)
    if not value:
        raise EnvironmentError(
            f"{var} is not set. "
            "Set it to a LiteLLM model string, e.g.:\n"
            "  gemini/gemini-2.5-flash\n"
            "  claude-haiku-4-5-20251001\n"
            "  ollama/llama3.1:8b\n"
            "See .env.example for full configuration reference."
        )
    return value
