"""LiteLLM agentic tool-use loop.

run_agent() drives the LLM until it stops calling tools, dispatching each
tool call through the registry and appending results back to the message thread.
"""

from __future__ import annotations

import json
from typing import Any

import litellm

from .config import Config
from .tools.registry import dispatch_tool


def run_agent(
    system_prompt: str,
    user_message: str,
    tier: int,
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

    kwargs = config.litellm_kwargs(tier=tier)

    for iteration in range(max_iterations):
        response = litellm.completion(
            messages=messages,
            tools=tools,
            tool_choice="auto",
            **kwargs,
        )

        msg = response.choices[0].message
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": _serialise_tool_calls(msg.tool_calls),
        })

        if not msg.tool_calls:
            return msg.content or ""

        for tc in msg.tool_calls:
            tool_name = tc.function.name
            tool_args = json.loads(tc.function.arguments)

            try:
                result = dispatch_tool(tool_name, tool_args, context)
            except Exception as exc:
                result = {"error": str(exc)}

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str),
            })

    raise RuntimeError(f"Agent exceeded {max_iterations} iterations without completing.")


def _serialise_tool_calls(tool_calls) -> list[dict] | None:
    """Convert litellm tool call objects to plain dicts for message history."""
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
