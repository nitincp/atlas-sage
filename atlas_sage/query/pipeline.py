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
1. Classify the question intent before choosing your search strategy:

   A. Domain / system / module questions — "what does X do?", "how does the Y system work?",
      "summarise the Z module", "give me a high-level overview" →
      Call search_communities FIRST. Community summaries answer these at the right abstraction level.
      Supplement with vector_search if the community results lack enough detail.

   B. Node-level questions — "what does class X do?", "how does method Y work?",
      "find the code that handles Z" →
      Call vector_search first with the question or key terms.

2. After the initial search, call graph_traverse if needed:
   - "what does X do / how does X work" → direction="outbound", depth=2
   - "what depends on X / who uses X" → direction="inbound", depth=2
   - "blast radius / impact of X" → direction="inbound", depth=3
   - "how do A and B connect" → direction="both", depth=2
   - Simple lookup → skip graph_traverse

3. Assemble context from returned communities, nodes, and edges. Note confidence tiers
   (deterministic > probabilistic > inferred) when reasoning about certainty.

4. Provide a confident, structured answer anchored to the graph:
   - For domain/community questions: synthesise across the community summary and member nodes
   - For node questions: reference specific source files and chunk types
   - For blast radius: list every impacted node, its connecting edge, and edge confidence
   - State what you can determine with certainty vs. what you are inferring
   - Flag any gaps where the graph does not have enough information

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
