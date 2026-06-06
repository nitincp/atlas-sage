# ATLAS-SAGE: BACKLOG

**Status:** ACTIVE  
**Version:** 0.4  
**Methodology:** Walking skeleton first. One language. One file. One node stored correctly.  
**Thesis reference:** `THESIS-SSR.md` — every sprint validates or evolves a claim in the thesis  
**Project purpose:** ATLAS-SAGE is the live proof of SSR. Sprints are evidence, not just features.

---

## Thesis Validation Map

| Sprint | Thesis claim being validated |
|---|---|
| Sprint 0 | SSR operational loop works end-to-end |
| Sprint 1 | Structured Speculation anchored to graph produces useful output |
| Sprint 2 | Skill system self-extends without code change |
| Sprint 3 | Community summaries answer cross-domain queries |
| Sprint 4 | **Domain SSR** — human corrections accumulate as graph knowledge |
| Sprint 5 | Loop 2 operational — Gap Reports drive skill evolution |
| Sprint 6 | SSR works across language boundaries |

Sprint 4 is the most important validation. Operational SSR is proven (THESIS-SSR.md section 4). Domain SSR — real SME, real corrections, real tacit knowledge extracted — is the remaining thesis claim.

---

## Principles

- Every sprint must produce a working, observable result
- No sprint builds infrastructure without a demonstrable output
- The walking skeleton must be end-to-end before any optimisation
- LLM orchestration owns decisions — sprints wire tools, not logic
- Every sprint either validates a thesis claim or generates evidence that refines it

---

## Sprint 0 — Walking Skeleton (Single File, Single Language)

**Goal:** One C# file ingested end-to-end. One node in the store. One SME query answered.

| ID | Task | Status |
|---|---|---|
| AS-01 | Initialise LanceDB store with node and edge schema | ✅ Done |
| AS-02 | Initialise Skill registry store (searchable by keyword) | ✅ Done |
| AS-03 | Wire search_skills and create_skill tools to orchestrator | ✅ Done |
| AS-04 | Single .cs file → orchestrator searches for C# parsing skill → creates if missing | ✅ Done |
| AS-05 | Skill-loaded tool: AST extraction → boilerplate strip → cleaned raw code | ✅ Done |
| AS-06 | Tier-2 call: cleaned code → domain summary generated | ✅ Done |
| AS-07 | Cloud embed summary (gemini-embedding-001, 3072-dim) → node written to LanceDB | ✅ Done |
| AS-08 | Manual SME query → vector search → single node retrieved → LLM answer | ✅ Done |
| AS-09 | Verify end-to-end: question in, answer out, node traceable to skill used | ✅ Done |

**Exit criteria:** SME asks a question about the ingested file. System returns a plausible, traceable answer via a skill it found or created. No MSBuildWorkspace hardcoded — tool choice is the skill's concern.

**Status:** ✅ COMPLETE. Validated end-to-end with SCSS (`test_harness/specs/sprint0_scss.py`). PostCSS skill created on-the-fly by LLM; AST nodes with typed edges stored; query returned grounded structured answer. C# ingestion deferred to Sprint 1 (requires multi-file context anyway). Test rewritten to generic `SprintSpec` pattern during Sprint 1 infrastructure work.

---

## Sprint 1 — Graph Edges (Single Language)

**Goal:** Multiple files. Edges between nodes. Graph traversal at query time.

**Language:** Python (built-in `ast` — no extra runtime; rich OOP: IMPORTS, INHERITS, INJECTS, CALLS)  
**Why not C#:** Requires Roslyn/.NET — heavier toolchain; Python env already present and produces equivalent edge variety.  
**Why not SCSS:** Style files lack class/method call structure; edges are shallow (IMPORTS only). Python gives all four edge types.  
**Test target:** Embedded 4-file order-processing mini-app (`models`, `repository`, `service`, `controller`) — stable, controlled, exercises all edge types.

| ID | Task | Status |
|---|---|---|
| AS-10 | Multi-file ingestion — orchestrator processes all .py files via loaded skill | ✅ Done |
| AS-11 | Edge extraction: IMPLEMENTS, INJECTS, CALLS, RETURNS (LLM chose these over IMPORTS) | ✅ Done |
| AS-12 | Edge storage with confidence metadata — all 22 edges stored as "deterministic" | ✅ Done |
| AS-13 | graph_traverse tool wired at query time | ✅ Done |
| AS-14 | Query depth control: orchestrator chose direction=inbound/outbound and depth correctly | ✅ Done |
| AS-15 | Blast radius query identified 3 impacted classes across 2 hops | ✅ Done |

**Exit criteria:** SME asks a cross-file architectural question. System traverses graph and assembles multi-node context. Answer references multiple files correctly. Blast radius query identifies all dependent classes via inbound traversal.

