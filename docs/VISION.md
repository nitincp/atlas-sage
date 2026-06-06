# ATLAS-SAGE: VISION

**ATLAS** — AST-anchored LLM Analysis System  
**SAGE** — the accumulated wisdom the system builds over a codebase

**Status:** ACTIVE  
**Version:** 0.3  
**Classification:** Internal AI Infrastructure / Developer Intelligence Platform

**Foundational thesis:** `THESIS-SSR.md` — Structured Speculation and Reinforcement: A Pattern for Extracting Tacit Knowledge from Complex Systems

**Project purpose:** ATLAS-SAGE is simultaneously a production system and a live validation of the SSR thesis. Every sprint either validates a thesis claim or evolves it. The system is the proof.

**Current confidence:**
- Implementation: 8/10 — walking skeleton validated end-to-end, SSR operational loop proven
- Usability: 9/10 — hybrid skill loop demonstrated SME-ready output from loop 1; domain SSR with real SME remains to be validated

---

## 1. The Problem

Legacy enterprise codebases — particularly in regulated domains — have no documentation. Understanding lives in people's heads. The code is the only source of truth, and it is polyglot: .NET backends, TypeScript frontends, HTML, CSS, configuration, contracts.

Existing approaches fail because they treat this as a retrieval problem. It is not. It is a **knowledge surfacing problem**. The SME already knows the answer — they just cannot articulate it without provocation.

---

## 2. The Philosophy

### Orchestration-First

Every decision that can be made by an LLM must be made by an LLM. The system does not hand-code routing logic, confidence scoring, chunking strategies, or edge inference. It provides tools. The LLM decides how and when to use them.

Manual optimisation of decisions the LLM already owns is premature complexity. It produces systems that are brittle, harder to maintain, and less capable than the model they are constraining.

### SSR — Structured Speculation and Reinforcement

The core intellectual principle that ATLAS-SAGE is built on. Not a workaround. A deliberate design position.

The entire GenAI field is organised around suppressing hallucination. RAG exists to suppress it. Grounding exists to suppress it. Confidence scoring exists to suppress it. SSR inverts this premise.

In a zero-documentation legacy codebase, suppression leaves you with nothing. A confident wrong interpretation anchored to real structure is more valuable than a correct silence.

**Structured Speculation** — the system generates confident hypotheses anchored to real AST edges, real type names, real call graphs. Not random hallucination. Wrong in the right neighbourhood. The LLM's plausible-but-wrong answer is a Socratic probe that provokes tacit knowledge the SME could not otherwise articulate.

**Reinforcement** — every SME correction is captured against the specific graph node or edge it corrects. The graph is strengthened permanently. The next SME starts from a stronger baseline. Speculation without Reinforcement leaves the system confidently wrong forever. Reinforcement without Speculation gives the SME nothing to react to.

Together they form a loop. The loop is SSR.

#### The Four Conditions

SSR is load-bearing only when all four conditions hold. Remove any one and the principle collapses:

1. A human holds tacit knowledge the system cannot access from code alone
2. That human cannot articulate the knowledge without provocation
3. The cost of a wrong answer is correction effort, not system failure
4. The correction itself is the artifact being harvested

Legacy codebase SME sessions satisfy all four. That is why SSR works here.

### The Graph is Ground Truth

Structural relationships extracted from compilers and language tools are deterministic. A method call is a method call. The right tool resolves it. This structural truth is the scaffold on which Structured Speculation operates — wrong in the right neighbourhood, never randomly wrong.

Which tool is the right tool is a runtime decision, not an architectural one. Tools are discovered and loaded via Skills.

---

## 3. The Scope

ATLAS-SAGE operates across the full polyglot surface of a modern enterprise codebase. No language is hardcoded. No tool is prescribed. When the orchestrator encounters a file type it has not seen before, it searches the Skill registry. If no skill exists, it creates one.

Examples of file types in scope: `.cs`, `.csproj`, `.sln`, `.ts`, `.tsx`, `.js`, `.html`, `.css`, `.scss`, `.proto`, `.json`, `.yaml`. This list is not exhaustive — it grows as the Skill registry grows.

The tool layer is a **registry discovered at runtime**, not a hardcoded pipeline.

---

## 4. Two Learning Loops

ATLAS-SAGE maintains two distinct, non-overlapping feedback loops:

### Loop 1 — Domain Knowledge

Operates at the codebase level. SME corrections during chat sessions update the graph. An edge the LLM inferred incorrectly gets corrected. A community summary that missed domain intent gets refined. This loop grows understanding of a specific codebase over time.

### Loop 2 — Operational Capability

Operates at the system level. After each ingestion run, the orchestrator emits a Gap Report: files it could not parse, edges it could not resolve, tools it could not find. These gaps drive Skill creation. Each Skill describes how to use a tool — never what the codebase means. Skills are portable across every codebase ATLAS-SAGE is pointed at.

The two loops never mix. Domain knowledge is codebase-specific. Operational capability is universal.

