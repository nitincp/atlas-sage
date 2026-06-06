"""search_skills and create_skill tool implementations.

create_skill calls the skill model with an IP-safe prompt (code structure only).
The LLM returns a structured skill document which is stored and returned.
"""

from __future__ import annotations

import json
import logging
import time
import uuid

import litellm

from ..config import Config
from ..store.store import AtlasStore

logger = logging.getLogger(__name__)

_CREATE_SKILL_SYSTEM = """\
You are a specialist tool engineer. Produce a parsing skill for a given file type.

A skill describes HOW to use a tool against a file type. It contains ZERO domain knowledge —
no interpretation of what any specific codebase means. Skills are reusable across all codebases.

Respond with a single JSON object — no markdown fences, no explanation:
{
  "name": "<descriptive skill name>",
  "tool_name": "<name of the parsing tool>",
  "execution_environment": "<python|node|python+dotnet|python+node>",
  "install_cmd": "<complete install command — runtime + packages, idempotent>",
  "extraction_script": "<complete script — see runtime rules below>",
  "chunk_types": ["<chunk types this skill produces>"],
  "edge_types": [{"type": "<CALLS|IMPORTS|etc>", "confidence": "<deterministic|probabilistic|inferred>"}],
  "limitations": ["<known limitations>"],
  "application_role": "<architectural role; which query categories weight these nodes HIGH vs LOW>",
  "summarisation_instructions": "<per-chunk-type guidance: domain signals, good vs bad summary, example>",
  "handbook": "<one paragraph: file type, runtime role, domain signals it carries, what it cannot express>"
}

## Step 1 — Choose the tool (environment first, script second)

Identify the NATIVE AST tool for the language, then choose the execution_environment:

  C# → Roslyn (Microsoft.CodeAnalysis.CSharp, requires .NET SDK)
    execution_environment: "python+dotnet"
    install_cmd: "pip install tree-sitter tree-sitter-c-sharp"
    extraction_script: Python — check shutil.which("dotnet") first.
      If found: invoke Roslyn via dotnet subprocess, parse JSON output.
      If not found: use tree-sitter-c-sharp as fallback (raise a warning, do not crash).

  SCSS / CSS → PostCSS
    execution_environment: "node"
    install_cmd: "npm install postcss postcss-scss uuid"
    extraction_script: Node.js — self-executing, writes JSON to stdout.

  TypeScript / JavaScript → ts-morph or TypeScript compiler API
    execution_environment: "node"
    install_cmd: "npm install ts-morph"
    extraction_script: Node.js — self-executing, writes JSON to stdout.

  Python → ast (stdlib, zero install)
    execution_environment: "python"
    install_cmd: ""

  HTML → lxml / BeautifulSoup
    execution_environment: "python"
    install_cmd: "pip install lxml beautifulsoup4"

  Generic fallback → tree-sitter with the language package
    execution_environment: "python"
    install_cmd: "pip install tree-sitter tree-sitter-<language>"

## Step 2 — Write the extraction_script

### Python runtime (execution_environment: python / python+dotnet / python+node)
  The executor runs the script via exec() in a Python namespace.
  Pre-set variables: source_code (str), file_path (str)
  Must assign: result = [list of node dicts]
  When invoking a CLI tool:
    • Availability check: shutil.which("dotnet") — raise RuntimeError with clear message if absent
    • Write helper scripts to tempfile; clean up in finally block
    • Capture output: subprocess.check_output([...], text=True, timeout=30)
    • Parse JSON into the tool contract format

### Node.js runtime (execution_environment: node)
  The executor writes the script to a temp .js file and runs: node script.js <file_path>
  file_path is available as: const filePath = process.argv[2]
  Must write result to stdout: process.stdout.write(JSON.stringify(result))
  Do NOT use module.exports — the script must be fully self-executing.

  Pre-installed npm packages (available via require): postcss, postcss-scss
  For UUID generation: use crypto.randomUUID() — built into Node.js, no require needed.
  Do NOT require: uuid, lodash, or any package not listed above. Use only built-ins + the pre-installed list.

### Every node dict must contain:
  node_id (fresh uuid str), language, source_file (= file_path), chunk_type, raw_cleaned, edges (list)

## Step 3 — Write summarisation_instructions

The ingestion orchestrator reads these per-chunk instructions to generate domain summaries.
For EACH chunk type your skill produces, provide:
  • What domain signals to read from the raw code (names, modifiers, base types, etc.)
  • What a GOOD summary states — domain meaning, not technical syntax
  • What to AVOID — do not restate types, do not describe CSS properties, do not paraphrase variable names
  • A concrete example: raw input → ideal summary

## Step 4 — Write application_role

Guide the query engine on how to weight nodes from this file type:
  • HIGH weight queries: what this file type is authoritative for
  • LOW weight queries: what this file type cannot answer
  • Any architectural invariants (e.g. "never contains runtime logic")
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
    """Call the skill model to generate a skill for the given file types, store it, return it."""
    user_prompt = (
        f"Create a parsing skill for the following file type(s): {file_types}\n\n"
        f"Here is a representative code sample (syntax only):\n\n{sample_code}"
    )

    kwargs = config.skill_litellm_kwargs()
    t0 = time.monotonic()
    response = litellm.completion(
        messages=[
            {"role": "system", "content": _CREATE_SKILL_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
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
    logger.info("create_skill | %.1fs | in=%d out=%d | $%.6f", elapsed, in_tok, out_tok, cost)

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
    """Parse JSON from LLM response, tolerating common model formatting mistakes."""
    text = raw.strip()

    # Strip markdown fences (```json ... ``` or ``` ... ```)
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = text.strip()

    # Fix triple-quoted strings: models like llama3.1 emit "key": """multi\nline"""
    text = _fix_triple_quotes(text)

    # Fix literal control characters inside JSON strings (newlines, tabs, etc).
    # Claude and other models sometimes emit extraction_script with real newlines
    # instead of \n escape sequences, making the JSON structurally invalid.
    text = _fix_control_chars_in_strings(text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Skill LLM returned invalid JSON: {exc}\nRaw response:\n{raw}") from exc


def _fix_triple_quotes(text: str) -> str:
    """Replace Python-style triple-quoted strings with valid JSON strings."""
    import re
    def replace_triple(m: re.Match) -> str:
        content = m.group(1)
        content = content.replace("\\", "\\\\")
        content = content.replace('"', '\\"')
        content = content.replace("\n", "\\n")
        return f'"{content}"'
    return re.sub(r'"""(.*?)"""', replace_triple, text, flags=re.DOTALL)


def _fix_control_chars_in_strings(text: str) -> str:
    """Escape unescaped control characters inside JSON string values.

    Walks the raw text character by character, tracking whether we are inside a
    JSON string. Any literal newline/carriage-return/tab found inside a string is
    replaced with its JSON escape sequence. Properly skips over already-escaped
    sequences (e.g. \\n) so they are not double-escaped.
    """
    _ESCAPES = {"\n": "\\n", "\r": "\\r", "\t": "\\t"}
    result: list[str] = []
    in_string = False
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\" and in_string:
            result.append(c)
            if i + 1 < len(text):
                result.append(text[i + 1])
                i += 2
            else:
                i += 1
            continue
        if c == '"':
            in_string = not in_string
            result.append(c)
        elif in_string and c in _ESCAPES:
            result.append(_ESCAPES[c])
        else:
            result.append(c)
        i += 1
    return "".join(result)
