# ATLAS-SAGE: Sprint 0–4 Retrospective

**Date:** June 2026  
**Scope:** Sprint 0 (walking skeleton) through Sprint 4 (domain SSR loop closure)  
**Purpose:** Start-gate for Sprint 5 — what the evidence says before the next loop begins

---

## Delivery Summary

| Sprint | Thesis claim validated | Key observable evidence | Cost | Result |
|---|---|---|---|---|
| Sprint 0 | SSR operational loop works end-to-end | PostCSS skill created on-the-fly; 26 SCSS nodes + typed edges stored; grounded query answered | $0.15 | Pass |
| Sprint 1 | Structured Speculation anchored to graph produces useful output | Blast radius traced `IOrderRepository → OrderService → OrderController` via inbound depth=3; dependency query traced outbound correctly | $0.36 | Pass |
| Sprint 2 | Skill system self-extends without code change | TypeScript ts-morph skill created in 3 attempts (SSR self-healing); zero code change; native parser enforced | $0.43 | Pass |
| Sprint 3 | Community summaries answer cross-domain queries | 7 Louvain communities over 60 nodes/27 edges; domain-intent query routed to community layer; Gemini 429 auto-recovered | $0.41 | Pass |
| Sprint 4 | Domain SSR: human corrections accumulate as graph knowledge | `search_corrections` surfaced as first line of Q2 answer; Q1→correction→Q2 loop observable in output | $0.52 | Pass (2nd run) |

**Canonical run totals:** ~$1.89 across 5 sprints, ~1.4M input tokens, ~93K output tokens  
**Total iterations (all runs, both systems):** 17 (11 test_harness + 6 pre-harness test_runs)  
**Failed first pass:** Sprint 4 only (node count non-determinism dropped below min_nodes assertion on run 10)

---

## What Worked

**Walking skeleton discipline held.** Every sprint was demonstrable end-to-end before the next started. Sprint 1's test harness infrastructure (SprintSpec, prompt versioning, cost tracking) emerged from sprint need mid-sprint — not as up-front planning. The discipline prevented architecture without evidence.

**LLM orchestration absorbed situations that would have required code fixes:**
- Sprint 2: ts-morph API hallucinations on skill creation attempts 1 and 2; orchestrator retried within the SSR loop and succeeded on attempt 3 of 5. No code change.
- Sprint 3: Gemini embedding hit a 429 mid-run; LiteLLM retry recovered without intervention. Run still passed.
- Sprint 4: per-node correction UUID lookup proved unstable; the pivot to `search_corrections(query_text)` upfront was a design-level change, not a patch. Stable on the next run.

Each was a live validation of the orchestration-first principle. A hand-coded routing system would have required a code change in all three cases.

**Prompt versioning created a complete audit trail.** 6 prompt versions captured across a single development day (12:44–16:11), tracking character-level deltas between versions. The v004→v005 delta (`query +849 chars`) maps directly to the correction-aware query changes in Sprint 4 — traceable without git blame.

**Cost curve is now evidence.** Sprint cost trend: `$0.15 → $0.36 → $0.43 → $0.41 → $0.52`. The Sprint 3→4 delta ($0.11) is attributable to one additional tool call per query (`search_corrections`). First time we have per-feature cost attribution.

---

## What Didn't Work

**C# deferred twice, now indefinite.** Sprint 0 goal was a C# file end-to-end. Sprint 1 also targeted C#. Both pivoted — Roslyn/.NET toolchain is heavier than a skill can install at runtime. The primary target codebase (eShopOnWeb) is C#. The most important language for the project is the one we have not validated.

**Community detection is edge-density-sensitive.**  
- Sprint 3: 60 nodes, 27 edges → 7 communities (density 0.45)  
- Sprint 4: 90 nodes, 21 edges → 0 communities (density 0.23)  

Same algorithm (Louvain), same fixture, 2.3× more nodes — zero communities. The boundary condition is uncharacterized. Sprint 4 passed because `min_communities` was not asserted. If Sprint 5 relies on community routing for gap report classification, this is a latent risk.

**Node count non-determinism is wider than expected.** Sprint 4 runs produced 39, 92, and 90 nodes for the same four input files. A 2.3× spread from a single LLM difference in chunk boundary decisions. The lower bound (39 nodes) caused the run 10 failure — below the `min_nodes` assertion. "Wrong in the right neighbourhood" is acceptable; a 2.3× count variance affects cost predictability and assertion calibration.

