"""Community detection and summarisation pipeline.

The LLM orchestrator calls detect_communities (Louvain on the edge graph),
reads the returned member summaries, generates a domain-level summary for each
community, and calls store_community to embed and persist it.
"""

from __future__ import annotations

from ..config import Config
from ..orchestrator import run_agent
from ..store.store import AtlasStore
from ..tools.definitions import COMMUNITY_TOOLS

_COMMUNITY_SYSTEM = """\
You are the ATLAS-SAGE community summarisation agent. Your job is to organise the
knowledge graph into meaningful domain communities and generate rich summaries for each.

Process:
1. Call detect_communities — this runs Louvain community detection on the graph edges
   and returns groups of related nodes with their summaries.
2. For each community group, read the member_summaries carefully.
   Then generate a domain-level summary covering:
   - Domain Scope: what does this group collectively handle? (one sentence)
   - Key Components: the most significant classes, interfaces, or functions
   - Domain Responsibilities: what business or technical problems does this community solve?
   - Connections: how does this community relate to or depend on the other communities?
3. Call store_community for each group, passing:
   - community_id (exact value from detect_communities)
   - level (0 for project-level groups; 1 if a group is clearly a sub-module)
   - member_node_ids (exact list from detect_communities)
   - summary (the domain-level text you just generated)
4. After all communities are stored, report: how many communities were detected,
   what each covers in one sentence, and the total member node count.

Constraints:
- Use the exact community_id and member_node_ids returned by detect_communities — never guess.
- Every community must have a summary before you call store_community.
- Community summaries answer "what does the X domain/module do?" — they must be at a
  higher level of abstraction than individual node summaries.
- If there is only one community (all nodes in one group), still summarise it — it becomes
  the project-level summary that answers cross-cutting domain queries.

Be confident. A clear, wrong domain hypothesis is more valuable than a vague hedge.
"""


def build_communities(config: Config) -> tuple[str, dict]:
    """Detect communities in the knowledge graph and generate LLM summaries for each.

    Returns (report, stats). Must be called after ingestion — requires nodes and edges
    to already be stored in the graph.
    """
    store = AtlasStore(config.lancedb_path)
    context = {"store": store, "config": config}

    text, stats = run_agent(
        system_prompt=_COMMUNITY_SYSTEM,
        user_message=(
            "Detect communities in the knowledge graph and generate a domain summary for each."
        ),
        tools=COMMUNITY_TOOLS,
        config=config,
        context=context,
        max_iterations=30,
    )
    return text, stats
