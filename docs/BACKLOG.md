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
| Sprint 5 (Branch B) | **Semantic Synthesis** — plain-English summaries read holistically produce SME-validatable BDD without explicit cross-type edges |
| Sprint 6 (Branch B) | Traceability index — every BDD sentence traces back to the raw code that produced it |
| Sprint 7 (Branch B) | SME→skill feedback loop — BDD correction updates `skill.summarisation_instructions`; re-ingest produces measurably better BDD |
| Sprint 8 (Branch B) | Stress tests — synthesis holds under name collision, missing links, noise files, multi-chain scenarios |
| Sprint 9 (Branch B) | eShopOnWeb — full polyglot codebase validates Branch B at scale |

Sprint 4 closed the Domain SSR claim for Branch A. The next claim — Branch B Semantic Synthesis — emerged experimentally during Sprint 5 planning: 4 files in 3 languages produced a complete BDD specification from plain-English summaries alone, with no cross-type edges. See `docs/THESIS-SSR.md` § 4.7 for the full evidence and the new SSR loop.

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

## Sprint 5 (Branch B) — BDD Synthesis Pipeline

**Goal:** Given any set of ingested files, the pipeline produces a BDD specification that a non-technical SME can read and validate. This is the first Branch B deliverable — formalising the finding from the experimental test into a callable pipeline function.

**Context:** The experimental test (2026-06-08) ingested 4 files (Python, TypeScript, HTML, SCSS) using `ingest()` unchanged from Sprint 4, then passed all 29 resulting node summaries to the LLM with a synthesis prompt. The output was 6 BDD scenarios in plain English. Sprint 5 wraps this into a first-class pipeline function with a test harness spec.

| ID | Task | Status |
|---|---|---|
| AS-68 | THESIS-SSR.md Branch B documentation — discovery, evidence, SSR loop diagram, traceability chain, relationship to Branch A | ✅ Done |
| AS-69 | `synthesise_bdd(config) → (bdd_text, stats)` pipeline function — reads all nodes from store via `list_nodes`, passes summaries + a product-owner synthesis prompt to Tier-2 LLM, returns Given/When/Then markdown | ⬜ Pending |
| AS-70 | BDD synthesis prompt — instructs LLM to: group behaviours by actor/trigger, write each scenario in Given/When/Then, use plain English (no class names or file paths), output markdown | ⬜ Pending |
| AS-71 | Sprint 5 harness spec — ingest `test_harness/fixtures/product_chain/` (4 files, 3 languages), call `synthesise_bdd()`, assert: ≥4 scenarios, loading state scenario present, no technical jargon in scenario text | ⬜ Pending |

**Fixture:** `test_harness/fixtures/product_chain/` — created during experimental test. `api.py` (Flask), `products.ts`, `index.html`, `product.scss`. The loading state thread across all three frontend files is the key signal.

**Exit criteria:** `synthesise_bdd()` called after ingesting the product_chain fixture produces ≥4 BDD scenarios in plain English. The loading state behavioral thread (SCSS + HTML + TypeScript independently describing it) appears as a unified scenario. A non-technical SME reading the output can validate or correct each scenario without referring to source code.

---

## Sprint 6 (Branch B) — Traceability Index

**Goal:** Every BDD scenario sentence maps back to the node summaries that contributed to it, and every node summary maps back to its `raw_cleaned` source code. The traceability chain is what makes SME corrections actionable.

**Context:** Without traceability, an SME can say "this scenario is wrong" but cannot tell the system which translation caused it. The chain `BDD scenario → summary → raw_cleaned → skill.summarisation_instructions` is the feedback path. Sprint 6 makes this chain explicit and queryable.

| ID | Task | Status |
|---|---|---|
| AS-72 | `synthesise_bdd()` extended to return `bdd_with_trace` — each scenario annotated with the node_ids whose summaries contributed to it (LLM identifies contributing nodes as part of synthesis) | ⬜ Pending |
| AS-73 | `get_bdd_trace(scenario_text, store)` — given a BDD scenario, returns: contributing node summaries, their `raw_cleaned` source, and the `skill_id` whose `summarisation_instructions` produced them | ⬜ Pending |
| AS-74 | Sprint 6 harness spec — after BDD synthesis, assert: each scenario has ≥1 contributing node; the loading state scenario traces back to nodes from all 3 frontend files; `raw_cleaned` is non-empty for all traced nodes | ⬜ Pending |

**Exit criteria:** For every BDD scenario produced, the system can name which node summaries contributed to it and which source lines they came from. An SME correcting a scenario can follow the trace to the exact `summarisation_instructions` that needs updating.

---