---

## 5. The Skill System

ATLAS-SAGE is self-extending through a Skill registry. A Skill is a reusable, LLM-authored recipe for using a specific tool against a specific file type.

- Skills contain **no domain knowledge** — they are tool instructions only
- Skills are **IP-safe** — a SCSS parsing skill describes PostCSS, not your codebase
- Skills are **searchable** — the orchestrator finds existing skills before attempting new work
- Skills are **self-generated** — the LLM creates missing skills using the create-skill skill
- Skills are **cumulative** — each run leaves the system more capable than before

### IP Preservation

Skills are the IP boundary. A skill describes how PostCSS parses SCSS. It contains zero knowledge of what any specific codebase means. Skills can be shared, reused, and open-sourced across organisations without legal risk. This removes a critical adoption barrier in regulated industries where client code is strictly confidential.

The codebase knowledge lives in the graph. The tool knowledge lives in the skill. They never mix.

### Token Efficiency

The specialist LLM is called once per skill creation cycle — not once per file, not once per run. A skill created today for SCSS parsing is reused on every future codebase ATLAS-SAGE encounters. At enterprise scale across a polyglot monolith this represents a compounding reduction in inference cost.

The SSR loop amplifies this further: skills stabilise in 3–5 loops. After stabilisation, zero specialist calls are needed for that file type across any codebase.

### Knowledge Handbook

Every skill creation interaction also produces a **Knowledge Handbook** for the file type — a plain English description of what the technology means in an application context, what domain signals it carries, and what it cannot express. The handbook is produced by the specialist LLM in Interaction 1 and enriched in subsequent loops as new understanding surfaces.

The handbook serves three purposes:
- Informs ATLAS's summarisation — what to look for and how to describe it
- Guides query routing — which questions this file type can and cannot answer
- Transfers to new team members — a living reference that grows with the system

### Tool Selection Hierarchy

Skills are not all equal. The specialist LLM selects tools in priority order:

```
1. Native / official library    → highest semantic fidelity
2. Established parser           → structural fidelity
3. Generic parser (Tree-sitter) → syntactic only
4. Generated script             → last resort, fragile
```

Every skill must also declare its **execution environment** — the sandbox required to run it. Simple skills run in Node.js. Complex language tools (Roslyn, TypeScript Compiler API) require a project-aware environment. Declaring this upfront prevents silent execution failures.

### Validated by SSR Loop Tests

The skill system was validated live in two tests against the same 5-file SCSS codebase. Full evidence in `THESIS-SSR.md` section 4.

**Test 1 — Parser skill (PostCSS):**
- STABLE after 4 loops
- 45 → 51 nodes as BEM extraction added in loop 2
- 4 specialist calls total

**Test 2 — Hybrid skill (Dart Sass + PostCSS):**
- STABLE after 3 loops
- 56 nodes from loop 1 — BEM visible immediately
- Compilation health signals surfaced — deprecation warnings, upgrade debt
- A class of output structurally unavailable to any parser regardless of loop count

**Key finding:** Declaring only OS and architecture in the environment prompt — letting the specialist choose tools — produced a better skill in fewer loops. The sandbox is not optional. It is a design constraint.

---

## 7. What ATLAS-SAGE is Not

- It is **not a documentation generator** — it produces understanding scaffolds, not finished docs
- It is **not a search engine** — vector search is one mechanism, not the purpose
- It is **not a static analysis tool** — correctness of interpretation is the LLM's concern
- It is **not RECAP** — RECAP optimised for grounded certainty in a single-language monolith; ATLAS-SAGE optimises for productive exploration across a polyglot surface
- It is **not suppressing hallucination** — it is structuring speculation and reinforcing correction

---

## 8. The North Star

An SME sits down cold — no documentation, no tribal knowledge, no onboarding. They ask a question about a module they have never seen. ATLAS-SAGE speculates confidently, anchored to the graph. The SME corrects it. The correction is captured. SAGE gets smarter.

The next SME starts further ahead. The one after that, further still.

Over time ATLAS-SAGE accumulates something no wiki, no Confluence page, and no onboarding document ever captured: the actual tacit understanding of how the system works, extracted one Reinforced Correction at a time.

That is SAGE. That is what the name means.

---

## 9. Portfolio Position

ATLAS-SAGE is not a standalone tool. It is the third and most complete expression of a pattern — SSR — discovered iteratively across Skills SME, CACA, and ATLAS-SAGE. Each system identified what the previous was missing. ATLAS-SAGE closes the loop.

The thesis (`THESIS-SSR.md`) documents the intellectual arc. ATLAS-SAGE is its live implementation. Every sprint either validates a claim in the thesis or generates new evidence that evolves it.

This is what senior AI systems architecture looks like in regulated enterprise contexts: not a product demo, but a body of work with a thesis, a lineage, and reproducible evidence.

The pattern — SSR — is the contribution. ATLAS-SAGE is the proof.
