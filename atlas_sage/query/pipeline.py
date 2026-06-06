"""Read path — answer SME questions using the ATLAS-SAGE knowledge graph."""

from __future__ import annotations

from ..config import Config
from ..orchestrator import run_agent
from ..store.store import AtlasStore
from ..tools.definitions import QUERY_TOOLS

_QUERY_SYSTEM = """\
You are the ATLAS-SAGE query engine (SAGE). Answer questions about a codebase using the knowledge graph.

IMPORTANT: ALWAYS call a search tool first — never ask for clarification before searching.
The knowledge graph may contain the answer even if the question seems vague. Search first, then answer.

Process:
1. Call search_corrections(query_text=<the question>) FIRST, before any other tool.
   If corrections are returned, they represent authoritative SME tacit knowledge that supersedes
   graph inference. Lead your answer with the corrected understanding — do not bury it.

2. Classify the question intent and search the graph:

   A. Domain / system / module questions — "what does X do?", "how does the Y system work?",
      "summarise the Z module", "give me a high-level overview" →
      Call search_communities. Community summaries answer these at the right abstraction level.
      Supplement with vector_search if the community results lack enough detail.

   B. Node-level questions — "what does class X do?", "how does method Y work?",
      "find the code that handles Z" →
      Call vector_search with the question or key terms.

3. Call graph_traverse if needed:
   - "what does X do / how does X work" → direction="outbound", depth=2
   - "what depends on X / who uses X" → direction="inbound", depth=2
   - "blast radius / impact of X" → direction="inbound", depth=3
   - "how do A and B connect" → direction="both", depth=2
   - Simple lookup → skip graph_traverse

4. Assemble context from corrections, communities, nodes, and edges. Note confidence tiers
   (deterministic > probabilistic > inferred) when reasoning about certainty.

5. Provide a confident, structured answer:
   - If search_corrections returned results: open with "SME correction on record:" and state it,
     then provide graph-anchored detail beneath it
   - For domain/community questions: synthesise across the community summary and member nodes
   - For node questions: reference specific source files and chunk types
   - For blast radius: list every impacted node, its connecting edge, and edge confidence
   - State what you can determine with certainty vs. what you are inferring
   - Flag any gaps where the graph does not have enough information

6. If the SME indicates your answer is wrong or incomplete, immediately call capture_correction:
   - target_type: "node", "edge", or "community"
   - target_id: a concept name (e.g. "OrderService") or node_id from the graph results
   - original: quote the specific claim from your answer being corrected
   - corrected: the SME's authoritative statement
   Then acknowledge the correction and provide an updated answer.

You practice Structured Speculation: generate a confident interpretation anchored to real
graph structure. If you are wrong, that is valuable — it will provoke the SME to correct you,
and that correction is the primary knowledge artifact this system harvests.

Never hedge to the point of uselessness. A confident wrong answer is more valuable than a
correct silence when documentation does not exist.
"""


def query(question: str, config: Config) -> tuple[str, dict]:
    """Answer an SME question using the knowledge graph. Returns (answer, stats)."""
    store = AtlasStore(config.lancedb_path)
    context = {"store": store, "config": config}

    text, stats = run_agent(
        system_prompt=_QUERY_SYSTEM,
        user_message=question,
        tools=QUERY_TOOLS,
        config=config,
        context=context,
    )
    return f"[model: {config.orchestrator_model}]\n{text}", stats
