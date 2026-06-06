# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project

**ATLAS-SAGE** — AST-anchored LLM Analysis System + accumulated knowledge graph  
**Branch:** `main` (active development)  
**Language:** Python  
**Full design:** `docs/VISION.md`, `docs/ARCHITECTURE.md`, `docs/BACKLOG.md`  
**Foundational thesis:** `docs/THESIS-SSR.md`

## Core principles (non-negotiable)

**Orchestration-first.** The LLM owns all routing, tool selection, confidence decisions, and edge inference. No hand-coded logic substitutes for LLM judgment.

**Skill registry, not hardcoded tools.** Before ingesting any file type, the orchestrator calls `search_skills(file_types)`. If no skill exists, it calls `create_skill()`. Tools are never hardcoded — loaded at runtime via the skill registry.

**Skills contain zero domain knowledge.** A skill describes how a tool works against a file type. It never encodes what any specific codebase means. This is the IP boundary.

**SSR loop.** Structured Speculation + Reinforcement. The system generates confident, graph-anchored hypotheses. SME corrections are the primary knowledge artifact. See `docs/THESIS-SSR.md`.

**Skill environment is self-declared — DO NOT OVERRIDE.** `create_skill` prompt provides OS-level capabilities only (Python 3.x and Node.js are available; no packages are assumed pre-installed). Every skill declares its own `install_cmd`. The executor runs `install_cmd` before the first extraction. Never list specific packages as pre-installed in the skill creation prompt. This is the boundary between the host environment and the skill's own setup responsibility.

**Test harness is the only testing ground — HARD RULE, DO NOT OVERRIDE.** All sprint validation tests use `SprintSpec` + `run_sprint()` from `atlas_sage.testing.runner`. No standalone test scripts. A new sprint = one new file in `test_harness/specs/sprintN.py` containing `SPEC = SprintSpec(...)`. The runner at `tests/test_harness_runner.py` discovers it automatically. Zero test logic in spec files. Artifacts, prompt versioning, cost tracking, and pass/fail are handled by the harness.

## Commands

```bash
# Run tests
pytest                                                    # all tests
pytest tests/test_harness_runner.py -v -s                 # all sprint validations
pytest tests/test_harness_runner.py -v -s -k sprint2      # one sprint
pytest tests/test_sprint0.py -v -s                        # unit/integration tests only

# Lint / format
ruff check .
ruff format .

# Install deps
pip install -r requirements.txt
# or if using pyproject.toml
pip install -e ".[dev]"

# CLI
atlas-sage ingest <file>
atlas-sage query "<question>"

# Query run log — see test_harness/README.md for full options
python -m atlas_sage.testing.harness_query --aggregate sprint
```

## Target codebase (sample input)

`eshoponweb/` is a git submodule — the eShopOnWeb reference app used as ingestion test input.

```bash
git submodule update --init    # first time
```

## Store schema (LanceDB)

**Node** — `{ node_id, language, source_file, chunk_type, raw_cleaned, summary, community_id, embedding, created_at, updated_at }`  
**Edge** — `{ edge_id, source_node_id, target_node_id, type, confidence, evidence, created_at }`  
**Community** — `{ community_id, level, member_node_ids, summary, embedding, updated_at }`  
**Correction** — `{ correction_id, session_id, target_type, target_id, original, corrected, captured_at }`

## Tool contract (uniform output from any skill)

```json
{
  "node_id": "uuid",
  "language": "csharp|typescript|html|css|unknown",
  "source_file": "relative/path",
  "chunk_type": "class|method|component|style-rule|interface|...",
  "raw_cleaned": "boilerplate-stripped source text",
  "edges": [{ "type": "...", "target_node_id": "uuid", "confidence": "deterministic|probabilistic|inferred" }]
}
```

## Model tiering

- **Tier-1** — fast, low-latency: intent detection, file classification, tool selection, query routing
- **Tier-2** — large context (128K+): domain summary generation, cross-language edge inference, community summarisation, SME query responses

## Key environment variables

| Variable | Purpose | Example |
|---|---|---|
| `ATLAS_ORCHESTRATOR_MODEL` | Model for all agent runs | `claude-haiku-4-5-20251001` |
| `ATLAS_SKILL_MODEL` | Model used for skill creation | `claude-haiku-4-5-20251001` |
| `ATLAS_EMBED_MODEL` | Embedding model (LiteLLM format) | `gemini/gemini-embedding-001` |
| `ATLAS_LANCEDB_PATH` | LanceDB data directory | `.atlas_sage/db` |
| `ATLAS_OLLAMA_BASE` | Ollama base URL for local models | `http://localhost:11434` |
| `TZ` | Timezone for all timestamps | `Asia/Kolkata` (set in devcontainer) |

## Pipeline API

All pipeline functions return `tuple[str, dict]` where `dict` is `{model, cost_usd, in_tokens, out_tokens, iterations}`:

- `run_agent(system_prompt, user_message, tools, config, context) → (text, stats)`
- `ingest(file_path, config) → (report, stats)`
- `ingest_directory(dir_path, config, pattern) → (report, stats)`
- `query(question, config) → (answer, stats)`

## Test harness

See [`test_harness/README.md`](test_harness/README.md) for layout, spec format, extension guide, and query CLI.

## MCP configuration

`.mcp.json` defines servers (paths use devcontainer-native `/workspaces/atlas-sage`):

| Server | Purpose |
|---|---|
| `github` | GitHub API via `GITHUB_TOKEN` env var |
| `filesystem` | Read access to `/workspaces/atlas-sage` |