**Status:** ✅ COMPLETE. Validated with Python (`test_harness/specs/sprint1.py`).  
Python AST skill created on-the-fly by LLM; nodes across 4 files; typed edges stored (IMPLEMENTS, INJECTS, CALLS, IMPORTS, USES).  
Blast radius query correctly traced IOrderRepository → OrderService → OrderController via inbound depth=3.  
Dependency query correctly traced OrderService outbound to IOrderRepository + model classes.  
Edge type note: LLM uses structural edge types (IMPLEMENTS, INJECTS, CALLS) — not import-statement reasoning.  
Cost/token tracking live: ~$0.36 per Python sprint run, ~$0.15 per SCSS run (claude-haiku-4-5-20251001).  

**Infrastructure completed alongside Sprint 1** (cross-cutting, not in original sprint scope):

| Item | Description | Status |
|---|---|---|
| Generic test runner | `SprintSpec` + `run_sprint()` pattern — new sprint = new data declaration only | ✅ Done |
| Prompt versioning | SHA-256 hash of all 4 system prompts; auto-creates `test_harness/prompts/v<N>/` on change | ✅ Done |
| Suite versioning | SHA-256 hash of input files; `test_harness/test_suites/<name>_v<N>/` — same input reused across prompt versions | ✅ Done |
| Run artifact persistence | `test_harness/runs/<timestamp>/` with `meta.json`, `output/` (skill, nodes, edges, queries) | ✅ Done |
| Run log + index | `run_log.json` append-only source of truth; `index.md` rebuilt each run | ✅ Done |
| Cost/token stats | `run_agent()` returns `tuple[str, dict]` with `cost_usd`, `in_tokens`, `out_tokens`, `model`; accumulated per sprint run | ✅ Done |
| Harness query CLI | `python -m atlas_sage.testing.harness_query` — filter/aggregate `run_log.json` without file traversal | ✅ Done |
| Native parser validation | Step 0 in `_CREATE_SKILL_SYSTEM` forces native parser declaration; `assert_sprint()` validates via `native_parser_keyword` | ✅ Done |
| IST timestamps | `TZ=Asia/Kolkata` in devcontainer; `datetime.now().astimezone()` throughout | ✅ Done |

---

## Sprint 2 — Skill System: Second Language + Quality Standards

**Goal:** Orchestrator handles a second language purely through skill discovery. Skill quality standards enforced. Zero code change.

| ID | Task | Status |
|---|---|---|
| AS-16 | Point orchestrator at repo containing .ts files | ✅ Done |
| AS-17 | Orchestrator calls create_skill for TypeScript (skill_model generates it) | ✅ Done |
| AS-18 | Skill produced with handbook, summarisation_instructions, application_role | ✅ Done |
| AS-19 | SSR loop runs — exit criteria declared, safety limit 5 loops | ✅ Done |
| AS-20 | Skill must declare execution environment (Node.js vs project-aware) | ✅ Done |
| AS-21 | Specialist must propose native/official library before parser fallback | ✅ Done |
| AS-22 | Handbook stored alongside skill in registry | ✅ Done |
| AS-23 | Verify: second language processed without any code change — skill only | ✅ Done |

**Exit criteria:** A .ts file is ingested correctly via a skill that includes handbook, execution environment declaration, and used the TypeScript Compiler API (native) not Tree-sitter (generic fallback).

**Status:** ✅ COMPLETE. Validated with TypeScript (`test_harness/specs/sprint2.py`).
TypeScript AST Parser skill created on-the-fly by LLM using ts-morph (TypeScript Compiler API); execution_environment=node; handbook explicitly favours ts-morph over tree-sitter with reasoning.
32 nodes across 4 files; 17 edges (IMPORTS, INJECTS, CALLS, IMPLEMENTS); all deterministic confidence.
Self-healing observed: orchestrator created 3 skill versions (ts-morph API hallucinations on attempts 1–2), succeeded on attempt 3 of 5 allowed — SSR loop working as designed.
Cost: ~$0.43 per run (claude-haiku-4-5-20251001). Zero code changes — skill only.

---

## Sprint 3 — Community Summaries

**Goal:** Community detection over AST graph. Tier-2 community summaries generated.

| ID | Task | Status |
|---|---|---|
| AS-24 | Leiden/Louvain community detection over graph edges | ✅ Done |
| AS-25 | Community hierarchy mapped to: project → namespace → class | ✅ Done |
| AS-26 | Community summary generation via orchestrator LLM | ✅ Done |
| AS-27 | Community nodes stored with embeddings | ✅ Done |
| AS-28 | Cross-cutting query routing: orchestrator identifies domain-level intent → community summaries pulled | ✅ Done |

**Exit criteria:** SME asks "what does the payment domain do?" System answers from community summary, not individual chunks.

**Status:** ✅ COMPLETE. Validated with Python (`test_harness/specs/sprint3.py`).
Louvain community detection over 60 nodes / 27 edges; LLM generated domain summaries per community;
`search_communities` wired to query engine with domain-intent routing in system prompt.
Domain summary query routed to community summaries and answered at correct abstraction level.
Cost: ~$0.41 per run (claude-haiku-4-5-20251001). Gemini embedding hit 429 rate limit mid-run;
litellm retry (num_retries=3) recovered without intervention — run still passed.