**test_runs/ orphaned the pre-harness history.** Six runs (12:46–13:09) exist in a separate directory with a separate `run_log.json` that the test_harness system does not know about. The true-first prompt version (hash `dfd77cd7`, 16 minutes before test_harness v001) is invisible to harness tooling. `harness_query --aggregate sprint` silently undercounts sprint 0 and sprint 1 iteration history.

**THESIS-SSR.md not updated after Sprint 4.** AS-53 has been open since sprint 4 completed. Sprint 4 is the highest-value thesis validation — "Domain SSR: human corrections accumulate as graph knowledge" — and it is not reflected in the paper. The thesis is currently a first draft that does not include the correction-capture evidence from the system it describes.

---

## Design Decisions That Changed

| What changed | Before | After | Driver |
|---|---|---|---|
| Sprint 0 language | C# | SCSS | Toolchain weight; SCSS gives a cleaner walking skeleton |
| Sprint 1 language | C# | Python | Roslyn/.NET; Python has all four edge types needed |
| Correction lookup | `get_corrections(node_id)` per node | `search_corrections(query_text)` once upfront | UUID match depends on LLM node selection order — non-deterministic |
| Correction target_id | Node UUID | Logical concept name (`"orderservice"`) | Stable across ingestion runs without requiring node lookup |
| Test infrastructure | Manual runs (test_runs/) | Automated SprintSpec + run_sprint() | Emerged from Sprint 1 iteration need; retro-applied to Sprint 0 |

---

## Technical Debt Register

| Ref | Item | Impact | Status |
|---|---|---|---|
| AS-53 | THESIS-SSR.md not updated with Sprint 4 domain SSR evidence | High — primary project artifact | Unblocked; ready to close |
| AS-57 | Gitignore misclassifies `prompts/`, `test_suites/`, `run_log.json` as generated artifacts | High — prompt engineering history and benchmark ledger lost on env rebuild | Open |
| AS-58 | test_runs/ orphaned — 6 pre-harness runs and true-first prompt disconnected from test_harness record | Medium — historical gap; harness_query undercounts | Open |
| AS-59 | No canonical marker in run_log.json | Medium — silent now; load-bearing as run volume grows | Open |
| — | Community detection edge-density boundary uncharacterized | Medium — 0 communities at density 0.23; risk for Sprint 5 community routing | Open |
| — | C# skill unvalidated | Medium-High — primary target codebase is C# | Indefinite |
| AS-55 | Skill validation loop informal — orchestrator inline-recovers but loop is not formalized | Low — adequate through Sprint 4; load-bearing at higher skill complexity | Unscheduled |

---

## Confidence Update

| Dimension | Score | vs. Last | Rationale |
|---|---|---|---|
| Implementation | 9/10 | ↑ +1 | All 5 thesis sprints delivered on target fixture; correction loop stable; eShopOnWeb full-repo scale still untested |
| Usability | 8/10 | ↓ -1 | Blast radius, domain summary, correction-aware queries proven on synthetic fixture; node non-determinism (39–92 for same input) is a real usability risk on larger inputs; real SME on real codebase unvalidated |
| Thesis | 9/10 | ↑ +2 | Operational SSR (sprints 0–2) + community-level queries (sprint 3) + domain SSR correction loop (sprint 4) all experimentally validated; Gap Reports (Loop 2) is the remaining unproven claim |
| Observability | 7/10 | ↑ +1 | Per-sprint cost/token/model tracked; prompt versioning audit trail live; per-call span visibility (AS-54) still deferred |

---

## Sprint 5 Start Gate

**What sprint 5 needs that we do not have yet:**
- Gap report schema — structured output format (not free-text ingestion_report.md)
- A second ingest pass pattern — run 1 identifies gaps, run 2 closes them; SprintSpec needs a two-pass fixture
- A fixture with deliberate gaps — e.g., mixed SCSS + Python where run 1 has no SCSS skill; run 2 should auto-create it

**What sprint 4 proved that sprint 5 can reuse:**
- The Q1→inject→Q2 pattern maps directly to run1→gap→run2; same harness structure
- `search_corrections` upfront is the model for how gap instructions should be injected — structured, stable, node-id-independent
- Cost baseline: $0.52/run; a second ingest pass adds ~60% — estimate $0.80–$1.00 per sprint 5 run

**Watch before Sprint 5 closes:** Community detection returned 0 in sprint 4 despite 90 nodes. If gap report routing uses community summaries to classify which skills are missing from which domains, the density boundary will surface again. Characterize it on a controlled fixture before relying on it.
