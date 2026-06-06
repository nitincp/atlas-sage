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
