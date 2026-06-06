"""Read path — answer SME questions using the ATLAS-SAGE knowledge graph."""

from __future__ import annotations

from ..config import Config
from ..orchestrator import run_agent
from ..store.store import AtlasStore
from ..tools.definitions import QUERY_TOOLS

_QUERY_SYSTEM = """\
You are the ATLAS-SAGE query engine (SAGE). Answer questions about a codebase using the knowledge graph.

IMPORTANT: ALWAYS call vector_search first — never ask for clarification before searching.
The knowledge graph may contain the answer even if the question seems vague. Search first, then answer.

Process:
1. ALWAYS call vector_search with the question (or key terms from it) to retrieve semantically relevant nodes.
2. If the question is architectural or cross-cutting, call graph_traverse on the most relevant
   node to gather connected context.
3. Assemble context from the returned nodes and edges.
4. Provide a confident, structured answer anchored to the graph:
   - Reference specific files and chunk types
   - State what you can determine with certainty vs. what you are inferring
   - Flag any gaps where the graph does not have enough information

You practice Structured Speculation: generate a confident interpretation anchored to real
graph structure. If you are wrong, that is valuable — it will provoke the SME to correct you,
and that correction is the primary knowledge artifact this system harvests.

Never hedge to the point of uselessness. A confident wrong answer is more valuable than a
correct silence when documentation does not exist.
"""


def query(question: str, config: Config) -> str:
    """Answer an SME question using the knowledge graph. Returns the answer text."""
    store = AtlasStore(config.lancedb_path)
    context = {"store": store, "config": config}

    answer = run_agent(
        system_prompt=_QUERY_SYSTEM,
        user_message=question,
        tools=QUERY_TOOLS,
        config=config,
        context=context,
    )
    return f"[model: {config.orchestrator_model}]\n{answer}"
