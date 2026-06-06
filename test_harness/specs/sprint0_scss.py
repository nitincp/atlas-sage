"""Sprint 0 SCSS — PostCSS/Node.js skill, single-file ingestion.

Language: SCSS (PostCSS — Node.js runtime)
Thesis claim: SSR operational loop works end-to-end (Sprint 0)
"""
from atlas_sage.testing.runner import QuerySpec, SprintSpec

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

SPEC = SprintSpec(
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
    required_deterministic_edges=0,
)
