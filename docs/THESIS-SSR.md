# Structured Speculation and Reinforcement
## A Pattern for Extracting Tacit Knowledge from Complex Systems

**Author:** TinTin  
**Date:** June 2026  
**Classification:** Original Research / AI Systems Design  
**Status:** Validated through Sprint 4 — Domain SSR and Operational SSR both experimentally confirmed

---

## Abstract

Legacy enterprise systems — particularly in regulated domains — accumulate tacit knowledge that is never documented. This knowledge lives in people's heads and surfaces only under provocation. Existing AI approaches to this problem treat it as a retrieval problem and fail because there is nothing to retrieve. This paper proposes **Structured Speculation and Reinforcement (SSR)** — a pattern in which an AI system generates confident, structurally-anchored hypotheses designed to be wrong, and captures human corrections as the primary knowledge artifact. SSR reframes hallucination from a failure mode into a deliberate mechanism for extracting tacit knowledge from both human experts and from complex systems themselves. The pattern was discovered iteratively across three systems — Skills SME, CACA, and ATLAS-SAGE — each one identifying what the previous was missing. This paper traces that journey, defines the pattern formally, and validates it through a live implementation test.

---

## 1. The Problem

### 1.1 Tacit Knowledge in Complex Systems

Every complex system — whether a legacy codebase, an expert practitioner, or an organisational process — accumulates knowledge that is never written down. This knowledge exists in two forms:

**Explicit knowledge** is documented. It can be retrieved, searched, and transferred. Documentation, wikis, and onboarding guides carry it.

**Tacit knowledge** is embodied. It exists in the intuition of an experienced engineer who knows which module to distrust, in the architect who remembers why a particular pattern was chosen twelve years ago, in the developer who has never articulated why a certain approach always fails — they just know it does.

Tacit knowledge is the majority of what makes a system comprehensible to insiders and opaque to outsiders.

### 1.2 Why Documentation Fails

Documentation fails because tacit knowledge cannot be articulated in the abstract. An SME asked to document a legacy module will produce a description of what they think is important. They will omit what they consider obvious. They will forget what they have internalised so deeply it no longer feels like knowledge. The most valuable things they know are the least likely to appear in documentation.

### 1.3 Why Retrieval Fails

Retrieval-Augmented Generation (RAG) fails in the zero-documentation context for a simple reason: there is nothing to retrieve. A vector search over an undocumented codebase returns code. Code without context is not understanding. The model can read the code but cannot know what it *means* in the domain, why it was written that way, or what happens when it is changed.

The entire field of enterprise AI for legacy systems is organised around this retrieval assumption. It is the wrong assumption for the class of problem that matters most.

---

## 2. The Journey

The SSR pattern was not designed. It was discovered iteratively across three systems, each one revealing what the previous was missing.

### 2.1 Skills SME — The Judgment Layer

The first system was the **Skills SME** — an AI governance layer designed to supervise AI agent behaviour in a complex codebase context. The core insight was that AI agents lack a judgment layer between intent and execution. They know how to do things but not whether they should. The Skills SME externalised this judgment.

Key contributions:

- The concept of an **externalized judgment layer** — separating what the system decides from how it executes
- The identification that judgment must be **human-gated** to remain trustworthy — autonomous optimisation is safe, autonomous value updates are not
- The separation of **wrong direction** from **uncertain direction** — the core SME competency

The Skills SME also identified its own critical gap: **the learning loop was missing**. The system could govern. It could not grow. Each session started from the same baseline. The tacit knowledge surfaced in one session did not inform the next.

### 2.2 CACA — The Governance Architecture

The second system was **CACA** (Continuously Adaptive Cognitive Architecture) — a real-time AI agent governance system that formalised the Skills SME's insights into a complete architecture.

Key contributions:

