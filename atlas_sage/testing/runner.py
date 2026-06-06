"""Generic sprint validation runner.

Each sprint is expressed as a SprintSpec (data only). run_sprint() executes the
full ingest → assert → save loop, versions prompts and input suites, and rebuilds
the root index.

Layout:

    test_harness/
      index.md            ← rebuilt each run; Prompt Versions + Test Runs tables
      run_log.json        ← append-only; source of truth for test run rows
      prompts/
        v001/
          meta.json       ← {version, hash, timestamp, note}
          create_skill.md
          ingestion.md
          multi_file_ingestion.md
          query.md
      test_suites/
        python_order_processing_v001/
          models.py  repository.py  service.py  controller.py
          suite.json  ← {name, version, hash, timestamp, pattern, files, description}
        scss_product_card_v001/
          product.scss
          suite.json
      runs/
        20260606_183022/     ← local time (TZ env var), flat — no sprint subdir
          meta.json          ← {sprint, suite, prompt_version, nodes, edges, passed, duration}
          output/
            skill.json  nodes.json  edges.json  ingestion_report.md
            queries/  <name>.md

Usage:

    SPRINT_N = SprintSpec(
        name="sprint1",
        suite_name="python_order_processing",
        files={"models.py": "...", ...},
        pattern="**/*.py",
        min_nodes=8,
        min_source_files=3,
        expected_edge_types={"IMPLEMENTS", "INJECTS", "CALLS"},
        native_parser_keyword="ast",
        queries=[QuerySpec(name="blast_radius", question="...", expected_keywords=["x"])],
    )

    def test_sprint_n(config, temp_db, src_dir):
        artifact = run_sprint(SPRINT_N, config, temp_db, src_dir)
        print(f"suite={artifact.suite_version}  prompt={artifact.prompt_version}")
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent.parent
TEST_HARNESS_ROOT = _PROJECT_ROOT / "test_harness"
PROMPTS_ROOT = TEST_HARNESS_ROOT / "prompts"
SUITES_ROOT = TEST_HARNESS_ROOT / "test_suites"
RUNS_ROOT = TEST_HARNESS_ROOT / "runs"
INDEX_PATH = TEST_HARNESS_ROOT / "index.md"
RUN_LOG_PATH = TEST_HARNESS_ROOT / "run_log.json"


def _now() -> datetime:
    """Current local time, honouring the TZ environment variable."""
    return datetime.now().astimezone()


def _ts_folder() -> str:
    """Timestamp string for directory names (local time)."""
    return _now().strftime("%Y%m%d_%H%M%S")


def _ts_display() -> str:
    """Timestamp string for index display (local time)."""
    return _now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Spec types — pure data, no logic
# ---------------------------------------------------------------------------


@dataclass
class QuerySpec:
    name: str
    question: str
    expected_keywords: list[str]
    min_length: int = 100


@dataclass
class SprintSpec:
    name: str
    suite_name: str
    files: dict[str, str]
    pattern: str
    min_nodes: int
    min_source_files: int
    expected_edge_types: set[str]
    native_parser_keyword: str
    queries: list[QuerySpec]
    required_deterministic_edges: int = 1
    required_execution_environment: str = ""  # if set, skill.execution_environment must match
    min_communities: int = 0  # >0 enables community detection step + assertions


# ---------------------------------------------------------------------------
# Artifact — result of one run_sprint() call
# ---------------------------------------------------------------------------


@dataclass
class RunArtifact:
    skill: dict
    nodes: list[dict]
    edges: list[dict]
    ingestion_report: str
    query_answers: dict[str, str]
    run_dir: str
    duration_s: float
    prompt_version: str
    suite_version: str
    orchestrator_model: str = ""
    skill_model: str = ""
    cost_usd: float = 0.0
    in_tokens: int = 0
    out_tokens: int = 0
    communities: list[dict] = None

    def __post_init__(self):
        if self.communities is None:
            self.communities = []


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_sprint(
    spec: SprintSpec,
    config,
    lancedb_path: str,
    src_dir: str,
) -> RunArtifact:
    """Execute the full sprint loop, save artifacts, update the index.

    Assertions run internally so pass/fail is captured for the index.
    Raises AssertionError on failure (after saving artifacts and updating index).
    """
    from ..community.pipeline import build_communities
    from ..ingestion.pipeline import ingest_directory
    from ..query.pipeline import query
    from ..store.store import AtlasStore

    TEST_HARNESS_ROOT.mkdir(parents=True, exist_ok=True)
    prompt_version = _get_or_create_prompt_version()
    suite_version = _get_or_create_suite(spec)

    cfg = _make_config(config, lancedb_path)
    t0 = time.monotonic()

    total_cost = 0.0
    total_in = 0
    total_out = 0

    report, ingest_stats = ingest_directory(src_dir, cfg, pattern=spec.pattern)
    total_cost += ingest_stats.get("cost_usd", 0.0)
    total_in += ingest_stats.get("in_tokens", 0)
    total_out += ingest_stats.get("out_tokens", 0)

    store = AtlasStore(lancedb_path)
    skills = store._table("skills").search().to_list()
    skill = skills[0] if skills else {}
    nodes = store._table("nodes").search().to_list()
    edges = store._table("edges").search().to_list()

    communities: list[dict] = []
    if spec.min_communities > 0:
        _, c_stats = build_communities(cfg)
        total_cost += c_stats.get("cost_usd", 0.0)
        total_in += c_stats.get("in_tokens", 0)
        total_out += c_stats.get("out_tokens", 0)
        communities = store.list_communities()

    answers: dict[str, str] = {}
    for q in spec.queries:
        answer, q_stats = query(q.question, cfg)
        answers[q.name] = answer
        total_cost += q_stats.get("cost_usd", 0.0)
        total_in += q_stats.get("in_tokens", 0)
        total_out += q_stats.get("out_tokens", 0)

    duration_s = time.monotonic() - t0
    orchestrator_model = getattr(cfg, "orchestrator_model", "")
    skill_model = getattr(cfg, "skill_model", "")

    run_dir = _save_run(
        spec, skill, nodes, edges, communities, report, answers,
        prompt_version, suite_version, duration_s,
        orchestrator_model, skill_model, total_cost, total_in, total_out,
    )

    artifact = RunArtifact(
        skill=skill,
        nodes=nodes,
        edges=edges,
        communities=communities,
        ingestion_report=report,
        query_answers=answers,
        run_dir=run_dir,
        duration_s=duration_s,
        prompt_version=prompt_version,
        suite_version=suite_version,
        orchestrator_model=orchestrator_model,
        skill_model=skill_model,
        cost_usd=round(total_cost, 6),
        in_tokens=total_in,
        out_tokens=total_out,
    )

    failure: AssertionError | None = None
    try:
        assert_sprint(artifact, spec)
    except AssertionError as exc:
        failure = exc

    _append_run_log(spec, artifact, passed=(failure is None))
    _rebuild_index()

    if failure:
        raise failure

    return artifact


# ---------------------------------------------------------------------------
# Standalone assertions (also called from run_sprint)
# ---------------------------------------------------------------------------


def assert_sprint(artifact: RunArtifact, spec: SprintSpec) -> None:
    """Run all generic sprint assertions. Raises AssertionError on failure."""
    _assert_native_parser(artifact, spec)
    _assert_nodes(artifact, spec)
    _assert_edges(artifact, spec)
    _assert_communities(artifact, spec)
    _assert_queries(artifact, spec)


def _assert_native_parser(artifact: RunArtifact, spec: SprintSpec) -> None:
    skill = artifact.skill
    kw = spec.native_parser_keyword.lower()
    fields = {
        "tool_name": (skill.get("tool_name") or "").lower(),
        "handbook": (skill.get("handbook") or "").lower(),
        "extraction_script": (skill.get("extraction_script") or "").lower(),
    }
    found_in = [name for name, text in fields.items() if kw in text]
    assert found_in, (
        f"Native parser keyword '{spec.native_parser_keyword}' not found in skill.\n"
        f"  tool_name: {skill.get('tool_name')!r}\n"
        f"  handbook excerpt: {fields['handbook'][:200]!r}\n"
        f"  Skill must declare the native parser and include usage instructions."
    )
    assert skill.get("handbook"), (
        "Skill is missing 'handbook'. "
        "The skill must document file type, runtime role, and domain signals."
    )
    assert skill.get("summarisation_instructions"), (
        "Skill is missing 'summarisation_instructions'. "
        "The skill must provide per-chunk-type summarisation guidance."
    )
    assert skill.get("application_role"), (
        "Skill is missing 'application_role'. "
        "The skill must declare which query categories weight these nodes HIGH vs LOW."
    )
    if spec.required_execution_environment:
        actual_env = skill.get("execution_environment", "")
        assert actual_env == spec.required_execution_environment, (
            f"Skill execution_environment is '{actual_env}', "
            f"expected '{spec.required_execution_environment}'.\n"
            f"  TypeScript skills must run in the Node.js environment (ts-morph requires Node)."
        )


def _assert_nodes(artifact: RunArtifact, spec: SprintSpec) -> None:
    nodes = artifact.nodes
    source_files = {n["source_file"] for n in nodes}
    assert len(nodes) >= spec.min_nodes, (
        f"Expected ≥{spec.min_nodes} nodes, got {len(nodes)}"
    )
    assert len(source_files) >= spec.min_source_files, (
        f"Expected nodes from ≥{spec.min_source_files} source files, got {source_files}"
    )


def _assert_edges(artifact: RunArtifact, spec: SprintSpec) -> None:
    edges = artifact.edges
    edge_types = {e["type"] for e in edges}
    allowed_confidence = {"deterministic", "probabilistic", "inferred"}
    found = spec.expected_edge_types & edge_types
    assert found, (
        f"Expected at least one of {spec.expected_edge_types}, got: {edge_types}"
    )
    bad = [e for e in edges if e.get("confidence") not in allowed_confidence]
    assert not bad, (
        f"Edges with invalid confidence: {[(e['edge_id'], e['confidence']) for e in bad]}"
    )
    det = [e for e in edges if e["confidence"] == "deterministic"]
    assert len(det) >= spec.required_deterministic_edges, (
        f"Expected ≥{spec.required_deterministic_edges} deterministic edge(s), got {len(det)}"
    )


def _assert_communities(artifact: RunArtifact, spec: SprintSpec) -> None:
    if spec.min_communities == 0:
        return
    comms = artifact.communities
    assert len(comms) >= spec.min_communities, (
        f"Expected ≥{spec.min_communities} communities, got {len(comms)}"
    )
    missing_summary = [c.get("community_id", "?") for c in comms if not c.get("summary")]
    assert not missing_summary, (
        f"Communities missing summaries: {missing_summary}"
    )


def _assert_queries(artifact: RunArtifact, spec: SprintSpec) -> None:
    for q in spec.queries:
        answer = artifact.query_answers.get(q.name, "")
        assert len(answer) > q.min_length, (
            f"Query '{q.name}' answer too short ({len(answer)} chars): {answer!r}"
        )
        answer_lower = answer.lower()
        found = [kw for kw in q.expected_keywords if kw in answer_lower]
        assert found, (
            f"Query '{q.name}' did not reference expected keywords.\n"
            f"  expected one of: {q.expected_keywords}\n"
            f"  answer excerpt: {answer[:300]!r}"
        )


# ---------------------------------------------------------------------------
# Run artifact persistence — runs/<timestamp>/meta.json + output/
# ---------------------------------------------------------------------------


def _save_run(
    spec: SprintSpec,
    skill: dict,
    nodes: list[dict],
    edges: list[dict],
    communities: list[dict],
    report: str,
    answers: dict[str, str],
    prompt_version: str,
    suite_version: str,
    duration_s: float,
    orchestrator_model: str = "",
    skill_model: str = "",
    cost_usd: float = 0.0,
    in_tokens: int = 0,
    out_tokens: int = 0,
) -> str:
    run_dir = RUNS_ROOT / _ts_folder()
    run_dir.mkdir(parents=True, exist_ok=True)

    # meta.json — run identity
    meta = {
        "sprint": spec.name,
        "suite": suite_version,
        "prompt_version": prompt_version,
        "timestamp": _ts_display(),
        "duration_s": round(duration_s),
        "nodes": len(nodes),
        "edges": len(edges),
        "communities": len(communities),
        "edge_types": sorted({e["type"] for e in edges}),
        "skill_name": skill.get("name") or "-",
        "tool_name": skill.get("tool_name") or "-",
        "skill_id": (skill.get("skill_id") or "")[:8],
        "orchestrator_model": orchestrator_model,
        "skill_model": skill_model,
        "cost_usd": round(cost_usd, 6),
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "passed": None,  # updated by _append_run_log after assertions
    }
    _write_json(run_dir / "meta.json", meta)

    # output/
    out = run_dir / "output"
    out.mkdir()
    _write_json(out / "skill.json", skill)
    _write_json(out / "nodes.json",
                [{k: v for k, v in n.items() if k != "embedding"} for n in nodes])
    _write_json(out / "edges.json", edges)
    _write_json(out / "communities.json",
                [{k: v for k, v in c.items() if k != "embedding"} for c in communities])
    (out / "ingestion_report.md").write_text(report, encoding="utf-8")

    queries_dir = out / "queries"
    queries_dir.mkdir()
    for name, answer in answers.items():
        (queries_dir / f"{name}.md").write_text(answer, encoding="utf-8")

    logger.info("run saved → %s", run_dir)
    return str(run_dir)


# ---------------------------------------------------------------------------
# Test suite versioning
# ---------------------------------------------------------------------------


def _get_or_create_suite(spec: SprintSpec) -> str:
    """Hash input files. Return existing suite version if unchanged, else create new."""
    SUITES_ROOT.mkdir(parents=True, exist_ok=True)

    combined = "\n---\n".join(
        f"{name}:\n{content}" for name, content in sorted(spec.files.items())
    )
    current_hash = hashlib.sha256(combined.encode()).hexdigest()[:8]

    # Search for existing suite with same name prefix and hash
    for suite_dir in sorted(SUITES_ROOT.iterdir()):
        if not suite_dir.name.startswith(spec.suite_name):
            continue
        meta_path = suite_dir / "suite.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("hash") == current_hash:
                return suite_dir.name

    # New suite version
    existing = sorted(
        d.name for d in SUITES_ROOT.iterdir()
        if d.is_dir() and d.name.startswith(spec.suite_name)
    )
    next_num = len(existing) + 1
    suite_version = f"{spec.suite_name}_v{next_num:03d}"
    suite_dir = SUITES_ROOT / suite_version
    suite_dir.mkdir()

    for name, content in spec.files.items():
        (suite_dir / name).write_text(content, encoding="utf-8")

    file_names = sorted(spec.files.keys())
    ext = spec.pattern.lstrip("**/.")
    description = (
        f"{len(file_names)} {ext} file(s): {', '.join(file_names)}"
    )
    _write_json(suite_dir / "suite.json", {
        "name": spec.suite_name,
        "version": suite_version,
        "hash": current_hash,
        "timestamp": _ts_display(),
        "pattern": spec.pattern,
        "files": file_names,
        "description": description,
    })

    logger.info("test suite %s created (hash %s)", suite_version, current_hash)
    return suite_version


# ---------------------------------------------------------------------------
# Prompt versioning
# ---------------------------------------------------------------------------


def _collect_prompts() -> dict[str, str]:
    from ..community.pipeline import _COMMUNITY_SYSTEM
    from ..ingestion.pipeline import (
        _INGESTION_SYSTEM,
        _MULTI_FILE_INGESTION_SYSTEM,
    )
    from ..query.pipeline import _QUERY_SYSTEM
    from ..tools.skill_tools import _CREATE_SKILL_SYSTEM

    return {
        "community": _COMMUNITY_SYSTEM,
        "create_skill": _CREATE_SKILL_SYSTEM,
        "ingestion": _INGESTION_SYSTEM,
        "multi_file_ingestion": _MULTI_FILE_INGESTION_SYSTEM,
        "query": _QUERY_SYSTEM,
    }


def _get_or_create_prompt_version() -> str:
    PROMPTS_ROOT.mkdir(parents=True, exist_ok=True)
    prompts = _collect_prompts()

    combined = "\n---\n".join(f"{k}:\n{v}" for k, v in sorted(prompts.items()))
    current_hash = hashlib.sha256(combined.encode()).hexdigest()[:8]

    for version_dir in sorted(PROMPTS_ROOT.iterdir()):
        meta_path = version_dir / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("hash") == current_hash:
                return meta["version"]

    existing = sorted(
        d.name for d in PROMPTS_ROOT.iterdir()
        if d.is_dir() and d.name.startswith("v")
    )
    next_num = len(existing) + 1
    version = f"v{next_num:03d}"
    version_dir = PROMPTS_ROOT / version
    version_dir.mkdir()

    for name, content in prompts.items():
        (version_dir / f"{name}.md").write_text(content, encoding="utf-8")

    note = _version_note(prompts, existing)
    _write_json(version_dir / "meta.json", {
        "version": version,
        "hash": current_hash,
        "timestamp": _ts_display(),
        "note": note,
    })
    logger.info("prompt version %s created (hash %s)", version, current_hash)
    return version


def _version_note(prompts: dict[str, str], prev_versions: list[str]) -> str:
    if not prev_versions:
        return "Initial prompt snapshot."
    prev_dir = PROMPTS_ROOT / prev_versions[-1]
    changed: list[str] = []
    for name, content in sorted(prompts.items()):
        prev_file = prev_dir / f"{name}.md"
        if not prev_file.exists():
            changed.append(f"{name} (new)")
        else:
            prev = prev_file.read_text(encoding="utf-8")
            if prev != content:
                delta = len(content) - len(prev)
                sign = "+" if delta >= 0 else ""
                changed.append(f"{name} ({sign}{delta} chars)")
    return f"Changed: {', '.join(changed)}." if changed else "No detected changes."


# ---------------------------------------------------------------------------
# Run log + index rebuild
# ---------------------------------------------------------------------------


def _append_run_log(spec: SprintSpec, artifact: RunArtifact, passed: bool) -> None:
    entries: list[dict] = []
    if RUN_LOG_PATH.exists():
        entries = json.loads(RUN_LOG_PATH.read_text(encoding="utf-8"))

    file_type = spec.pattern.lstrip("**/.")
    rel_dir = str(Path(artifact.run_dir).relative_to(TEST_HARNESS_ROOT))

    entries.append({
        "run_num": len(entries) + 1,
        "timestamp": _ts_display(),
        "sprint": spec.name,
        "file_type": file_type,
        "skill_name": artifact.skill.get("name") or "-",
        "tool_name": artifact.skill.get("tool_name") or "-",
        "skill_id": (artifact.skill.get("skill_id") or "")[:8],
        "nodes": len(artifact.nodes),
        "edges": len(artifact.edges),
        "communities": len(artifact.communities),
        "edge_types": ", ".join(sorted({e["type"] for e in artifact.edges})),
        "duration_s": round(artifact.duration_s),
        "passed": passed,
        "prompt_version": artifact.prompt_version,
        "suite_version": artifact.suite_version,
        "run_dir": rel_dir,
        "orchestrator_model": artifact.orchestrator_model,
        "skill_model": artifact.skill_model,
        "cost_usd": artifact.cost_usd,
        "in_tokens": artifact.in_tokens,
        "out_tokens": artifact.out_tokens,
    })
    _write_json(RUN_LOG_PATH, entries)

    # Update meta.json in the run dir with final pass/fail
    meta_path = Path(artifact.run_dir) / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["passed"] = passed
        _write_json(meta_path, meta)


def _rebuild_index() -> None:
    """Rebuild index.md from run_log.json and prompts/*/meta.json."""
    # ── Prompt versions ──────────────────────────────────────────────────────
    prompt_rows: list[str] = []
    if PROMPTS_ROOT.exists():
        for vdir in sorted(PROMPTS_ROOT.iterdir()):
            mp = vdir / "meta.json"
            if mp.exists():
                m = json.loads(mp.read_text(encoding="utf-8"))
                prompt_rows.append(
                    f"| {m['version']} | {m['timestamp']} | `{m['hash']}` | {m['note']} |"
                )

    # ── Test suites ───────────────────────────────────────────────────────────
    suite_rows: list[str] = []
    if SUITES_ROOT.exists():
        for sdir in sorted(SUITES_ROOT.iterdir()):
            sp = sdir / "suite.json"
            if sp.exists():
                s = json.loads(sp.read_text(encoding="utf-8"))
                suite_rows.append(
                    f"| {s['version']} | {s['timestamp']} | `{s['hash']}`"
                    f" | {s['pattern']} | {s['description']} |"
                )

    # ── Test runs ─────────────────────────────────────────────────────────────
    run_rows: list[str] = []
    if RUN_LOG_PATH.exists():
        for e in json.loads(RUN_LOG_PATH.read_text(encoding="utf-8")):
            pass_mark = "✅" if e["passed"] else "❌"
            cost = f"${e.get('cost_usd', 0):.4f}"
            tok = f"{e.get('in_tokens', 0)}↑{e.get('out_tokens', 0)}↓"
            omodel = e.get("orchestrator_model", "-")
            comms = e.get("communities", "-")
            run_rows.append(
                f"| {e['run_num']} | {e['timestamp']} | {e['sprint']}"
                f" | {e['file_type']} | {e['skill_name']} | {e['tool_name']}"
                f" | {e['skill_id']} | {e['nodes']} | {e['edges']} | {comms}"
                f" | {e['edge_types']} | {e['duration_s']}s"
                f" | {pass_mark} | {e['prompt_version']} | {e['suite_version']}"
                f" | {omodel} | {cost} | {tok}"  # noqa: E501
                f" | `{e['run_dir']}` |"
            )

    content = (
        "# ATLAS-SAGE Test Harness Index\n\n"
        "## Prompt Versions\n\n"
        "| Version | Timestamp | Hash | Note |\n"
        "|---------|-----------|------|------|\n"
        + ("\n".join(prompt_rows) + "\n" if prompt_rows else "")
        + "\n"
        "## Test Suites\n\n"
        "| Suite | Timestamp | Hash | Pattern | Description |\n"
        "|-------|-----------|------|---------|-------------|\n"
        + ("\n".join(suite_rows) + "\n" if suite_rows else "")
        + "\n"
        "## Test Runs\n\n"
        "| # | Timestamp | Sprint | Type | Skill | Tool | Skill ID"
        " | Nodes | Edges | Comms | Edge Types | Dur | Pass | Prompt | Suite"
        " | Model | Cost | Tokens | Run Dir |\n"
        "|---|-----------|--------|------|-------|------|---------|"
        "-------|-------|-------|------------|-----|------|--------|-------|"
        "-------|------|--------|--------|\n"
        + ("\n".join(run_rows) + "\n" if run_rows else "")
    )
    INDEX_PATH.write_text(content, encoding="utf-8")
    logger.info("index rebuilt → %s", INDEX_PATH)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _make_config(config, lancedb_path: str):
    return type(config)(
        orchestrator_model=config.orchestrator_model,
        skill_model=config.skill_model,
        lancedb_path=lancedb_path,
        embed_model=config.embed_model,
    )
