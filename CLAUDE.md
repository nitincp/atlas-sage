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

# Lint / format
ruff check .
ruff format .

# Install deps
pip install -r requirements.txt
# or if using pyproject.toml
pip install -e ".[dev]"
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

## MCP configuration

`.mcp.json` defines servers (paths use devcontainer-native `/workspaces/atlas-sage`):

| Server | Purpose |
|---|---|
| `github` | GitHub API via `GITHUB_TOKEN` env var |
| `filesystem` | Read access to `/workspaces/atlas-sage` |
