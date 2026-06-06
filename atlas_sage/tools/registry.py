"""Tool dispatch registry — maps LLM tool call names to implementations.

Context dict passed to dispatch_tool must contain:
  store: AtlasStore
  config: Config
"""

from __future__ import annotations

from typing import Any

from .executor import execute_skill
from .skill_tools import create_skill, search_skills
from .store_tools import graph_traverse, list_nodes_tool, store_edge_tool, store_node, vector_search_tool


def dispatch_tool(name: str, args: dict[str, Any], context: dict) -> Any:
    """Route a tool call by name to its implementation."""
    store = context["store"]
    config = context["config"]

    match name:
        case "search_skills":
            return search_skills(args["file_types"], store)

        case "create_skill":
            return create_skill(
                args["file_types"],
                args["sample_code"],
                config,
                store,
            )

        case "execute_skill":
            return execute_skill(args["skill_id"], args["file_path"], store)

        case "store_node":
            return store_node(args["node"], config.embed_model, store)

        case "store_edge":
            return store_edge_tool(
                args["source_node_id"],
                args["target_node_id"],
                args["edge_type"],
                args["confidence"],
                args["evidence"],
                store,
            )

        case "list_nodes":
            return list_nodes_tool(store, limit=args.get("limit", 200))

        case "vector_search":
            return vector_search_tool(
                args["query_text"],
                config.embed_model,
                store,
                limit=args.get("limit", 5),
            )

        case "graph_traverse":
            return graph_traverse(
                args["node_id"],
                args.get("depth", 2),
                store,
                direction=args.get("direction", "outbound"),
            )

        case _:
            raise ValueError(f"Unknown tool: {name}")