- **Two distinct learning loops** — operational (autonomous, self-correcting) and domain (human-gated, versioned, auditable)
- **Semantic versioning for knowledge updates** — minor versions auto-applied, significant versions human-approved, major versions human-authored
- **Mapping to EU AI Act principles** — human oversight of judgment updates derived from first principles, not compliance requirements

CACA solved the governance problem completely. But it operated in real-time, governing agent behaviour session by session. The knowledge accumulated in one session still did not persist to the next in a structured way. The learning loop existed conceptually but had no mechanism to close it.

The missing piece: a way to extract tacit knowledge from the system itself — not just from human corrections — and accumulate it permanently.

### 2.3 ATLAS-SAGE — The Loop Closes

The third system was **ATLAS-SAGE** (AST-anchored LLM Analysis System / SAGE) — a polyglot codebase intelligence platform. ATLAS-SAGE brought three new elements that the previous systems lacked:

**The graph as scaffold.** Instead of a flat document corpus, ATLAS-SAGE builds a graph of structural relationships extracted by compiler-grade tools (Roslyn, TypeScript Compiler API, PostCSS). These relationships are deterministic. They are not inferred. A method call is a method call.

**The skill system.** ATLAS-SAGE is self-extending. When it encounters a file type it cannot parse, it delegates to a specialist LLM which creates a reusable skill. Skills carry no domain knowledge — they are tool instructions only. They are portable across every codebase ATLAS-SAGE is pointed at.

**SSR as the operating principle.** ATLAS-SAGE does not suppress hallucination. It structures speculation — anchors it to the graph so it is wrong in the right neighbourhood — and captures every correction as a permanent graph update.

The learning loop that Skills SME identified as missing and CACA could not close now has a mechanism. Skills SME was not superseded by ATLAS-SAGE. It became a first-class citizen inside the system it helped design.

```
Skills SME
  → externalized judgment layer
  → learning loop identified as missing

        ↓

CACA
  → two loops formalised
  → human-gated governance
  → loop still unclosed at system level

        ↓

ATLAS-SAGE
  → SSR closes the loop
  → Skills SME pattern applied to codebase knowledge
  → the system that was missing a learning loop
    becomes a system whose entire purpose
    is learning
```

---

## 3. The Pattern: SSR

### 3.1 Definition

**Structured Speculation and Reinforcement (SSR)** is a knowledge extraction pattern in which:

1. A system generates confident hypotheses anchored to known structural truth
2. These hypotheses are presented to a knowledge holder as plausible interpretations
3. The knowledge holder's correction — not confirmation — is the primary artifact
4. The correction is captured against the specific structural element that provoked it
5. The system's understanding is permanently updated

SSR is not a retrieval pattern. It is a provocation pattern. The system is not trying to retrieve knowledge that exists somewhere. It is trying to surface knowledge that exists only in a human mind and has never been articulated.

### 3.2 Structured Speculation

Structured Speculation is the first half of the loop. It is deliberate, disciplined hallucination.

**Random hallucination** is useless. A model that invents facts about a codebase provides no value because its confabulations have no relationship to structural reality.

**Structured Speculation** is different. The system reads real type names, real call graphs, real assembly boundaries, real AST edges. It generates a hypothesis that is consistent with this structure. The hypothesis may be wrong about intent, about domain meaning, about business context. But it is wrong in a specific, bounded, productive way.

The wrong answer provokes the right answer. An SME who cannot articulate what a module does in the abstract will immediately correct a plausible but wrong description. The correction contains the tacit knowledge. The speculation was the mechanism to extract it.

### 3.3 Reinforcement

Reinforcement is the second half of the loop. Every correction is captured as a permanent update against the specific node, edge, or community that provoked it. The graph is strengthened. The next query over that region starts from a better baseline.

Reinforcement without Speculation gives the system nothing to reinforce — the SME has no provocation, the tacit knowledge stays locked.

Speculation without Reinforcement leaves the system permanently wrong — each session confabulates the same errors because nothing was captured.

