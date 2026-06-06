"""store_node, store_edge, vector_search_tool, graph_traverse, list_nodes_tool."""

from __future__ import annotations

import uuid

import litellm

from ..store.store import AtlasStore


def _embed(text: str, model: str) -> list[float]:
    """Embed text via LiteLLM — works with any provider that has an embedding API."""
    response = litellm.embedding(model=model, input=[text])
    return response.data[0]["embedding"]


def store_node(node: dict, embed_model: str, store: AtlasStore) -> dict:
    """Embed the node's summary, write it to the knowledge graph, and persist its edges.

    Returns {"node_id": ..., "edges_stored": N}.
    """
    summary = node.get("summary", "")
    if not summary:
        raise ValueError(f"Node {node.get('node_id')} has no summary — generate one before storing.")

    embedding = _embed(summary, embed_model)
    node["embedding"] = embedding
    node_id = store.write_node(node)

    edges_stored = 0
    for edge in node.get("edges", []):
        target = edge.get("target_node_id")
        if target:
            store.write_edge({
                "edge_id": str(uuid.uuid4()),
                "source_node_id": node_id,
                "target_node_id": target,
                "type": edge.get("type", "UNKNOWN"),
                "confidence": edge.get("confidence", "inferred"),
                "evidence": edge.get("evidence", ""),
            })
            edges_stored += 1

    return {"node_id": node_id, "edges_stored": edges_stored}


def store_edge_tool(
    source_node_id: str,
    target_node_id: str,
    edge_type: str,
    confidence: str,
    evidence: str,
    store: AtlasStore,
) -> dict:
    """Store a directed edge between two existing nodes. Returns the edge_id."""
    valid_confidence = {"deterministic", "probabilistic", "inferred"}
    if confidence not in valid_confidence:
        confidence = "inferred"
    edge_id = store.write_edge({
        "edge_id": str(uuid.uuid4()),
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "type": edge_type,
        "confidence": confidence,
        "evidence": evidence,
    })
    return {"edge_id": edge_id, "stored": True}


def vector_search_tool(query_text: str, embed_model: str, store: AtlasStore, limit: int = 5) -> list[dict]:
    """Embed query_text and return the top matching nodes from the knowledge graph."""
    query_embedding = _embed(query_text, embed_model)
    results = store.vector_search(query_embedding, limit=limit)
    # Strip embedding vectors from results to keep context payloads compact
    for row in results:
        row.pop("embedding", None)
    return results


def graph_traverse(node_id: str, depth: int, store: AtlasStore, direction: str = "outbound") -> dict:
    """Follow edges from node_id up to depth hops.

    direction:
      "outbound"  — follow edges where node is source (what does this node depend on / call?)
      "inbound"   — follow edges where node is target (what depends on / calls this node? — blast radius)
      "both"      — follow edges in both directions
    """
    visited_nodes: dict[str, dict] = {}
    visited_edges: list[dict] = []
    frontier = [node_id]

    for _ in range(depth):
        next_frontier = []
        for nid in frontier:
            if nid in visited_nodes:
                continue
            node = store.get_node(nid)
            if node:
                node.pop("embedding", None)
                visited_nodes[nid] = node

            edges: list[dict] = []
            if direction in ("outbound", "both"):
                edges.extend(store.get_edges_for_node(nid))
            if direction in ("inbound", "both"):
                edges.extend(store.get_incoming_edges(nid))

            for edge in edges:
                visited_edges.append(edge)
                # Traverse toward the neighbour node regardless of direction
                neighbour = (
                    edge.get("target_node_id")
                    if direction in ("outbound", "both")
                    else edge.get("source_node_id")
                )
                if direction == "both":
                    src, tgt = edge.get("source_node_id"), edge.get("target_node_id")
                    neighbour = tgt if src == nid else src
                if neighbour and neighbour not in visited_nodes:
                    next_frontier.append(neighbour)

        frontier = next_frontier

    return {"nodes": list(visited_nodes.values()), "edges": visited_edges}


def list_nodes_tool(store: AtlasStore, limit: int = 200) -> list[dict]:
    """Return all stored nodes (summary + metadata, no embeddings). Used for cross-file edge inference."""
    return store.list_nodes(limit=limit)