## Sprint 7 (Branch B) — SME→Skill Feedback Loop

**Goal:** SME validates a BDD scenario, marks it wrong, the system traces the correction back to the responsible `skill.summarisation_instructions`, updates them, and re-ingests the affected files. The next BDD output reflects the correction.

**Context:** This is the deepest feedback level in Branch B's SSR loop. Updating `summarisation_instructions` improves how every node of that chunk type is translated — in this codebase and all future ones. The correction propagates forward without touching individual nodes.

| ID | Task | Status |
|---|---|---|
| AS-75 | `update_skill_summarisation(skill_id, chunk_type, instruction_delta, store)` — appends or replaces a correction clause in `skill.summarisation_instructions` for the given chunk type | ⬜ Pending |
| AS-76 | Skill re-run after summarisation update — re-execute skill extraction + summarisation on affected file(s), overwrite existing nodes with improved summaries, re-embed | ⬜ Pending |
| AS-77 | Sprint 7 harness spec — deliberately introduce a bad `summarisation_instructions` clause in the SCSS skill; run synthesis; SME "correction" provided as test input; update instructions; re-ingest; assert BDD output changed and is more accurate | ⬜ Pending |

**Exit criteria:** A known-bad summarisation instruction produces a wrong BDD scenario. The correction updates `skill.summarisation_instructions`. Re-ingesting the file produces a node summary that triggers a correct BDD scenario on the next synthesis pass. The original wrong scenario is gone.

---

## Sprint 8 (Branch B) — Stress Tests

**Goal:** Confirm that semantic synthesis holds — and degrades gracefully — under conditions harder than the clean product_chain fixture.

**Levels are cumulative: each adds one complication to the previous fixture.**

| ID | Level | Scenario | What it tests |
|---|---|---|---|
| AS-78 | Level 2 | Name collision — two unrelated CSS components share a class name (e.g. `.card` used in both product list and user profile) | Synthesis must produce two separate behavioral threads, not merge them. |
| AS-79 | Level 3 | Missing link — SCSS and HTML present; TypeScript file absent (no fetch logic) | Gap surfaces as an incomplete scenario: behaviour stops at "data is displayed" with no "data is fetched" origin. |
| AS-80 | Level 4 | Noise files — add `config.yaml`, `README.md`, `package.json` to the fixture directory | Summaries of non-behavioral files must not pollute BDD output; scenarios must still be behaviorally coherent. |
| AS-81 | Level 5 | Multi-chain — add a second independent behavioral thread (e.g. a shopping cart alongside the product list) | Two separate BDD scenario groups produced; loading state thread for products does not bleed into cart scenarios. |

**Exit criteria per level:** BDD output changes in the expected direction. The complication does not collapse the output — it shapes it correctly.

---

## Sprint 9 (Branch B) — eShopOnWeb Validation

**Goal:** Run the full Branch B pipeline on `eshoponweb/` — a real, multi-language reference application. BDD output reviewed by a technical SME (Nitin) as a proxy for non-technical SME validation.

**Context:** eShopOnWeb is the existing git submodule at `eshoponweb/`. It contains C#, TypeScript, SCSS, HTML, and YAML. Skills for all file types will be created on-the-fly. The test validates that Branch B holds at real-world scale and polyglot diversity.

| ID | Task | Status |
|---|---|---|
| AS-82 | Run `ingest_directory("eshoponweb/", config)` with skill creation for all encountered file types | ⬜ Pending |
| AS-83 | Run `synthesise_bdd()` over all ingested nodes — expect 10–20+ BDD scenarios across multiple domain threads | ⬜ Pending |
| AS-84 | Review BDD output for: recognisable eShopOnWeb behaviours (product catalog, cart, checkout, auth), no jargon leakage, no merged chains from unrelated domains | ⬜ Pending |
| AS-85 | Introduce one known correction (e.g. checkout flow misrepresented), update `summarisation_instructions`, re-ingest affected files, verify BDD output corrects | ⬜ Pending |
| AS-86 | Sprint 9 harness spec — automated assertions on scenario count, domain coverage, jargon-free text; SME review recorded as a correction in the corrections table | ⬜ Pending |

**Exit criteria:** eShopOnWeb BDD output contains recognisable behavioural scenarios for the main shopping flows. At least one SME correction demonstrably improves the output via the `summarisation_instructions` feedback path. The system has not required any code changes since Sprint 4.


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

Items are grouped by the sprint that unlocks them. Nothing here is picked up unless explicitly pulled into a sprint during planning.

### Unlocked by retro (not sprint-gated)

