"""Write path — ingest a source file into the ATLAS-SAGE knowledge graph.

The LLM orchestrator owns all decisions: skill discovery, skill creation,
extraction, summarisation, and storage. No logic here substitutes for LLM judgment.
"""

from __future__ import annotations

import os

from ..config import Config
from ..orchestrator import run_agent
from ..store.store import AtlasStore
from ..tools.definitions import INGESTION_TOOLS

_INGESTION_SYSTEM = """\
You are the ATLAS-SAGE ingestion orchestrator. Your job is to ingest a source file into the knowledge graph.

Follow this process precisely:

1. Call search_skills with the file's language/type identifiers to check for an existing skill.
2. If no skill exists, call create_skill with the file types and a short sample of the raw code
   (syntax only — no client context, no domain meaning). This preserves the IP boundary.
3. Call execute_skill with the returned skill_id and the file path. This extracts raw nodes.
4. For each raw node returned, generate a domain summary covering:
   - Domain Purpose: what this code element does in an application context
   - Logic Flow: how it works step by step
   - Inferred Constraints: business rules or invariants you can infer from the structure
   Then call store_node with the node including your generated summary.
5. When all nodes are stored, report what was ingested: file, skill used, node count, chunk types seen.

Be confident in your summaries. Anchor them to the real structure you see. Wrong in the right
neighbourhood is more valuable than a correct silence in a zero-documentation codebase.
"""


def ingest(file_path: str, config: Config) -> str:
    """Ingest a single source file. Returns the orchestrator's ingestion report."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Source file not found: {file_path}")

    store = AtlasStore(config.lancedb_path)
    context = {"store": store, "config": config}

    ext = os.path.splitext(file_path)[1].lstrip(".")
    language_hint = _EXT_LANGUAGE.get(ext, ext)

    # Read a small sample for skill creation (if needed) — syntax only, no client context
    with open(file_path, encoding="utf-8") as fh:
        sample = fh.read(3000)

    user_message = (
        f"Ingest this file into the knowledge graph.\n\n"
        f"File: {file_path}\n"
        f"Language/type: {language_hint} (.{ext})\n"
        f"File type identifiers to use when searching/creating skills: ['{language_hint}', '.{ext}']\n\n"
        f"Sample (first 3000 chars, for skill creation only if needed):\n```\n{sample}\n```"
    )

    return run_agent(
        system_prompt=_INGESTION_SYSTEM,
        user_message=user_message,
        tier=2,
        tools=INGESTION_TOOLS,
        config=config,
        context=context,
    )


_EXT_LANGUAGE = {
    "cs": "csharp",
    "ts": "typescript",
    "tsx": "typescript",
    "js": "javascript",
    "jsx": "javascript",
    "py": "python",
    "html": "html",
    "css": "css",
    "scss": "scss",
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "proto": "protobuf",
}
