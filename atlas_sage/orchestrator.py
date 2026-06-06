"""LiteLLM agentic tool-use loop.

run_agent() drives the LLM until it stops calling tools, dispatching each
tool call through the registry and appending results back to the message thread.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import litellm

from .config import Config
from .tools.registry import dispatch_tool

logger = logging.getLogger(__name__)


def run_agent(
    system_prompt: str,
    user_message: str,
    tools: list[dict],
    config: Config,
    context: dict[str, Any],
    max_iterations: int = 20,
) -> str:
    """Run the agentic tool-use loop.

    Returns the final text response from the LLM once it stops calling tools.
    context is passed through to every tool dispatch call.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    kwargs = config.litellm_kwargs()
    total_cost = 0.0
    total_in = 0
    total_out = 0
    agent_start = time.monotonic()
    logger.info("run_agent start | model=%s", kwargs["model"])

    for iteration in range(max_iterations):
        t0 = time.monotonic()
        response = litellm.completion(
            messages=messages,
            tools=tools,
            tool_choice="auto",
            **kwargs,
        )
        elapsed = time.monotonic() - t0

        usage = response.usage or {}
        in_tok = getattr(usage, "prompt_tokens", 0) or 0
        out_tok = getattr(usage, "completion_tokens", 0) or 0
        try:
            cost = litellm.completion_cost(completion_response=response)
        except Exception:
            cost = 0.0
        total_cost += cost
        total_in += in_tok
        total_out += out_tok

        logger.info(
            "llm_call [%d] | %.1fs | in=%d out=%d | $%.6f",
            iteration, elapsed, in_tok, out_tok, cost,
        )

        msg = response.choices[0].message
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": _serialise_tool_calls(msg.tool_calls),
        })

        if not msg.tool_calls:
            total_elapsed = time.monotonic() - agent_start
            logger.info(
                "run_agent done | iterations=%d | %.1fs total | in=%d out=%d | $%.6f total",
                iteration + 1, total_elapsed, total_in, total_out, total_cost,
            )
            return msg.content or ""

        for tc in msg.tool_calls:
            tool_name = tc.function.name
            tool_args = json.loads(tc.function.arguments)
            logger.info("tool_call [%d] → %s(%s)", iteration, tool_name, _summarise_args(tool_args))

            try:
                result = dispatch_tool(tool_name, tool_args, context)
                logger.info("tool_result [%d] ← %s: %s", iteration, tool_name, _summarise_result(result))
            except Exception as exc:
                logger.warning("tool_error [%d] ← %s: %s", iteration, tool_name, exc)
                result = {"error": str(exc)}

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str),
            })

    raise RuntimeError(f"Agent exceeded {max_iterations} iterations without completing.")


def _serialise_tool_calls(tool_calls) -> list[dict] | None:
    if not tool_calls:
        return None
    return [
        {
            "id": tc.id,
            "type": "function",
            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
        }
        for tc in tool_calls
    ]


def _summarise_args(args: dict) -> str:
    """Short args summary for logging — truncates large values."""
    parts = []
    for k, v in args.items():
        s = str(v)
        parts.append(f"{k}={s[:60]!r}{'…' if len(s) > 60 else ''}")
    return ", ".join(parts)


def _summarise_result(result: Any) -> str:
    s = json.dumps(result, default=str)
    return s[:120] + "…" if len(s) > 120 else s