| ID | Item |
|---|---|
| AS-61 | Add `--canonical` filter to `harness_query` CLI — `canonical: true` field added by AS-59; CLI has no way to query it yet; small addition, deferred until there are enough runs that filtering by canonical matters |

### Activates after Sprint 7 (feedback loop stable)

| ID | Item |
|---|---|
| AS-47 | Prompt cache optimisation (static prefix ordering) — per-sprint cost is $0.52 on the 4-file fixture; eShopOnWeb will multiply input tokens significantly; static prefix caching is the primary cost lever |
| AS-56 | Provider fallback for rate limits — `num_retries=3` handles Gemini 429s (Sprint 3 evidence); LiteLLM Router `fallbacks` per model tier is the production hardening step when retrying the same provider burns quota at scale |
| AS-54 | Telemetry / distributed trace integration — LiteLLM callbacks + Langfuse for per-call span visibility; complement to run_log aggregate stats; relevant when real-repo usage begins |
| AS-51 | BDD-to-community propagation — accumulated SME corrections on BDD scenarios should backfill community summaries; natural extension once the SME→skill feedback loop is stable |

### Activates after Sprint 9 (eShopOnWeb validated)

| ID | Item |
|---|---|
| AS-46 | Git-push hook for incremental re-ingestion — triggers re-ingest on push; depends on BDD synthesis pipeline being stable enough to consume programmatically |
| AS-50 | OpenAPI spec ingestion — Branch B proves cross-language chains without OpenAPI; this is the fast path to add once the synthesis baseline is established |

### Deferred — no sprint gate

| ID | Item | Note |
|---|---|---|
| AS-48 | Multi-repo support | Architectural change — graph spanning multiple repositories requires a different store partitioning model. Revisit when eShopOnWeb single-repo is stable. |

### Retired

| ID | Item | Reason |
|---|---|---|
| AS-49 | gRPC / protobuf tool skill | Sprint 2 validated that the skill system creates language-specific tools on-the-fly without code change. Explicitly scheduling a gRPC skill is contrary to that thesis claim. If a target repo contains `.proto` files the orchestrator will create the skill. No sprint work required. |
| AS-34 | Gap report emitted at end of every ingestion run | Branch B makes explicit gap tracking unnecessary — the synthesis pass surfaces missing behavioral threads as incomplete scenarios. Structural gaps are now semantic gaps, which are more useful. |
| AS-35 | Skill failure gap report | Retained implicitly: a file type with no skill still fails to ingest and won't appear in synthesis. Explicit gap report format deferred. |
| AS-36 | Unresolved binding gap | Branch B does not require `target_ref` binding edges. The `__ref__` sentinel approach is deferred with the cross-type binding work it depended on. |
| AS-52 | Gap report dashboard UI | Retired with AS-34 — no gap report schema to build a UI over. |
| AS-64 | `target_ref` resolution at query time | Retired — Branch B does not use `target_ref` sentinels. |


## Non-Negotiables

- No tool is hardcoded — all tools are loaded via skills at runtime
- LLM orchestrator owns all routing and reasoning decisions — no hand-coded logic
- Skills contain zero domain knowledge — tool instructions only
- Correction capture is first-class — not an afterthought
- Every sprint is demonstrable end-to-end before the next begins
- Every sprint references the thesis claim it validates — see Thesis Validation Map

---

## Current Confidence (updated 2026-06-08 — Branch B discovery)

| Dimension | Score | Movement | Rationale |
|---|---|---|---|
| Implementation | 9/10 | → | Branch A (Sprints 0–4) fully delivered. Branch B pipeline (synthesise_bdd, traceability, SME→skill loop) not yet implemented — experimental test used ad-hoc LLM call, not a production function. Score holds pending Sprint 5–7. |
| Usability | 9/10 | ↑ +1 | BDD output is a direct SME validation surface — no graph traversal knowledge required. Non-technical stakeholder can read and correct a scenario directly. This changes the usability ceiling. |
| Thesis | 10/10 | ↑ +1 | Branch B finding: plain-English summaries reconstruct cross-language behavioral chains without explicit edges. Experimentally confirmed on 29-node, 4-file, 3-language fixture. Loading state thread found across SCSS + HTML + TypeScript with no declared relationship. SSR loop closes at `skill.summarisation_instructions` — the deepest feedback level possible. |
| Observability | 7/10 | → | Run log, cost tracking, prompt versioning all live. Traceability index (BDD sentence → node → raw code) is the next observability layer — Sprint 6. |

Branch B shifts the confidence ceiling. The original thesis was "LLM-anchored graph queries answer architectural questions." Branch B adds: "the translation layer is the primary knowledge artifact, and correcting it corrects everything downstream." This is a stronger claim with stronger evidence.

