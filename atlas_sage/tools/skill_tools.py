"""search_skills and create_skill tool implementations.

create_skill calls the Tier-2 LLM with an IP-safe prompt (code structure only).
The LLM returns a structured skill document which is stored and returned.
"""

from __future__ import annotations

import json
import uuid

import litellm

from ..config import Config
from ..store.store import AtlasStore

_CREATE_SKILL_SYSTEM = """\
You are a specialist tool engineer. Your job is to produce a parsing skill for a given file type.

A skill describes HOW to use a tool against a file type. It contains ZERO domain knowledge —
no interpretation of what any specific codebase means. Skills are reusable across all codebases.

You must respond with a single JSON object with these fields:
{
  "name": "<descriptive skill name>",
  "tool_name": "<name of the parsing tool>",
  "execution_environment": "<python|node|project-aware>",
  "install_cmd": "<pip or npm install command>",
  "extraction_script": "<complete Python script as a string>",
  "chunk_types": ["<list of chunk types this skill produces>"],
  "edge_types": [{"type": "<CALLS|IMPORTS|etc>", "confidence": "<deterministic|probabilistic|inferred>"}],
  "limitations": ["<list of known limitations>"],
  "handbook": "<plain English: file type, application role, domain signals it carries, what it cannot express>"
}

The extraction_script must be a valid Python script that:
- Receives two variables already set in its namespace: source_code (str) and file_path (str)
- Uses the tool declared in tool_name
- Produces a list of dicts in tool contract format assigned to the variable `result`
- Each dict must have: node_id (uuid str), language, source_file (=file_path), chunk_type, raw_cleaned, edges (list)
- Import uuid and generate fresh node_ids

Tool selection priority (use the highest tier available):
1. Native/official library — highest semantic fidelity
2. Established parser — structural fidelity
3. Generic parser (Tree-sitter) — syntactic only
4. Generated script — last resort

Respond with JSON only. No markdown fences, no explanation.
"""


def search_skills(file_types: list[str], store: AtlasStore) -> list[dict]:
    """Return existing skills that cover any of the requested file types."""
    return store.search_skills(file_types)


def create_skill(
    file_types: list[str],
    sample_code: str,
    config: Config,
    store: AtlasStore,
) -> dict:
    """Call Tier-2 LLM to generate a skill for the given file types, store it, and return it."""
    user_prompt = (
        f"Create a parsing skill for the following file type(s): {file_types}\n\n"
        f"Here is a representative code sample (syntax only):\n\n{sample_code}"
    )

    kwargs = config.litellm_kwargs(tier=2)
    response = litellm.completion(
        messages=[
            {"role": "system", "content": _CREATE_SKILL_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        **kwargs,
    )

    raw = response.choices[0].message.content.strip()
    skill_data = _parse_skill_json(raw)

    skill = {
        "skill_id": str(uuid.uuid4()),
        "file_types": file_types,
        "version": 1,
        **skill_data,
    }

    store.write_skill(skill)
    return skill


def _parse_skill_json(raw: str) -> dict:
    """Parse JSON from LLM response, stripping any accidental markdown fences."""
    text = raw
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Skill LLM returned invalid JSON: {exc}\nRaw response:\n{raw}") from exc