They are a pair. Neither operates without the other.

### 3.4 The Four Conditions

SSR is load-bearing only when all four conditions hold simultaneously. Remove any one and the pattern collapses:

**Condition 1 — Inaccessible tacit knowledge**
A human holds knowledge the system cannot access from available artifacts alone. If the knowledge can be extracted directly, retrieval is superior to speculation.

**Condition 2 — Articulation requires provocation**
The human cannot or does not articulate the knowledge without a specific prompt. If they can articulate it freely, documentation is superior to speculation.

**Condition 3 — Correction cost is manageable**
The cost of a wrong answer is effort spent correcting it, not system failure, safety incident, or irreversible action. SSR is not appropriate where wrong answers have severe consequences.

**Condition 4 — Correction is the target artifact**
The organisation benefits from capturing the corrections, not just from receiving correct answers. SSR is not appropriate where individual answers are the goal — it is appropriate where accumulated understanding is the goal.

Legacy codebase SME sessions satisfy all four conditions. That is why SSR works in this domain.

### 3.5 SSR at Multiple Levels

SSR operates at two distinct levels in ATLAS-SAGE, each with a different knowledge holder:

**Domain SSR — Loop 1**
The knowledge holder is the SME. The system speculates about domain meaning. The SME corrects. Codebase-specific understanding accumulates.

**Operational SSR — Loop 2**
The knowledge holder is a specialist LLM. The system speculates about how to parse a file type. The specialist corrects and produces a skill. Tool-handling capability accumulates.

The two loops never mix. Domain knowledge is codebase-specific. Operational capability is universal.

---

## 4. Validation

Two tests were run against the same five-file SCSS codebase simulating an aviation frontend. Test 1 used a parser-only skill (PostCSS). Test 2 used a hybrid skill (Dart Sass + PostCSS) produced after the sandbox environment observation surfaced a better tool choice. Both tests ran under the same SSR protocol: exit criteria declared, safety limit five loops, specialist LLM validates each loop.

---

### 4.1 Test Protocol

**Environment declaration (ATLAS-SAGE → Specialist):**
```
OS: Linux Ubuntu 24
Architecture: x86_64
Please provide a setup script that installs everything needed.
```

Two lines. Everything else — tool selection, installation, configuration, execution — was the specialist's responsibility. This is the minimal viable environment declaration. ATLAS-SAGE declares what it has. The specialist decides what to build.

**Exit criteria:**
- Specialist finds no gaps in skill or handbook
- All domain-meaningful chunks extracted and summarised correctly
- Safety limit: five loops maximum
- Beyond limit: human escalation with full loop history

**Each loop sends:**
- Every summary produced
- The source code block that produced it
- The current skill version

The specialist cannot validate a summary without seeing what produced it. The code block is the ground truth.

---

### 4.2 Test 1 — Parser Skill (PostCSS)

**Interaction 1:** ATLAS-SAGE delegated with file samples and required contract. No assumptions about SCSS included. Claude produced Skill v1.0 with parsing and summarisation instructions. Handbook v1.0 produced alongside.

**SSR Loop Results:**

| Loop | Skill | Gaps | Updates |
|---|---|---|---|
| 1 | v1.0 → v1.1 | 3 | BEM extraction added, infrastructure filter added, handbook: BEM as domain signal |
| 2 | v1.1 → v1.2 | 3 | respond-to parameter semantics, elevation level semantics, handbook: elevation levels |
| 3 | v1.2 → v1.3 | 1 | `__price` data shape signal |
| 4 | v1.3 | 0 | ✅ STABLE |

**Result:** STABLE after 4 loops. 45 nodes (v1.0) → 51 nodes (v1.1+).

**Key learning:** BEM child elements were structurally invisible in v1.0. Two of the four loops were spent on structural gaps before semantic refinement could begin.

---

### 4.3 Test 2 — Hybrid Skill (Dart Sass + PostCSS)

