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
                "write a domain summary covering: Domain Purpose, Logic Flow, Inferred Constraints."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "node": {
                        "type": "object",
                        "description": (
                            "Node in tool contract format. Required fields: node_id, language, "
                            "source_file, chunk_type, raw_cleaned, summary. "
                            "Optional: edges (list of edge objects with type, target_node_id, confidence)."
                        ),
                    }
                },
                "required": ["node"],
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
                "Follow AST edges from a node outward to gather related context. "
                "Returns nodes and edges up to the specified depth."
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
                        "description": "How many hops to traverse (default 2).",
                        "default": 2,
                    },
                },
                "required": ["node_id"],
            },
        },
    },
]
