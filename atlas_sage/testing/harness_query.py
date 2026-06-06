"""Query the test harness run_log.json without traversing individual run directories.

Usage:
    python -m atlas_sage.testing.harness_query [options]

Examples:
    # All runs
    python -m atlas_sage.testing.harness_query

    # Only passing sprint1 runs
    python -m atlas_sage.testing.harness_query --sprint sprint1 --passed

    # Aggregate cost + tokens by prompt version
    python -m atlas_sage.testing.harness_query --aggregate prompt_version

    # Runs with a specific model
    python -m atlas_sage.testing.harness_query --model claude-haiku

    # Output as JSON (pipe-friendly)
    python -m atlas_sage.testing.harness_query --sprint sprint1 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.parent
RUN_LOG_PATH = _PROJECT_ROOT / "test_harness" / "run_log.json"


def _load() -> list[dict]:
    if not RUN_LOG_PATH.exists():
        return []
    return json.loads(RUN_LOG_PATH.read_text(encoding="utf-8"))


def _filter(entries: list[dict], args: argparse.Namespace) -> list[dict]:
    if args.sprint:
        entries = [e for e in entries if e.get("sprint") == args.sprint]
    if args.prompt:
        entries = [e for e in entries if e.get("prompt_version") == args.prompt]
    if args.suite:
        entries = [e for e in entries if e.get("suite_version", "").startswith(args.suite)]
    if args.model:
        entries = [e for e in entries if args.model in (e.get("orchestrator_model") or "")]
    if args.passed:
        entries = [e for e in entries if e.get("passed") is True]
    if args.failed:
        entries = [e for e in entries if e.get("passed") is False]
    return entries


def _aggregate(entries: list[dict], key: str) -> list[dict]:
    groups: dict[str, dict] = {}
    for e in entries:
        gk = e.get(key, "unknown")
        if gk not in groups:
            groups[gk] = {key: gk, "runs": 0, "passed": 0, "failed": 0,
                          "cost_usd": 0.0, "in_tokens": 0, "out_tokens": 0,
                          "total_nodes": 0, "total_edges": 0}
        g = groups[gk]
        g["runs"] += 1
        g["passed"] += 1 if e.get("passed") else 0
        g["failed"] += 1 if not e.get("passed") else 0
        g["cost_usd"] = round(g["cost_usd"] + e.get("cost_usd", 0), 6)
        g["in_tokens"] += e.get("in_tokens", 0)
        g["out_tokens"] += e.get("out_tokens", 0)
        g["total_nodes"] += e.get("nodes", 0)
        g["total_edges"] += e.get("edges", 0)
    return list(groups.values())


def _table(rows: list[dict], cols: list[str]) -> None:
    if not rows:
        print("(no results)")
        return
    widths = {c: max(len(c), max(len(str(r.get(c, "-"))) for r in rows)) for c in cols}
    sep = "+-" + "-+-".join("-" * widths[c] for c in cols) + "-+"
    header = "| " + " | ".join(c.ljust(widths[c]) for c in cols) + " |"
    print(sep)
    print(header)
    print(sep)
    for r in rows:
        print("| " + " | ".join(str(r.get(c, "-")).ljust(widths[c]) for c in cols) + " |")
    print(sep)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query test harness run_log.json")
    parser.add_argument("--sprint", help="Filter by sprint name")
    parser.add_argument("--prompt", help="Filter by prompt version (e.g. v001)")
    parser.add_argument("--suite", help="Filter by suite name prefix")
    parser.add_argument("--model", help="Filter by orchestrator model substring")
    parser.add_argument("--passed", action="store_true", help="Only passing runs")
    parser.add_argument("--failed", action="store_true", help="Only failing runs")
    parser.add_argument("--aggregate", metavar="KEY",
                        help="Aggregate by field (e.g. prompt_version, sprint, orchestrator_model)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    entries = _load()
    if not entries:
        print("No runs found in run_log.json", file=sys.stderr)
        return

    entries = _filter(entries, args)

    if args.aggregate:
        rows = _aggregate(entries, args.aggregate)
        if args.as_json:
            print(json.dumps(rows, indent=2))
        else:
            cols = [args.aggregate, "runs", "passed", "failed",
                    "cost_usd", "in_tokens", "out_tokens", "total_nodes", "total_edges"]
            _table(rows, cols)
    else:
        if args.as_json:
            print(json.dumps(entries, indent=2))
        else:
            cols = ["run_num", "timestamp", "sprint", "file_type", "tool_name",
                    "nodes", "edges", "duration_s", "passed",
                    "prompt_version", "suite_version", "orchestrator_model",
                    "cost_usd", "in_tokens", "out_tokens"]
            _table(entries, cols)

    print(f"\n({len(entries)} run(s) shown)")


if __name__ == "__main__":
    main()