The sandbox test revealed that PostCSS is a parser while Dart Sass is the official compiler. Running the native compiler in a sandbox surfaces a category of signal no parser can produce: compilation health — deprecation warnings, syntax errors, upgrade debt.

The corrected Interaction 1 prompt declared only OS and architecture. The specialist independently selected the hybrid approach, produced a setup script, and delivered Skill v1.0 with both tools configured.

**SSR Loop Results:**

| Loop | Skill | Gaps | Updates |
|---|---|---|---|
| 1 | v1.0 → v1.1 | 3 | Deprecation type distinction, mixin parameter semantics, handbook: health signals |
| 2 | v1.1 → v1.2 | 1 | `__price` data shape signal |
| 3 | v1.2 | 0 | ✅ STABLE |

**Result:** STABLE after 3 loops. 56 nodes from loop 1 (BEM visible immediately).

---

### 4.4 Comparison

| Metric | PostCSS only | Hybrid |
|---|---|---|
| Loops to stable | 4 | 3 |
| Nodes in loop 1 | 45 | 56 |
| BEM visible in loop 1 | ❌ | ✅ |
| Infrastructure handled in loop 1 | ❌ | ✅ |
| Compilation health signals | ❌ | ✅ |
| Deprecation warnings surfaced | ❌ | ✅ |
| Upgrade debt visible | ❌ | ✅ |

The loop count difference (4 vs 3) understates the quality difference. The PostCSS test spent two loops fixing structural gaps. The hybrid test started structurally complete and spent all three loops on semantic refinement.

More significantly: the hybrid surfaced a category of knowledge structurally unavailable to any parser regardless of how many SSR loops run:

```
_buttons.scss  → @import deprecated (Dart Sass 3.0)
               → darken() deprecated (use color.scale)
_mixins.scss   → @import deprecated
_variables.scss → compiles cleanly
```

This codebase has upgrade debt before Dart Sass 3.0 ships. An SME session on this codebase now starts with that information. No amount of SSR loops on a pure parser would have produced it.

---

### 4.5 What the Tests Prove Together

**SSR convergence is fast.** Both tests reached stability within the five-loop safety limit. The exit criteria — not the counter — determined when to stop.

**The sandbox is not optional.** Declaring the execution environment and letting the specialist choose tools is a design constraint, not a convenience. It produced a better skill in fewer loops.

**The diff is the learning.** Every version bump is a permanent, versioned, auditable record of what was wrong and why it was fixed. The skill does not just improve — it remembers why it improved.

**IP is preserved throughout.** Every skill version — both PostCSS and hybrid — describes tool behaviour and file type patterns. Zero client codebase knowledge in any artifact. Skills produced here are safe to share across organisations and projects.

**Token efficiency compounds.** Both skills required a bounded specialist interaction (4 and 3 calls respectively). Every future codebase ATLAS-SAGE processes reuses the stable skill at zero additional specialist cost. The investment is made once and amortised across every project in the registry.

---

### 4.6 Domain SSR Validation — Sprint 4

Sections 4.1–4.5 validate **Operational SSR** (Loop 2): the system extending its own tool-handling capability through specialist LLM correction. Sprint 4 validates **Domain SSR** (Loop 1): human corrections accumulating as permanent graph knowledge.

**Test fixture:** Four-file Python order-processing application (OrderController, OrderService, IOrderRepository, Order). 90 nodes, 21 edges. Same fixture as Sprints 1–3.

**Protocol:**
- Q1: Query with no prior corrections in the graph — establish the speculative baseline
- SME correction injected: the system's inference about OrderService's transaction handling was wrong
- Q2: Same query re-run — correction surfaces before graph traversal begins

**Results:**

| Step | Observable |
|---|---|
| Q1 | No corrections found. Answer based on graph structure and LLM inference. OrderService described as managing order operations. |
| Correction | SME flagged: "OrderService uses Unit of Work pattern to execute repository operations atomically" — not visible from AST structure alone |
| Q2 | First line of answer: *"SME Correction on Record: Unit of Work pattern…atomically."* Graph traversal then grounded the correction in structural evidence |

