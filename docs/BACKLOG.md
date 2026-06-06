# ATLAS-SAGE: BACKLOG

**Status:** ACTIVE  
**Version:** 0.3  
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

**Status:** ✅ COMPLETE. Validated end-to-end with SCSS (`tests/test_scss.py` — 2 passed, ~80s, ~$0.056). PostCSS skill created on-the-fly by LLM; 12 AST nodes with typed edges stored; query returned grounded structured answer. C# ingestion deferred to Sprint 1 (requires multi-file context anyway).

---

## Sprint 1 — Graph Edges (Single Language)

**Goal:** Multiple C# files. Edges between nodes. Graph traversal at query time.

| ID | Task |
|---|---|
| AS-10 | Multi-file ingestion — orchestrator processes all .cs files via loaded skill |
| AS-11 | Edge extraction: CALLS, IMPLEMENTS, INHERITS, INJECTS |
| AS-12 | Edge storage with confidence metadata |
| AS-13 | graph_traverse tool wired at query time |
| AS-14 | Query depth control: orchestrator determines traversal depth by intent |
| AS-15 | Blast radius query: "what is impacted if X changes" — traversal answer |

**Exit criteria:** SME asks a cross-file architectural question. System traverses graph and assembles multi-node context. Answer references multiple files correctly.

---

## Sprint 2 — Skill System: Second Language + Quality Standards

**Goal:** Orchestrator handles a second language purely through skill discovery. Skill quality standards enforced. Zero code change.

| ID | Task |
|---|---|
| AS-16 | Point orchestrator at repo containing .ts files |
| AS-17 | Orchestrator calls create_skill for TypeScript (skill_model generates it) |
| AS-18 | Skill produced with handbook, summarisation_instructions, application_role |
| AS-19 | SSR loop runs — exit criteria declared, safety limit 5 loops |
| AS-20 | Skill must declare execution environment (Node.js vs project-aware) |
| AS-21 | Specialist must propose native/official library before parser fallback |
| AS-22 | Handbook stored alongside skill in registry |
| AS-23 | Verify: second language processed without any code change — skill only |

**Exit criteria:** A .ts file is ingested correctly via a skill that includes handbook, execution environment declaration, and used the TypeScript Compiler API (native) not Tree-sitter (generic fallback).

---

## Sprint 3 — Community Summaries

**Goal:** Community detection over AST graph. Tier-2 community summaries generated.

| ID | Task |
|---|---|
| AS-20 | Leiden/Louvain community detection over graph edges |
| AS-21 | Community hierarchy mapped to: project → namespace → class |
| AS-22 | Community summary generation via orchestrator LLM |
| AS-23 | Community nodes stored with embeddings |
| AS-24 | Cross-cutting query routing: orchestrator identifies domain-level intent → community summaries pulled |

**Exit criteria:** SME asks "what does the payment domain do?" System answers from community summary, not individual chunks.

---

## Sprint 4 — Correction Capture (Loop 1)

**Goal:** SME corrections are captured and update the graph.

| ID | Task |
|---|---|
| AS-25 | Correction capture UI — SME flags wrong answer inline |
| AS-26 | Correction stored against node/edge/community |
| AS-27 | Corrected nodes re-summarised on next ingestion run |
| AS-28 | Correction history visible to Tier-2 in subsequent queries |
| AS-29 | Verify: corrected edge produces different answer on re-query |

**Exit criteria:** SME corrects a wrong edge inference. Next query against same node reflects correction. System is measurably smarter.

---

## Sprint 5 — Gap Reports (Loop 2)

**Goal:** Ingestion run emits structured gap report. Custom instructions generated for next run.

| ID | Task |
|---|---|
| AS-30 | Gap report emitted at end of every ingestion run |
| AS-31 | Unparseable files logged with file type and recommended skill |
| AS-32 | Unresolved edges logged with confidence breakdown |
| AS-33 | Gap report → custom instructions generation for next run |
| AS-34 | Verify: second run on same repo is measurably more complete than first |

**Exit criteria:** Run 1 identifies SCSS files as a gap. Gap report recommends PostCSS skill. Run 2 processes SCSS files correctly via auto-created skill.

---

## Sprint 6 — Cross-Language Edges

**Goal:** TS frontend and C# backend connected via HTTP_CALLS edges.

| ID | Task |
|---|---|
| AS-35 | Static URL string matching: TS fetch literal → extracted C# route |
| AS-36 | Synthetic contract node generation from route attributes (no OpenAPI) |
| AS-37 | Cross-language edge storage with confidence tier |
| AS-38 | Inferred edge — Tier-2 reasons over candidates, stores with evidence |
| AS-39 | Full-stack query: "what happens when this button is clicked" — traverses TS → C# → DB |

**Exit criteria:** SME asks a full-stack question spanning frontend and backend. System traces path across language boundary and assembles coherent answer.

---

## Backlog (Unscheduled)

| ID | Item |
|---|---|
| AS-40 | LiteLLM gateway — model-agnostic routing, local model support | ✅ Done |
| AS-41 | vLLM / Ollama local deployment option | ✅ Done (ollama/ prefix supported via ATLAS_OLLAMA_BASE) |
| AS-42 | Git-push hook for incremental re-ingestion |
| AS-43 | Prompt cache optimisation (static prefix ordering) | ⏳ Sprint 1 candidate |
| AS-44 | Multi-repo support |
| AS-45 | gRPC / protobuf tool skill |
| AS-46 | OpenAPI spec ingestion when available |
| AS-47 | SME session history as community correction source |
| AS-48 | Gap report dashboard UI |
| AS-49 | Thesis evolution — update THESIS-SSR.md after Sprint 4 domain SSR validation |

---

## Non-Negotiables

- No tool is hardcoded — all tools are loaded via skills at runtime
- LLM orchestrator owns all routing and reasoning decisions — no hand-coded logic
- Skills contain zero domain knowledge — tool instructions only
- Correction capture is first-class — not an afterthought
- Every sprint is demonstrable end-to-end before the next begins
- Every sprint references the thesis claim it validates — see Thesis Validation Map

---

## Current Confidence (updated post SCSS validation)

| Dimension | Score | Rationale |
|---|---|---|
| Implementation | 8/10 | Walking skeleton validated. SSR operational loop proven. LanceDB graph traversal at scale untested. |
| Usability | 9/10 | Hybrid skill loop 1 produced SME-ready output. Domain SSR with real SME unvalidated. |
| Thesis | 7/10 | Operational SSR fully validated. Domain SSR (Sprint 4) is the remaining thesis risk. |

The system that knows what it does not know is more trustworthy than one that silently covers gaps. Gap Reports and loop exit criteria are evidence of self-awareness — which changes the risk profile more than the scores capture.
