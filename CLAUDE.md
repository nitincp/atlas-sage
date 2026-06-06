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

## Commands

```bash
# Run tests
pytest
pytest tests/test_sprint1.py -v -s   # Sprint 1 (Python, ~4min, ~$0.36)
pytest tests/test_scss.py -v -s      # Sprint 0 SCSS (~2min, ~$0.15)

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

# Query the test harness run log (no file traversal)
python -m atlas_sage.testing.harness_query
python -m atlas_sage.testing.harness_query --sprint sprint1 --passed
python -m atlas_sage.testing.harness_query --aggregate prompt_version --json
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

## Test harness layout

```
test_harness/
  index.md          ← rebuilt each run
  run_log.json      ← append-only, queryable
  prompts/v<N>/     ← auto-created on any prompt change (SHA-256 hash)
  test_suites/<name>_v<N>/  ← auto-created on input file change
  runs/<timestamp>/ ← one dir per sprint run (IST timestamp)
    meta.json       ← nodes, edges, cost_usd, in_tokens, out_tokens, model, passed
    output/         ← skill.json, nodes.json, edges.json, ingestion_report.md, queries/
```

Prompt versioning is automatic — edit any system prompt and re-run tests; a new `prompts/v<N>/` is created with a diff note. Same input reused across prompt versions (suite hash is independent).

## MCP configuration

`.mcp.json` defines servers (paths use devcontainer-native `/workspaces/atlas-sage`):

| Server | Purpose |
|---|---|
| `github` | GitHub API via `GITHUB_TOKEN` env var |
| `filesystem` | Read access to `/workspaces/atlas-sage` |