def detect_communities_tool(store: AtlasStore) -> list[dict]:
    """Run Louvain community detection on the edge graph.

    Returns community groups with member_node_ids and truncated member_summaries
    so the orchestrator can generate domain summaries without extra round-trips.
    """
    import uuid

    import networkx as nx
    from networkx.algorithms.community import louvain_communities

    nodes = store.list_nodes(limit=1000)
    edges = store.get_all_edges()
    node_map = {n["node_id"]: n for n in nodes}

    G = nx.Graph()
    for n in nodes:
        G.add_node(n["node_id"])
    for edge in edges:
        src, tgt = edge["source_node_id"], edge["target_node_id"]
        if src in node_map and tgt in node_map:
            G.add_edge(src, tgt)

    if G.number_of_edges() == 0:
        raw_groups = [{nid} for nid in G.nodes()]
    else:
        raw_groups = louvain_communities(G, seed=42)

    result = []
    for group in raw_groups:
        member_ids = list(group)
        community_id = str(uuid.uuid4())
        member_summaries = [
            {
                "node_id": nid,
                "source_file": node_map[nid].get("source_file", ""),
                "chunk_type": node_map[nid].get("chunk_type", ""),
                "summary": (node_map[nid].get("summary") or "")[:400],
            }
            for nid in member_ids
            if nid in node_map
        ]
        result.append({
            "community_id": community_id,
            "level": 0,
            "member_node_ids": member_ids,
            "member_summaries": member_summaries,
        })

    return result


def store_community_tool(community: dict, embed_model: str, store: AtlasStore) -> dict:
    """Embed community summary and write to communities table. Updates member nodes' community_id."""
    summary = community.get("summary", "")
    if not summary:
        raise ValueError("Community must have a 'summary' before storing.")
    embedding = _embed(summary, embed_model)
    community["embedding"] = embedding
    community_id = store.write_community(community)
    for node_id in community.get("member_node_ids", []):
        try:
            store.update_node_community(node_id, community_id)
        except Exception:
            pass
    return {"community_id": community_id, "members": len(community.get("member_node_ids", []))}


def search_communities_tool(query_text: str, embed_model: str, store: AtlasStore, limit: int = 3) -> list[dict]:
    """Embed query_text and return the top matching community summaries."""
    embedding = _embed(query_text, embed_model)
    results = store.vector_search_communities(embedding, limit=limit)
    for row in results:
        row.pop("embedding", None)
    return results


def capture_correction_tool(
    target_type: str,
    target_id: str,
    original: str,
    corrected: str,
    session_id: str,
    store: AtlasStore,
) -> dict:
    """Capture an SME correction against a node, edge, or community.

    target_type: 'node' | 'edge' | 'community'
    target_id:   the node_id / edge_id / community_id being corrected
    original:    what the system said (quoted from the answer)
    corrected:   what the SME says is actually true
    session_id:  query session identifier (pass the current session id)

    Returns {"correction_id": ..., "stored": True}
    """
    correction_id = str(uuid.uuid4())
    store.write_correction({
        "correction_id": correction_id,
        "session_id": session_id,
        "target_type": target_type,
        "target_id": target_id,
        "original": original,
        "corrected": corrected,
    })
    return {"correction_id": correction_id, "stored": True}


def get_corrections_tool(target_id: str, store: AtlasStore) -> list[dict]:
    """Return all SME corrections previously captured for a node, edge, or community.

    Call this before answering about any specific node to check whether the SME
    has already corrected the system's inference about it.
    """
    return store.get_corrections(target_id)


def search_corrections_tool(query_text: str, store: AtlasStore) -> list[dict]:
    """Search all stored SME corrections for relevance to the current question.

    Call this ONCE at the start of every query, before vector_search.
    Returns corrections whose original, corrected, or target_id text overlaps
    with the query. If results exist, they represent authoritative SME knowledge
    that must take precedence over anything inferred from the graph.
    """
    all_corrections = store.get_all_corrections()
    if not all_corrections:
        return []
    query_words = {w for w in query_text.lower().split() if len(w) > 2}
    results = []
    for c in all_corrections:
        searchable = " ".join([
            c.get("original", ""),
            c.get("corrected", ""),
            c.get("target_id", ""),
        ]).lower()
        if any(w in searchable for w in query_words):
            results.append(c)
    return results
