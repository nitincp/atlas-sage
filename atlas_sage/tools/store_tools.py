"""store_node and vector_search_tool — LanceDB write and read operations with embedding."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..store.store import AtlasStore

if TYPE_CHECKING:
    pass

_embedder = None


def _get_embedder(model_name: str):
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(model_name)
    return _embedder


def store_node(node: dict, embed_model: str, store: AtlasStore) -> str:
    """Embed the node's summary and write it to the knowledge graph. Returns node_id."""
    summary = node.get("summary", "")
    if not summary:
        raise ValueError(f"Node {node.get('node_id')} has no summary — generate one before storing.")

    embedder = _get_embedder(embed_model)
    embedding = embedder.encode(summary, normalize_embeddings=True).tolist()
    node["embedding"] = embedding
    return store.write_node(node)


def vector_search_tool(query_text: str, embed_model: str, store: AtlasStore, limit: int = 5) -> list[dict]:
    """Embed query_text and return the top matching nodes from the knowledge graph."""
    embedder = _get_embedder(embed_model)
    query_embedding = embedder.encode(query_text, normalize_embeddings=True).tolist()
    results = store.vector_search(query_embedding, limit=limit)
    # Strip embedding vectors from results to keep context payloads compact
    for row in results:
        row.pop("embedding", None)
    return results


def graph_traverse(node_id: str, depth: int, store: AtlasStore) -> dict:
    """Follow edges outward from node_id up to depth hops. Returns nodes and edges."""
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
            edges = store.get_edges_for_node(nid)
            for edge in edges:
                visited_edges.append(edge)
                target = edge.get("target_node_id")
                if target and target not in visited_nodes:
                    next_frontier.append(target)
        frontier = next_frontier

    return {"nodes": list(visited_nodes.values()), "edges": visited_edges}