**What this proves:**

The speculative Q1 answer was not wrong about what the code does. It was wrong about how it does it — the tacit architectural intent behind the transaction boundary. That intent is not in the AST. It is not in any comment. It exists only in the SME's understanding of the system's design.

Q1 provoked the correction. The correction was captured against a logical concept (`orderservice`) rather than a node UUID — stable across ingestion runs, independent of extraction non-determinism.

Q2 led with SME knowledge, then used the graph to ground it. This is the SSR loop closing at the domain level:

```
Speculative Q1
  → wrong in the right neighbourhood
  → SME corrects (tacit knowledge surfaces)
  → correction stored in graph

        ↓

Q2 (same query)
  → correction retrieved first
  → graph traversal follows
  → answer starts from human knowledge, not LLM inference
```

**The loop is observable, not inferred.** The shift from Q1 to Q2 is visible in the answer text, not in an evaluation metric. The system does not claim to have learned. It demonstrates it.

**Cost:** $0.52/run — the $0.11 increase over Sprint 3 ($0.41) is attributable to one additional `search_corrections` tool call per query. First quantified cost of the Domain SSR loop.

---

## 5. Implications

### 5.1 For Regulated Enterprise AI

Regulated enterprises — aviation, finance, healthcare — face a specific version of the tacit knowledge problem. Their legacy systems are old, undocumented, and critical. Their SMEs are scarce, expensive, and leaving. The knowledge walking out the door when an experienced engineer retires is not in any system.

SSR provides a mechanism to extract that knowledge systematically. Not through documentation campaigns. Not through knowledge management systems. Through provocation — let the AI be wrong, capture the correction, accumulate the understanding.

The human-gated governance model inherited from CACA ensures this is deployable in regulated contexts. Domain knowledge updates require human approval. Operational capability updates are autonomous. The distinction maps directly to EU AI Act requirements for high-risk AI systems without being designed to.

### 5.2 For Data Sovereignty

The declarative spec pattern — proven on chess.yaml, extended to RCR — runs on small local SLMs. The spec provides all reasoning context. No frontier model required.

```
compliance.yaml   → declarative spec, no client IP
Phi-3 Mini 3.8B   → runs on-premise via Ollama
                    zero cloud API calls
                    zero data egress
                    near-zero inference cost
                    auditable, explainable
```

GDPR Article 17 validation running on a local server with a 3.8B model. No data leaving the building. This is the EU AI Act compliance story. This is the German enterprise story.

The basket-agent-poc already proved this at the governance layer — Phi-3 Mini governed by Basket.SKILL.md, 6/6 BDD passing. RCR applies the same pattern to compliance rules.

### 5.2 For AI Systems Design

SSR challenges a foundational assumption of the current AI field: that hallucination is always a failure mode to be suppressed.

Hallucination is a failure mode when the system is expected to retrieve known facts. It is a feature when the system is expected to surface unknown ones. The distinction is not about the model's behaviour — it is about the context in which the model operates and the purpose the behaviour serves.

This suggests a broader design principle: **the appropriate response to AI uncertainty depends on whether the uncertainty is about retrievable facts or about tacit knowledge.** Retrieval systems should suppress uncertainty. Provocation systems should structure it.

### 5.3 For the Practitioner

SSR was not discovered by reading research papers. It was discovered by building systems, noticing what was missing, and building the next system to fill the gap. The pattern became visible only in retrospect — after Skills SME, CACA, and ATLAS-SAGE were all built and the lineage could be traced.

This is how architectural insight works in practice. Not top-down from theory. Bottom-up from accumulated failure and correction. Which is, itself, an instance of SSR.

---

## 6. Conclusion

