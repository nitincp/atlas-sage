"""Sprint 0 SCSS validation — PostCSS/Node.js skill, single-file ingestion.

Language: SCSS (PostCSS — Node.js runtime)
Thesis claim: SSR operational loop works end-to-end (Sprint 0)

Edge types exercised:
  IMPORTS — @import statements (deterministic)
  USES    — @include mixin references (deterministic)

AS-01 through AS-09: walking skeleton validated.

Run:
    pytest tests/test_scss.py -v -s

Artifacts saved to: test_runs/sprint0_scss/<timestamp>/
"""

from __future__ import annotations

import shutil

import pytest

from atlas_sage.testing.runner import QuerySpec, SprintSpec, run_sprint

# ---------------------------------------------------------------------------
# Sample SCSS — variables, mixins, selectors, imports, BEM nesting
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Sprint 0 SCSS specification — data only
# ---------------------------------------------------------------------------

SPRINT0_SCSS = SprintSpec(
    name="sprint0_scss",
    suite_name="scss_product_card",
    files={"product.scss": SAMPLE_SCSS},
    pattern="**/*.scss",
    min_nodes=1,
    min_source_files=1,
    expected_edge_types={"IMPORTS", "USES", "CALLS", "INCLUDES"},
    native_parser_keyword="postcss",
    queries=[
        QuerySpec(
            name="ui_components",
            question="What UI components are defined in the knowledge graph?",
            expected_keywords=["product", "card", "price", "btn", "button", "danger"],
            min_length=50,
        ),
    ],
    required_deterministic_edges=0,  # SCSS may produce 0 cross-file edges on a single file
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
def src_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("scss_src")
    for name, content in SPRINT0_SCSS.files.items():
        (d / name).write_text(content)
    return str(d)


# ---------------------------------------------------------------------------
# Test — one function, all assertions delegated to assert_sprint()
# ---------------------------------------------------------------------------


def test_scss(config, temp_db, src_dir):
    """AS-01 through AS-09: SCSS ingest via PostCSS skill, query answered."""
    artifact = run_sprint(SPRINT0_SCSS, config, temp_db, src_dir)
    print(f"\nNodes: {len(artifact.nodes)} | Edges: {len(artifact.edges)} | {artifact.duration_s:.0f}s")
    print(f"Skill: {artifact.skill.get('name')} ({artifact.skill.get('tool_name')})")
    print(f"Artifacts: {artifact.run_dir}  prompt: {artifact.prompt_version}")
