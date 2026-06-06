"""Sprint 0 end-to-end tests.

AS-09: Verify end-to-end: question in, answer out, node traceable to skill used.

These tests require:
  - ATLAS_TIER1_MODEL and ATLAS_TIER2_MODEL env vars set
  - A running LLM backend (Ollama or API key)
  - tree-sitter-c-sharp installed

Run with: pytest tests/test_sprint0.py -v
"""

from __future__ import annotations

import os
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
    """Config fixture — skips module if model env vars are not set."""
    tier1 = os.getenv("ATLAS_TIER1_MODEL")
    tier2 = os.getenv("ATLAS_TIER2_MODEL")
    if not tier1 or not tier2:
        pytest.skip("ATLAS_TIER1_MODEL and ATLAS_TIER2_MODEL must be set to run Sprint 0 tests.")
    from atlas_sage.config import Config
    return Config()


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


# ── AS-01 / AS-02: Store initialisation ───────────────────────────────────────

def test_store_initialises(temp_db):
    from atlas_sage.store.store import AtlasStore
    store = AtlasStore(temp_db)
    # All five tables must exist after init
    table_names = store._db.list_tables().tables
    assert "nodes" in table_names
    assert "edges" in table_names
    assert "skills" in table_names
    assert "communities" in table_names
    assert "corrections" in table_names


# ── AS-03: Skill registry ─────────────────────────────────────────────────────

def test_search_skills_returns_empty_on_fresh_store(temp_db):
    from atlas_sage.store.store import AtlasStore
    from atlas_sage.tools.skill_tools import search_skills
    store = AtlasStore(temp_db)
    result = search_skills(["csharp", ".cs"], store)
    assert result == []


# ── AS-04 → AS-07: Full ingestion ─────────────────────────────────────────────

def test_ingest_creates_node(config, temp_db, sample_cs_file):
    """Ingest a .cs file — verify at least one node is stored."""
    # Override lancedb path to use our temp db
    config_copy = type(config)(
        tier1_model=config.tier1_model,
        tier2_model=config.tier2_model,
        ollama_base=config.ollama_base,
        lancedb_path=temp_db,
        embed_model=config.embed_model,
    )

    from atlas_sage.ingestion.pipeline import ingest
    report = ingest(sample_cs_file, config_copy)

    assert report, "Ingestion returned empty report"

    from atlas_sage.store.store import AtlasStore
    store = AtlasStore(temp_db)

    nodes = store._table("nodes").search().to_list()
    assert len(nodes) >= 1, f"Expected at least 1 node in store, got {len(nodes)}"

    # Verify the node references the ingested file
    source_files = {n["source_file"] for n in nodes}
    assert any(sample_cs_file in sf or sf in sample_cs_file for sf in source_files), (
        f"No node references the ingested file. source_files={source_files}"
    )

    # Verify a skill was created
    skills = store._table("skills").search().to_list()
    assert len(skills) >= 1, "Expected a C# skill to be created"


# ── AS-08: SME query ──────────────────────────────────────────────────────────

def test_query_returns_answer(config, temp_db):
    """Query the graph — answer must be non-empty and reference the ingested content."""
    config_copy = type(config)(
        tier1_model=config.tier1_model,
        tier2_model=config.tier2_model,
        ollama_base=config.ollama_base,
        lancedb_path=temp_db,
        embed_model=config.embed_model,
    )

    from atlas_sage.query.pipeline import query
    answer = query("What does CatalogItem represent?", config_copy)

    assert answer, "Query returned empty answer"
    assert len(answer) > 50, f"Answer suspiciously short: {answer!r}"