Tacit knowledge in complex systems cannot be retrieved because it has never been stored. It can only be extracted through provocation — by presenting a plausible-but-wrong interpretation to a knowledge holder and capturing the correction.

**Structured Speculation and Reinforcement** is the formalisation of this mechanism. It is not a new technology. It is a pattern that makes deliberate use of what AI systems already do — generate confident, plausible interpretations — by anchoring those interpretations to structural truth and treating every correction as a permanent knowledge update.

The pattern was discovered across three systems over time. Skills SME identified the need for a judgment layer and the missing learning loop. CACA formalised the governance architecture and the two-loop model. ATLAS-SAGE closed the loop with the graph scaffold and the skill system that makes operational capability accumulate automatically.

ATLAS-SAGE did not supersede its predecessors. It completed them. The Skills SME — a system that could govern but not learn — became the governing intelligence inside a system whose entire purpose is learning.

The thesis is simple: **in the presence of inaccessible tacit knowledge, structured wrongness is more valuable than accurate silence.** The correction is the artifact. The accumulation of corrections is understanding.

That understanding — built one reinforced correction at a time — is what SAGE means.

---

## Appendix: System Lineage

```
Skills SME (2025)
  Purpose:    Govern AI agent behaviour
  Insight:    Judgment must be externalised
  Gap:        Learning loop missing

        ↓

CACA (2025-2026)
  Purpose:    Continuously adaptive agent governance
  Insight:    Two loops — autonomous vs human-gated
  Gap:        Loop closes session by session, not permanently

        ↓

ATLAS-SAGE (2026)
  Purpose:    Polyglot codebase intelligence
  Insight:    SSR — structured speculation + reinforcement
  Status:     Sprint 4 complete — Domain SSR loop closed
              Operational SSR: Sprints 0–2 (skill self-extension)
              Community SSR:   Sprint 3 (cross-domain query routing)
              Domain SSR:      Sprint 4 (correction capture, Q1→Q2 shift observable)
```

## Appendix: SSR Conditions Reference

| Condition | Required | If missing |
|---|---|---|
| Inaccessible tacit knowledge | Yes | Use retrieval instead |
| Articulation requires provocation | Yes | Use documentation instead |
| Correction cost is manageable | Yes | Do not use SSR |
| Correction is the target artifact | Yes | Use Q&A instead |

## Appendix: Validation Evidence

### Test 1 — PostCSS Parser Skill

| Artifact | Version | What changed | Why |
|---|---|---|---|
| SKILL-scss-postcss | v1.0 | Initial | Interaction 1 |
| SKILL-scss-postcss | v1.1 | BEM extraction, infrastructure filter | Loop 1 — structural gaps |
| SKILL-scss-postcss | v1.2 | Mixin parameter + elevation level semantics | Loop 2 — semantic gaps |
| SKILL-scss-postcss | v1.3 | Price element data shape signal | Loop 3 — depth gap |
| — | v1.3 | STABLE | Loop 4 |

Result: 4 loops. 45 → 51 nodes.

---

### Test 2 — Hybrid Skill (Dart Sass + PostCSS)

| Artifact | Version | What changed | Why |
|---|---|---|---|
| SKILL-scss-hybrid | v1.0 | Initial — hybrid approach, 56 nodes, health signals | Interaction 1 |
| SKILL-scss-hybrid | v1.1 | Deprecation type distinction, mixin/elevation semantics | Loop 1 — semantic gaps |
| SKILL-scss-hybrid | v1.2 | Price element data shape signal | Loop 2 — depth gap |
| — | v1.2 | STABLE | Loop 3 |

Result: 3 loops. 56 nodes from loop 1. Deprecation signals surfaced.

---

### Key Finding

Hybrid skill stable one loop earlier. More importantly: surfaced compilation health signals structurally unavailable to any parser. Sandbox environment declaration was the enabling design decision — ATLAS declared OS/architecture only, specialist chose tools.
