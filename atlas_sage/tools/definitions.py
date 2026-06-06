"""OpenAI-format tool definitions for the LLM orchestrator.

These are the tools the orchestrator LLM can call. Definitions are data only —
no logic lives here.
"""

from __future__ import annotations

INGESTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_skills",
            "description": (
                "Search the skill registry for existing skills that cover the given file types. "
                "Always call this before create_skill. Returns a list of matching skill objects."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File type identifiers to search for, e.g. ['csharp', '.cs']",
                    }
                },
                "required": ["file_types"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_skill",
            "description": (
                "Ask the specialist LLM to create a new parsing skill for the given file types. "
                "Pass a representative sample of the raw file content (code structure only — "
                "no client context, no domain meaning). Returns the created skill object."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File types the skill must cover, e.g. ['csharp', '.cs']",
                    },
                    "sample_code": {
                        "type": "string",
                        "description": "A short sample of the raw file to parse (syntax only, no client context).",
                    },
                },
                "required": ["file_types", "sample_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_skill",
            "description": (
                "Run the skill's extraction script against the given file. "
                "Returns a list of raw nodes in tool contract format. "
                "Nodes will not yet have summaries — you must generate and add those before storing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_id": {
                        "type": "string",
                        "description": "ID of the skill to execute.",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the source file to parse.",
                    },
                },
                "required": ["skill_id", "file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "store_node",
            "description": (
                "Embed the node's summary and write it to the knowledge graph. "
                "You MUST populate the 'summary' field before calling this — "
                "write a domain summary covering: Domain Purpose, Logic Flow, Inferred Constraints. "
                "Any edges in the node's 'edges' list are automatically persisted."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "node": {
                        "type": "object",
                        "description": (
                            "Node in tool contract format. Required fields: node_id, language, "
                            "source_file, chunk_type, raw_cleaned, summary. "
                            "Optional: edges (list of edge objects with type, target_node_id, confidence, evidence)."
                        ),
                    }
                },
                "required": ["node"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "store_edge",
            "description": (
                "Store a directed edge between two already-stored nodes. "
                "Use this for cross-file edges (CALLS, IMPLEMENTS, INHERITS, INJECTS) "
                "inferred after all nodes from multiple files have been stored."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source_node_id": {"type": "string", "description": "node_id of the calling/dependent node."},
                    "target_node_id": {"type": "string", "description": "node_id of the called/dependency node."},
                    "edge_type": {
                        "type": "string",
                        "enum": ["CALLS", "IMPLEMENTS", "INHERITS", "INJECTS", "IMPORTS", "USES", "RETURNS"],
                        "description": "Semantic relationship type.",
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["deterministic", "probabilistic", "inferred"],
                        "description": "Certainty level: deterministic, probabilistic, or inferred.",
                    },
                    "evidence": {
                        "type": "string",
                        "description": "Short explanation of why this edge exists (e.g. 'CatalogService.GetItems() called in BasketController').",  # noqa: E501
                    },
                },
                "required": ["source_node_id", "target_node_id", "edge_type", "confidence", "evidence"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_nodes",
            "description": (
                "Return all nodes currently in the knowledge graph (summary + metadata, no embeddings). "
                "Use this after ingesting multiple files to discover node IDs for cross-file edge inference."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum nodes to return (default 200).",
                        "default": 200,
                    }
                },
                "required": [],
            },
        },
    },
]

COMMUNITY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "detect_communities",
            "description": (
                "Run Louvain community detection on the knowledge graph edges. "
                "Returns community groups with member_node_ids and member_summaries "
                "(truncated per-node summaries). "
                "You must generate a domain-level summary for each group, then call store_community."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "store_community",
            "description": (
                "Embed the community summary and write the community to the knowledge graph. "
                "Provide a domain-level summary synthesising what the group collectively does. "
                "community_id and member_node_ids must come from detect_communities."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "community_id": {
                        "type": "string",
                        "description": "Exact community_id from detect_communities.",
                    },
                    "level": {
                        "type": "integer",
                        "description": "Hierarchy level: 0=project, 1=module/namespace, 2=class.",
                    },
                    "member_node_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Node IDs in this community (from detect_communities).",
                    },
                    "summary": {
                        "type": "string",
                        "description": (
                            "Domain-level summary you generated. Must cover: "
                            "Domain Scope, Key Components, Domain Responsibilities, "
                            "and how this community connects to others."
                        ),
                    },
                },
                "required": ["community_id", "level", "member_node_ids", "summary"],
            },
        },
    },
]

QUERY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "vector_search",
            "description": (
                "Embed the query text and search the knowledge graph for semantically similar nodes. "
                "Returns the top matching nodes with their summaries and source locations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query_text": {
                        "type": "string",
                        "description": "The question or search phrase to embed and search with.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of nodes to return (default 5).",
                        "default": 5,
                    },
                },
                "required": ["query_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "graph_traverse",
            "description": (
                "Follow AST edges from a node to gather related context. "
                "Returns nodes and edges up to the specified depth. "
                "Use direction='inbound' for blast-radius / impact queries (who depends on this?). "
                "Use direction='outbound' (default) for dependency queries (what does this depend on?). "
                "Use direction='both' for full neighbourhood context."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Starting node ID.",
                    },
                    "depth": {
                        "type": "integer",
                        "description": (
                            "How many hops to traverse. "
                            "1 = immediate neighbours; 2 = two hops (default); 3 = blast radius. "
                            "For narrow lookups use 1; architectural/cross-cutting use 2; impact analysis use 3."
                        ),
                        "default": 2,
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["outbound", "inbound", "both"],
                        "description": (
                            "Edge direction to follow. "
                            "'outbound': what does this node call/depend on. "
                            "'inbound': what depends on / calls this node (blast radius). "
                            "'both': full neighbourhood."
                        ),
                        "default": "outbound",
                    },
                },
                "required": ["node_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_communities",
            "description": (
                "Search community summaries for cross-domain or high-level questions. "
                "Use this FIRST when the question asks about a domain, module, system, or "
                "high-level capability (e.g. 'what does the X domain do?', "
                "'how does the payment system work?', 'summarise the order module'). "
                "Community summaries answer these at a higher level of abstraction than individual nodes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query_text": {
                        "type": "string",
                        "description": "The high-level question or domain term to search with.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum communities to return (default 3).",
                        "default": 3,
                    },
                },
                "required": ["query_text"],
            },
        },
    },
]
