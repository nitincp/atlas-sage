"""CLI entry points for ATLAS-SAGE.

atlas-sage ingest <file_path>
atlas-sage query  "<question>"
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="atlas-sage",
        description="ATLAS-SAGE — AST-anchored LLM Analysis System",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ingest
    ingest_p = sub.add_parser("ingest", help="Ingest a source file into the knowledge graph.")
    ingest_p.add_argument("file_path", help="Path to the source file to ingest.")

    # query
    query_p = sub.add_parser("query", help="Ask an SME question about the codebase.")
    query_p.add_argument("question", help="The question to answer.")

    args = parser.parse_args()

    # Config loaded here so env errors surface before doing any work
    from .config import Config
    config = Config()

    if args.command == "ingest":
        from .ingestion.pipeline import ingest
        text, stats = ingest(args.file_path, config)
        print(text)
        _print_stats(stats)

    elif args.command == "query":
        from .query.pipeline import query
        text, stats = query(args.question, config)
        print(text)
        _print_stats(stats)


def _print_stats(stats: dict) -> None:
    cost = stats.get("cost_usd", 0)
    in_t = stats.get("in_tokens", 0)
    out_t = stats.get("out_tokens", 0)
    itr = stats.get("iterations", 0)
    print(f"\n[cost=${cost:.6f} | in={in_t} out={out_t} | iter={itr}]")


if __name__ == "__main__":
    sys.exit(main())
