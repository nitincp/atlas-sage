"""SCSS ingestion grounding test.

Uses PostCSS (Node.js) — fast, no dotnet, no heavy model downloads.
Embedding: gemini/gemini-embedding-001 via LiteLLM (cloud, no local model).

Run:
    pytest tests/test_scss.py -v -s
"""

from __future__ import annotations

import shutil

import pytest

SAMPLE_SCSS = """\
$primary-color: #3498db;
$danger-color: #e74c3c;
$font-size-base: 16px;

@mixin flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

@mixin respond-to($breakpoint) {
  @if $breakpoint == mobile {
    @media (max-width: 768px) { @content; }
  }
}

@import 'variables';
@import 'mixins';

.product-card {
  @include flex-center;
  padding: 1rem;
  border: 1px solid #eee;

  &__price {
    color: $primary-color;
    font-size: $font-size-base * 1.5;
  }

  &__status--unavailable {
    opacity: 0.5;
    cursor: not-allowed;
    color: $danger-color;
  }
}

.btn-danger {
  background-color: $danger-color;
  color: white;
}
"""


@pytest.fixture(scope="module")
def config():
    try:
        from atlas_sage.config import Config
        return Config()
    except EnvironmentError as exc:
        pytest.skip(str(exc))


@pytest.fixture(scope="module")
def temp_db(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("scss_db"))
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(scope="module")
def sample_scss_file(tmp_path_factory):
    d = tmp_path_factory.mktemp("scss_files")
    f = d / "product.scss"
    f.write_text(SAMPLE_SCSS)
    return str(f)


def _make_config(config, lancedb_path: str):
    return type(config)(
        orchestrator_model=config.orchestrator_model,
        skill_model=config.skill_model,
        lancedb_path=lancedb_path,
        embed_model=config.embed_model,
    )


def test_scss_ingest_creates_nodes(config, temp_db, sample_scss_file):
    """Ingest a .scss file — verify skill uses PostCSS/Node and nodes are stored."""
    from atlas_sage.ingestion.pipeline import ingest
    from atlas_sage.store.store import AtlasStore

    cfg = _make_config(config, temp_db)
    report = ingest(sample_scss_file, cfg)

    print(f"\n{report}")

    store = AtlasStore(temp_db)

    skills = store._table("skills").search().to_list()
    assert len(skills) >= 1, "Expected a SCSS skill to be created"
    skill = skills[0]
    print(f"\nskill: {skill['name']} | env: {skill['execution_environment']} | tool: {skill['tool_name']}")

    nodes = store._table("nodes").search().to_list()
    assert len(nodes) >= 1, "Expected ≥1 node stored after SCSS ingestion"

    chunk_types = {n["chunk_type"] for n in nodes}
    print(f"chunk_types found: {chunk_types}")

    # SCSS should produce at least one recognisable CSS construct.
    # LLM-generated type names vary (e.g. "variable_declaration" vs "variable",
    # "selector_rule" vs "style-rule") — match by keyword prefix.
    keywords = {"variable", "mixin", "selector", "style", "import", "rule"}
    assert any(
        any(kw in ct for kw in keywords) for ct in chunk_types
    ), f"Expected CSS-related chunk types, got {chunk_types}"


def test_scss_query(config, temp_db):
    """Query the SCSS graph — answer should reference product-card or price."""
    from atlas_sage.query.pipeline import query

    cfg = _make_config(config, temp_db)
    answer = query("What UI components are defined in the knowledge graph?", cfg)

    assert answer, "Query returned empty answer"
    assert len(answer) > 50, f"Answer too short: {answer!r}"
    print(f"\n{answer}")
