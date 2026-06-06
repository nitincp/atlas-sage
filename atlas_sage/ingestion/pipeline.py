"""Write path — ingest source files into the ATLAS-SAGE knowledge graph.

The LLM orchestrator owns all decisions: skill discovery, skill creation,
extraction, summarisation, and storage. No logic here substitutes for LLM judgment.
"""

from __future__ import annotations

import glob
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


def ingest(file_path: str, config: Config) -> tuple[str, dict]:
    """Ingest a single source file. Returns (report, stats)."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Source file not found: {file_path}")

    store = AtlasStore(config.lancedb_path)
    context = {"store": store, "config": config}

    ext = os.path.splitext(file_path)[1].lstrip(".")
    language_hint = _EXT_LANGUAGE.get(ext, ext)

    with open(file_path, encoding="utf-8") as fh:
        sample = fh.read(3000)

    user_message = (
        f"Ingest this file into the knowledge graph.\n\n"
        f"File: {file_path}\n"
        f"Language/type: {language_hint} (.{ext})\n"
        f"File type identifiers to use when searching/creating skills: ['{language_hint}', '.{ext}']\n\n"
        f"Sample (first 3000 chars, for skill creation only if needed):\n```\n{sample}\n```"
    )

    text, stats = run_agent(
        system_prompt=_INGESTION_SYSTEM,
        user_message=user_message,
        tools=INGESTION_TOOLS,
        config=config,
        context=context,
    )
    return f"[model: {config.orchestrator_model}]\n{text}", stats


_CROSS_FILE_SYSTEM = """\
You are the ATLAS-SAGE cross-file edge inference engine. Multiple source files have just been
ingested into the knowledge graph. Your job is to discover and store edges BETWEEN nodes from
different files.

Process:
1. Call list_nodes to retrieve all stored nodes and their summaries.
2. Reason over the nodes to identify cross-file structural relationships:
   - CALLS: method/function in file A calls method/function in file B
   - IMPLEMENTS: class in file A implements interface/abstract class in file B
   - INHERITS: class in file A inherits from class in file B
   - INJECTS: constructor parameter in file A is typed as class/interface in file B (DI)
   - IMPORTS: file A imports a type declared in file B
3. For each inferred relationship, call store_edge with:
   - source_node_id: the node doing the calling/implementing/inheriting/injecting
   - target_node_id: the node being called/implemented/inherited/injected
   - edge_type: one of CALLS, IMPLEMENTS, INHERITS, INJECTS, IMPORTS
   - confidence: "deterministic" if provable from type names, "probabilistic" if strongly implied, "inferred" otherwise
   - evidence: a short explanation (e.g. "OrderController injects IOrderService via constructor")
4. Report: how many cross-file edges were stored, by type and confidence.

Constraints:
- Only create edges between nodes that actually exist in the list_nodes results.
- Use the node_id values exactly as returned — do not guess or construct them.
- Prefer fewer, high-confidence edges over many speculative ones.
- Skills contain zero domain knowledge — your edge inferences come from structural patterns only.
"""

_MULTI_FILE_INGESTION_SYSTEM = """\
You are the ATLAS-SAGE ingestion orchestrator. Your job is to ingest multiple source files
into the knowledge graph.

For each file in the list provided:
1. Call search_skills with the file's language/type identifiers to check for an existing skill.
2. If no skill exists, call create_skill with the file types and a short sample of the raw code
   (syntax only — no client context, no domain meaning). The same skill can be reused for all
   files of the same type — you only need to create it once.
3. Call execute_skill with the skill_id and the file path. This extracts raw nodes.
4. For each raw node returned, generate a domain summary covering:
   - Domain Purpose: what this code element does in an application context
   - Logic Flow: how it works step by step
   - Inferred Constraints: business rules or invariants you can infer from the structure
   Then call store_node with the node including your generated summary.

After ALL files have been processed and their nodes stored:
5. Call list_nodes to see all stored nodes and their summaries.
6. Reason about cross-file structural relationships. Edge types to consider:
   - IMPORTS: file/module A imports a name declared in file B (deterministic — provable from import statements)
   - INHERITS: class A extends/inherits from class B defined in another file (deterministic)
   - IMPLEMENTS: class A implements an interface/abstract class B from another file (deterministic)
   - CALLS: function/method in file A calls a function/method whose node is in file B (probabilistic)
   - INJECTS: constructor/initialiser in file A declares a parameter typed as class/interface B
     from another file (deterministic)
7. For each relationship, call store_edge with:
   - source_node_id / target_node_id: exact IDs from list_nodes — never guessed
   - edge_type: one of the types above
   - confidence: "deterministic" for import/inherit/implement/inject, "probabilistic" for calls,
     "inferred" if uncertain
   - evidence: one sentence explaining the structural evidence
     (e.g. "OrderService.__init__ takes IOrderRepository parameter")
8. Report: files ingested, nodes stored, cross-file edges created (count by type and confidence).

Constraints:
- Only create edges between nodes that appear in the list_nodes results.
- Use exact node_id values — never construct or guess them.
- Prefer fewer, higher-confidence edges over many speculative ones.
- Skills contain zero domain knowledge — edges come from structural patterns only.

Be confident in your summaries and edges. Anchored structure is more valuable than silence.
"""


def ingest_directory(
    dir_path: str,
    config: Config,
    pattern: str = "**/*.cs",
) -> tuple[str, dict]:
    """Ingest all matching files in a directory. Returns (report, stats).

    The orchestrator processes all files in a single agentic run so it can infer
    cross-file edges after all nodes are stored.
    """
    if not os.path.isdir(dir_path):
        raise NotADirectoryError(f"Not a directory: {dir_path}")

    files = sorted(glob.glob(os.path.join(dir_path, pattern), recursive=True))
    if not files:
        return f"No files matched pattern '{pattern}' in {dir_path}", {}

    store = AtlasStore(config.lancedb_path)
    context = {"store": store, "config": config}

    file_list = "\n".join(f"  - {f}" for f in files)
    ext = pattern.lstrip("*").lstrip(".").split(".")[-1]
    language_hint = _EXT_LANGUAGE.get(ext, ext)

    with open(files[0], encoding="utf-8") as fh:
        sample = fh.read(2000)

    user_message = (
        f"Ingest the following {len(files)} {language_hint} file(s) into the knowledge graph.\n\n"
        f"Files to ingest:\n{file_list}\n\n"
        f"Language/type: {language_hint} (.{ext})\n"
        f"File type identifiers: ['{language_hint}', '.{ext}']\n\n"
        f"Sample from first file (for skill creation if needed):\n```\n{sample}\n```"
    )

    text, stats = run_agent(
        system_prompt=_MULTI_FILE_INGESTION_SYSTEM,
        user_message=user_message,
        tools=INGESTION_TOOLS,
        config=config,
        context=context,
        max_iterations=50,
    )
    return f"[model: {config.orchestrator_model}]\n{text}", stats


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
