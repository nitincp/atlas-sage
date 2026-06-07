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
| LiteLLM gateway (AS-44) | Model-agnostic routing; all `run_agent()` calls go through LiteLLM — provider-swap requires only env var change | ✅ Done |
| Local model support (AS-45) | `ollama/` prefix via `ATLAS_OLLAMA_BASE`; vLLM-compatible; skill and orchestrator models independently configurable | ✅ Done |

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

**Status:** ✅ COMPLETE. Validated with Python (`test_harness/specs/sprint4.py`).
`search_corrections` called before any graph search — correction surfaced as first line of Q2 answer: "SME Correction on Record: Unit of Work pattern…atomically."
`get_corrections(node_id)` per-node loop proved unreliable (LLM checks a subset of returned nodes; UUID match depends on selection order). Replaced with `search_corrections(query_text)` called once upfront — stable and node_id-independent.
Corrections stored with logical concept name as `target_id` (e.g. `"orderservice"`) rather than UUID — stable across ingestion runs without requiring node lookup.
Q1 baseline correctly reported no prior corrections. Domain SSR loop closes: speculative Q1 provoked correction; Q2 led with SME knowledge then grounded it in graph structure.
Cost: ~$0.52/run (claude-haiku-4-5-20251001), up from sprint3 ~$0.41 — extra `search_corrections` call per query is the delta.

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
| AS-55 | Skill creation loop exit criteria — gap report triggers skill creation; formalize the SSR loop (compare output against gap spec, send delta back to skill model, max 5 iterations). Currently the orchestrator inline-recovers (Sprint 2 evidence: 3 attempts); this makes exit criteria explicit within the Loop 2 flow. |

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

## Retrospective Improvements — Sprint 0–4

Surfaced during the Sprint 0–4 retrospective (`docs/RETRO-S0-S4.md`). Bridge items before Sprint 5 starts. **All items complete.**

| ID | Item | Priority | Status |
|---|---|---|---|
| AS-53 | Update THESIS-SSR.md with Sprint 4 domain SSR validation evidence — primary artifact of the project now reflects the correction-capture proof | High | ✅ Done |
| AS-57 | Fix test_harness gitignore — `prompts/`, `test_suites/`, `run_log.json` tracked; `index.md` untracked | High | ✅ Done (db3e885) |
| AS-58 | Merge test_runs/ into test_harness/ — 6 pre-harness run entries absorbed; true-first prompt `dfd77cd7` imported as `v000`; orphan directory retired; harness_query now sees 17 runs (was 11) | Medium | ✅ Done |
| AS-59 | Add `canonical: true` marker to run_log.json per sprint — reference passing run marked for runs 7, 8, 13, 14, 17 | Medium | ✅ Done |
| AS-60 | Characterize community detection edge-density boundary — Sprint 3 edges/nodes=0.45 → 7 communities; Sprint 4 at 0.23 produced singletons (community detection skipped in spec). Fix: `detect_communities_tool` filters singleton groups; degenerate fallback preserved; boundary documented in code | Medium | ✅ Done |

---

## Backlog (Unscheduled)

Items are grouped by the sprint that unlocks them. Nothing here is picked up unless explicitly pulled into a sprint during planning. Items with no sprint gate are deferred indefinitely.

### Unlocked by retro (not Sprint 5 scope)

| ID | Item |
|---|---|
| AS-61 | Add `--canonical` filter to `harness_query` CLI — `canonical: true` field added by AS-59; CLI has no way to query it yet; small addition, deferred until there are enough runs that filtering by canonical matters |

### Activates after Sprint 5

| ID | Item |
|---|---|
| AS-52 | Gap report dashboard UI — UX layer over the Sprint 5 structured gap report output; not useful until the gap report schema is stable |
| AS-46 | Git-push hook for incremental re-ingestion — triggers re-ingest on push; depends on Sprint 5 gap reports being stable enough to consume programmatically |

### Activates after Sprint 6

| ID | Item |
|---|---|
| AS-47 | Prompt cache optimisation (static prefix ordering) — per-sprint cost is $0.52 on the 4-file fixture; eShopOnWeb (~400+ files) will multiply input tokens significantly; static prefix caching is the primary cost lever for full-repo ingestion |
| AS-56 | Provider fallback for rate limits — `num_retries=3` handles Gemini 429s (Sprint 3 evidence); LiteLLM Router `fallbacks` per model tier is the production hardening step when retrying the same provider burns quota at scale |
| AS-54 | Telemetry / distributed trace integration — LiteLLM callbacks + Langfuse for per-call span visibility; complement to run_log aggregate stats; relevant when production usage on real repos begins |
| AS-50 | OpenAPI spec ingestion — Sprint 6 deliberately proves cross-language edges *without* OpenAPI (inference only); this is the fast path to add once the inference baseline is established |
| AS-51 | SME session history as community correction source — corrections update individual nodes; community summaries do not yet reflect accumulated SME knowledge; Loop 1→community propagation; natural thesis extension once Sprint 6 closes the cross-language loop |

### Deferred — no sprint gate

| ID | Item | Note |
|---|---|---|
| AS-48 | Multi-repo support | Architectural change — graph spanning multiple repositories requires a different store partitioning model. No sprint slot; revisit when eShopOnWeb single-repo is stable. |

### Retired

| ID | Item | Reason |
|---|---|---|
| AS-49 | gRPC / protobuf tool skill | Sprint 2 validated that the skill system creates language-specific tools on-the-fly without code change. Explicitly scheduling a gRPC skill is contrary to that thesis claim. If a target repo contains `.proto` files the orchestrator will create the skill. No sprint work required. |

---

## Non-Negotiables

- No tool is hardcoded — all tools are loaded via skills at runtime
- LLM orchestrator owns all routing and reasoning decisions — no hand-coded logic
- Skills contain zero domain knowledge — tool instructions only
- Correction capture is first-class — not an afterthought
- Every sprint is demonstrable end-to-end before the next begins
- Every sprint references the thesis claim it validates — see Thesis Validation Map

---

## Current Confidence (updated post Sprint 4 — see RETRO-S0-S4.md)

| Dimension | Score | Movement | Rationale |
|---|---|---|---|
| Implementation | 9/10 | ↑ +1 | All 5 thesis sprints delivered; correction loop stable; eShopOnWeb full-repo scale still untested |
| Usability | 8/10 | ↓ -1 | Blast radius, domain summary, correction-aware queries proven on synthetic fixture; node count non-determinism (39–92 for same input in sprint 4) is a usability risk at scale; real SME on real codebase unvalidated |
| Thesis | 9/10 | ↑ +2 | Operational SSR (sprints 0–2) + community-level queries (sprint 3) + domain SSR correction loop (sprint 4) experimentally validated; Gap Reports (Loop 2) is the remaining unproven claim |
| Observability | 7/10 | ↑ +1 | Per-sprint cost/token/model tracked; prompt versioning audit trail live; per-call span visibility (AS-54) still deferred |

The system that knows what it does not know is more trustworthy than one that silently covers gaps. Gap Reports and loop exit criteria are evidence of self-awareness — which changes the risk profile more than the scores capture.