---

## Sprint 4 — Correction Capture (Loop 1)

**Goal:** SME corrections are captured and update the graph.

| ID | Task |
|---|---|
| AS-29 | Correction capture UI — SME flags wrong answer inline |
| AS-30 | Correction stored against node/edge/community |
| AS-31 | Corrected nodes re-summarised on next ingestion run |
| AS-32 | Correction history visible to Tier-2 in subsequent queries |
| AS-33 | Verify: corrected edge produces different answer on re-query |

**Exit criteria:** SME corrects a wrong edge inference. Next query against same node reflects correction. System is measurably smarter.

---

## Sprint 5 — Gap Reports (Loop 2)

**Goal:** Ingestion run emits structured gap report. Custom instructions generated for next run.

| ID | Task |
|---|---|
| AS-34 | Gap report emitted at end of every ingestion run |
| AS-35 | Unparseable files logged with file type and recommended skill |
| AS-36 | Unresolved edges logged with confidence breakdown |
| AS-37 | Gap report → custom instructions generation for next run |
| AS-38 | Verify: second run on same repo is measurably more complete than first |

**Exit criteria:** Run 1 identifies SCSS files as a gap. Gap report recommends PostCSS skill. Run 2 processes SCSS files correctly via auto-created skill.

---

## Sprint 6 — Cross-Language Edges

**Goal:** TS frontend and C# backend connected via HTTP_CALLS edges.

| ID | Task |
|---|---|
| AS-39 | Static URL string matching: TS fetch literal → extracted C# route |
| AS-40 | Synthetic contract node generation from route attributes (no OpenAPI) |
| AS-41 | Cross-language edge storage with confidence tier |
| AS-42 | Inferred edge — Tier-2 reasons over candidates, stores with evidence |
| AS-43 | Full-stack query: "what happens when this button is clicked" — traverses TS → C# → DB |

**Exit criteria:** SME asks a full-stack question spanning frontend and backend. System traces path across language boundary and assembles coherent answer.

---

## Backlog (Unscheduled)

| ID | Item | Status |
|---|---|---|
| AS-44 | LiteLLM gateway — model-agnostic routing, local model support | ✅ Done |
| AS-45 | vLLM / Ollama local deployment option | ✅ Done (`ollama/` prefix via `ATLAS_OLLAMA_BASE`) |
| AS-46 | Git-push hook for incremental re-ingestion | — |
| AS-47 | Prompt cache optimisation (static prefix ordering) | — |
| AS-48 | Multi-repo support | — |
| AS-49 | gRPC / protobuf tool skill | — |
| AS-50 | OpenAPI spec ingestion when available | — |
| AS-51 | SME session history as community correction source | — |
| AS-52 | Gap report dashboard UI | — |
| AS-53 | Thesis evolution — update THESIS-SSR.md after Sprint 4 domain SSR validation | — |
| AS-56 | Provider fallback for rate limits — LiteLLM Router with `fallbacks` per model tier; `ATLAS_EMBED_MODEL_FALLBACK` for embedding 429s; currently `num_retries=3` retries same provider which works but burns quota faster | — |
| AS-54 | Telemetry / distributed trace integration — LiteLLM callbacks + Langfuse for per-call span visibility (timing, token breakdown by tool call, skill cache hit rate). Complement to run_log stats, not a replacement. Defer to Sprint 3+ when prompts are stable and production usage begins. | — |
| AS-55 | Skill validation loop — post-execute skill, compare output against spec, send delta back to skill model (max 5 loops). Currently the orchestrator inline-recovers; this formalises the loop with exit criteria. | — |

---

## Non-Negotiables

- No tool is hardcoded — all tools are loaded via skills at runtime
- LLM orchestrator owns all routing and reasoning decisions — no hand-coded logic
- Skills contain zero domain knowledge — tool instructions only
- Correction capture is first-class — not an afterthought
- Every sprint is demonstrable end-to-end before the next begins
- Every sprint references the thesis claim it validates — see Thesis Validation Map

---

## Current Confidence (updated post Sprint 1 + test harness)

| Dimension | Score | Rationale |
|---|---|---|
| Implementation | 8/10 | Multi-file graph edges proven. Cost/token tracking live. Test harness versioning operational. Scale (eShopOnWeb full repo) untested. |
| Usability | 9/10 | Blast radius and dependency queries answered correctly. Domain SSR with real SME unvalidated. |
| Thesis | 7/10 | Operational SSR fully validated across two languages. Domain SSR (Sprint 4) is the remaining thesis risk. |
| Observability | 6/10 | Aggregate cost/token/model tracked per run. Per-call span visibility (telemetry) deferred to AS-54. Node/edge counts non-deterministic across runs — expected until prompts stabilise. |

The system that knows what it does not know is more trustworthy than one that silently covers gaps. Gap Reports and loop exit criteria are evidence of self-awareness — which changes the risk profile more than the scores capture.
