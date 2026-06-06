# ATLAS-SAGE

**AST-anchored LLM Analysis System + accumulated knowledge graph**

ATLAS-SAGE answers architectural questions about legacy polyglot codebases that have no documentation. It ingests source files, builds a typed graph of structural relationships, and answers SME questions using that graph as ground truth — practising **Structured Speculation and Reinforcement (SSR)**.

Full design: [`docs/VISION.md`](docs/VISION.md) · [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/BACKLOG.md`](docs/BACKLOG.md) · [`docs/THESIS-SSR.md`](docs/THESIS-SSR.md)

---

## Core Ideas

**Orchestration-first.** The LLM owns all routing, tool selection, confidence decisions, and edge inference. No hand-coded logic substitutes for LLM judgment.

**Skill registry, not hardcoded tools.** Before ingesting any file type, the orchestrator calls `search_skills()`. If no skill exists, it calls `create_skill()`. Tools are discovered at runtime — never hardcoded.

**SSR loop.** The system generates confident, graph-anchored hypotheses. A confident wrong answer is more valuable than correct silence in a zero-documentation codebase — it provokes the SME to correct it. That correction is the knowledge artifact being harvested.

---

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Set required env vars (copy from .env.example if present)
export ATLAS_ORCHESTRATOR_MODEL=claude-haiku-4-5-20251001
export ATLAS_SKILL_MODEL=claude-haiku-4-5-20251001
export ATLAS_EMBED_MODEL=gemini/gemini-embedding-001
export ANTHROPIC_API_KEY=...
export GEMINI_API_KEY=...

# Ingest a file
atlas-sage ingest path/to/service.py

# Ingest a directory of Python files
# (use the CLI or the ingestion pipeline directly)

# Ask a question
atlas-sage query "What is the blast radius if IOrderRepository changes?"
```

---

## Architecture

```
Source Files (polyglot)
      │
      ▼
LLM Orchestrator  ←→  Skill Registry (search / create at runtime)
      │
      ▼
Graph + Vector Store (LanceDB)
   nodes: chunk_type, summary, embedding
   edges: CALLS, IMPLEMENTS, INJECTS, INHERITS, IMPORTS + confidence + evidence
      │
      ▼
SME Query Engine  →  vector_search + graph_traverse → structured answer
      │
      ▼
Correction Capture → graph strengthened → next SME starts further ahead
```

**Model tiering:**
- Tier-1 (fast): intent detection, file classification, tool selection, query routing
- Tier-2 (128K+): domain summary generation, cross-file edge inference, community summaries, SME responses

Both tiers use the same `ATLAS_ORCHESTRATOR_MODEL` env var; LiteLLM abstracts the provider.

---

## Store Schema (LanceDB)

| Table | Key fields |
|---|---|
| `nodes` | `node_id, language, source_file, chunk_type, raw_cleaned, summary, embedding` |
| `edges` | `edge_id, source_node_id, target_node_id, type, confidence, evidence` |
| `communities` | `community_id, level, member_node_ids, summary, embedding` |
| `corrections` | `correction_id, session_id, target_type, target_id, original, corrected` |
| `skills` | `skill_id, name, tool_name, file_types, handbook, extraction_script` |

---

## Running Tests

Tests validate the full SSR loop end-to-end: skill creation, node extraction, edge inference, graph traversal, and query quality.

```bash
# All tests
pytest

# Sprint 1 — Python multi-file ingestion + graph edges (~4 min, ~$0.36)
pytest tests/test_sprint1.py -v -s

# Sprint 0 — SCSS ingestion + query (~2 min, ~$0.15)
pytest tests/test_scss.py -v -s
```

Each test run saves artifacts to `test_harness/runs/<timestamp>/` and updates `test_harness/index.md`.

### Test Harness Query

```bash
# See all runs
python -m atlas_sage.testing.harness_query

# Filter
python -m atlas_sage.testing.harness_query --sprint sprint1 --passed
python -m atlas_sage.testing.harness_query --aggregate prompt_version

# JSON output for scripting
python -m atlas_sage.testing.harness_query --aggregate orchestrator_model --json
```

Prompt versioning is automatic: edit any system prompt and re-run tests — a new `prompts/v<N>/` is created with a diff note. Same input files are reused across prompt versions via independent hash-based suite versioning.

---

## Project Layout

```
atlas_sage/
  orchestrator.py          ← run_agent() → tuple[str, dict] (text + stats)
  config.py                ← Config, litellm_kwargs()
  ingestion/
    pipeline.py            ← ingest(), ingest_directory() → tuple[str, dict]
  query/
    pipeline.py            ← query() → tuple[str, dict]
  store/
    store.py               ← AtlasStore (LanceDB wrapper)
  tools/
    skill_tools.py         ← create_skill, search_skills (LLM-generated skills)
    definitions.py         ← INGESTION_TOOLS, QUERY_TOOLS (tool schemas)
    registry.py            ← dispatch_tool()
  testing/
    runner.py              ← SprintSpec, run_sprint(), assert_sprint()
    harness_query.py       ← CLI query over run_log.json

tests/
  test_sprint1.py          ← Sprint 1: Python multi-file, graph edges
  test_scss.py             ← Sprint 0: SCSS single-file walking skeleton

test_harness/              ← auto-created, gitignored
  index.md                 ← rebuilt each run
  run_log.json             ← append-only source of truth
  prompts/v<N>/            ← prompt snapshots, auto-versioned on change
  test_suites/<name>_v<N>/ ← input file snapshots, hash-versioned
  runs/<timestamp>/        ← one dir per run (IST timestamp)

docs/
  VISION.md                ← philosophy, scope, SSR explanation
  ARCHITECTURE.md          ← component design, store schema, test harness
  BACKLOG.md               ← sprint plan, thesis validation map
  THESIS-SSR.md            ← foundational intellectual framework

eshoponweb/                ← git submodule: reference ingestion target
```

---

## Development

```bash
# Devcontainer (recommended) — VS Code + Docker
# Opens with Python 3.12, Node.js, TZ=Asia/Kolkata pre-configured

# Lint
ruff check .
ruff format .

# eShopOnWeb submodule (ingestion test target)
git submodule update --init
```
