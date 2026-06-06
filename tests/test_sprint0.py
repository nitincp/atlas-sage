"""Sprint 0 end-to-end tests — AS-01 through AS-09.

Model config comes from .env (same source as the CLI).
Set ATLAS_ORCHESTRATOR_MODEL and ATLAS_SKILL_MODEL in your .env.

Run with -s to see orchestrator tool traces (INFO logs).
"""

from __future__ import annotations

import shutil

import pytest

SAMPLE_CS = """\
namespace BlazorShared.Models;

public class CatalogItem
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string Description { get; set; }
    public decimal Price { get; set; }

    public bool IsAvailable()
    {
        return Price > 0 && !string.IsNullOrEmpty(Name);
    }
}
"""


@pytest.fixture(scope="module")
def config():
    """Build Config from env vars. Skips if required vars are missing."""
    try:
        from atlas_sage.config import Config
        return Config()
    except EnvironmentError as exc:
        pytest.skip(str(exc))


@pytest.fixture(scope="module")
def temp_db(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("atlas_db"))
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(scope="module")
def sample_cs_file(tmp_path_factory):
    d = tmp_path_factory.mktemp("cs_files")
    f = d / "CatalogItem.cs"
    f.write_text(SAMPLE_CS)
    return str(f)


def _make_config(config, lancedb_path: str):
    """Clone config with a different lancedb_path (isolates each test run)."""
    return type(config)(
        orchestrator_model=config.orchestrator_model,
        skill_model=config.skill_model,
        ollama_base=config.ollama_base,
        lancedb_path=lancedb_path,
        embed_model=config.embed_model,
    )


# ── AS-01 / AS-02: Store initialisation ───────────────────────────────────────

def test_store_initialises(temp_db):
    from atlas_sage.store.store import AtlasStore
    store = AtlasStore(temp_db)
    table_names = store._db.list_tables().tables
    for expected in ("nodes", "edges", "skills", "communities", "corrections"):
        assert expected in table_names


# ── AS-03: Skill registry ─────────────────────────────────────────────────────

def test_search_skills_returns_empty_on_fresh_store(temp_db):
    from atlas_sage.store.store import AtlasStore
    from atlas_sage.tools.skill_tools import search_skills
    store = AtlasStore(temp_db)
    assert search_skills(["csharp", ".cs"], store) == []


# ── AS-04 → AS-07: Full ingestion ─────────────────────────────────────────────

def test_ingest_creates_node(config, temp_db, sample_cs_file):
    """Ingest a .cs file — verify at least one node and one skill are stored."""
    from atlas_sage.ingestion.pipeline import ingest
    from atlas_sage.store.store import AtlasStore

    cfg = _make_config(config, temp_db)
    report = ingest(sample_cs_file, cfg)

    assert report, "Ingestion returned empty report"
    print(f"\n[{config.orchestrator_model}] ingestion report:\n{report}")

    store = AtlasStore(temp_db)
    nodes = store._table("nodes").search().to_list()

    assert len(nodes) >= 1, (
        "Expected ≥1 node in store, got 0. "
        "Run with -s to see orchestrator tool traces."
    )

    source_files = {n["source_file"] for n in nodes}
    assert any(sample_cs_file in sf or sf in sample_cs_file for sf in source_files), (
        f"No node references the ingested file. source_files={source_files}"
    )

    skills = store._table("skills").search().to_list()
    assert len(skills) >= 1, "Expected a C# skill to be created"
    print(f"skill tool_name={skills[0].get('tool_name')}")


# ── AS-08: SME query ──────────────────────────────────────────────────────────

def test_query_returns_answer(config, temp_db):
    """Query the graph — answer must be non-empty."""
    from atlas_sage.query.pipeline import query

    cfg = _make_config(config, temp_db)
    answer = query("What does CatalogItem represent?", cfg)

    assert answer, "Query returned empty answer"
    assert len(answer) > 50, f"Answer suspiciously short: {answer!r}"
    print(f"\n[{config.orchestrator_model}] query answer:\n{answer}")
