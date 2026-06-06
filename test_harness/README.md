# ATLAS-SAGE Test Harness

> The test harness is the **only** ground for validating sprint-level ingestion behavior.
> Every run produces versioned artifacts, tracks cost and tokens, logs pass/fail, and rebuilds
> the index automatically. No standalone scripts. No ad-hoc assertions.

The harness evolves sprint-to-sprint. **There is no backward version support — this is by
design.** When the harness gains new capabilities for Sprint N, older specs may no longer
run correctly under it. That is acceptable. Run artifacts are historical records; the harness
is always optimised for the current sprint frontier.

**Hard rule:** adding a new sprint means adding one file to `test_harness/specs/`. No new
test files. No standalone scripts. The runner discovers specs automatically.

---

## Sandbox assumption

> **The dev container is the sandbox.**
>
> There is no separate sandbox environment yet. When a skill's `install_cmd` runs
> (e.g. `npm install ts-morph` or `pip install lxml`), it executes directly inside
> the dev container. This is the intended behavior until a dedicated sandbox is wired in.
> Keep `install_cmd` entries idempotent — they will mutate the dev container's
> `node_modules` or Python environment on first execution.

---

## Directory layout

```
test_harness/
  README.md               ← this file
  index.md                ← rebuilt after every run; prompt + suite + run tables
  run_log.json            ← append-only source of truth; never edit by hand

  specs/                  ← one file per sprint — this is where new sprints go
    sprint0_scss.py       ← SPEC = SprintSpec(...)
    sprint1.py
    sprint2.py

  prompts/
    v001/
      meta.json           ← {version, hash, timestamp, note}
      create_skill.md     ← snapshot of _CREATE_SKILL_SYSTEM at run time
      ingestion.md
      multi_file_ingestion.md
      query.md
    v002/ ...             ← auto-created when any system prompt changes

  test_suites/            ← auto-created on first run of each spec
    python_order_processing_v001/
      models.py  repository.py  service.py  controller.py
      suite.json              ← {name, version, hash, timestamp, pattern, files}
    typescript_order_processing_v001/ ...
    scss_product_card_v001/ ...

  runs/
    20260606_132604/           ← local time (TZ env var)
      meta.json                ← run identity + stats + pass/fail
      output/
        skill.json             ← full skill document used for this run
        nodes.json             ← all nodes (embedding stripped)
        edges.json             ← all edges
        ingestion_report.md    ← orchestrator's free-text report
        queries/
          blast_radius.md      ← LLM answer for each QuerySpec
          dependency.md
```

Versioning is **automatic**:
- Edit any system prompt → new `prompts/vN/` created on next run
- Change any input file in a spec → new `test_suites/<name>_vN/` created on next run
- Same input across prompt versions reuses the existing suite directory

---

## Adding a new sprint

1. Create `test_harness/specs/sprintN.py` with a `SPEC = SprintSpec(...)`.
2. Run `pytest tests/test_harness_runner.py -v -s -k sprintN`.
3. Done. No other files change.

The runner (`tests/test_harness_runner.py`) glob-discovers all `*.py` files in `specs/`
and parametrizes automatically. Alphabetical order.

### Minimal spec file

```python
"""Sprint N — <Language>, <thesis claim>."""
from atlas_sage.testing.runner import QuerySpec, SprintSpec

SAMPLE_FOO = """\
# source code here
"""

SPEC = SprintSpec(
    name="sprintN",
    suite_name="<language>_<domain>",
    files={"foo.ext": SAMPLE_FOO},
    pattern="**/*.ext",
    min_nodes=4,
    min_source_files=1,
    expected_edge_types={"IMPORTS"},
    native_parser_keyword="<parser-name>",
    queries=[
        QuerySpec(
            name="basic",
            question="What does this code do?",
            expected_keywords=["<keyword>"],
        ),
    ],
)
```

That's the entire file. No fixtures, no pytest imports, no test logic.

---

## Running tests

```bash
# All sprints
pytest tests/test_harness_runner.py -v -s

# One sprint
pytest tests/test_harness_runner.py -v -s -k sprint2

# Unit/integration tests (store, skill registry — not sprint validation)
pytest tests/test_sprint0.py -v -s

# Everything
pytest -v -s
```

---

## SprintSpec field reference

| Field | Type | Default | Purpose |
|---|---|---|---|
| `name` | str | — | Sprint identifier used in run_log and artifact directories |
| `suite_name` | str | — | Prefix for the test suite directory in `test_suites/` |
| `files` | dict[str, str] | — | Source files written to a temp dir before ingestion |
| `pattern` | str | — | Glob passed to `ingest_directory` (e.g. `**/*.ts`) |
| `min_nodes` | int | — | Assertion: at least N nodes stored in LanceDB |
| `min_source_files` | int | — | Assertion: nodes span at least N distinct source files |
| `expected_edge_types` | set[str] | — | Assertion: at least one of these edge types must appear |
| `native_parser_keyword` | str | — | Must appear in skill `tool_name`, `handbook`, or `extraction_script` |
| `queries` | list[QuerySpec] | — | SME questions to run and assert against |
| `required_deterministic_edges` | int | 1 | Min edges with `confidence="deterministic"` |
| `required_execution_environment` | str | "" | If set, `skill.execution_environment` must match exactly |

### QuerySpec field reference

| Field | Type | Default | Purpose |
|---|---|---|---|
| `name` | str | — | Answer saved to `output/queries/<name>.md` |
| `question` | str | — | Natural-language question sent to the query pipeline |
| `expected_keywords` | list[str] | — | At least one must appear in the answer (case-insensitive) |
| `min_length` | int | 100 | Answer must exceed this character count |

---

## Querying run history

```bash
# All runs (tabular)
python -m atlas_sage.testing.harness_query

# Filter by sprint
python -m atlas_sage.testing.harness_query --sprint sprint2

# Only passing runs
python -m atlas_sage.testing.harness_query --sprint sprint1 --passed

# Aggregate cost + tokens by prompt version
python -m atlas_sage.testing.harness_query --aggregate prompt_version

# Aggregate by sprint
python -m atlas_sage.testing.harness_query --aggregate sprint

# JSON output (pipe-friendly)
python -m atlas_sage.testing.harness_query --sprint sprint2 --json
```

### run_log.json fields

| Field | Description |
|---|---|
| `run_num` | Monotonically increasing run number |
| `timestamp` | Local time (IST if `TZ=Asia/Kolkata`) |
| `sprint` | `SprintSpec.name` |
| `file_type` | Extension from pattern (e.g. `ts`, `py`, `scss`) |
| `skill_name` | Name the LLM gave the created skill |
| `tool_name` | Parser the skill declared (e.g. `ts-morph`, `ast`, `PostCSS`) |
| `skill_id` | First 8 chars of the skill UUID |
| `nodes` / `edges` | Counts stored in LanceDB for this run |
| `edge_types` | Comma-separated distinct edge types |
| `duration_s` | Wall-clock seconds for full ingest + query cycle |
| `passed` | `true` / `false` |
| `prompt_version` | Which prompt snapshot was active (`v001`, `v002`, ...) |
| `suite_version` | Which input file snapshot was active |
| `orchestrator_model` | Model used for ingestion and query |
| `skill_model` | Model used for skill creation |
| `cost_usd` | Estimated API cost for this run |
| `in_tokens` / `out_tokens` | Token counts |

---

## Extending the harness

### Adding a new assertion

Add a field to `SprintSpec` in [atlas_sage/testing/runner.py](../atlas_sage/testing/runner.py)
and the corresponding check in the relevant `_assert_*` function. Update every active spec
in `test_harness/specs/` to set the field correctly. There is no obligation to give the
field a default that keeps older specs green — if an older spec can't satisfy the new
assertion, update it or accept that it will fail under the current harness.

### Adding an assertion specific to one sprint

Add it directly in the spec file as a module-level callable, or extend `run_sprint`'s
return value (`RunArtifact`) if the data isn't already there. Do not add test logic to
the runner file.

`RunArtifact` fields available after `run_sprint`: `skill`, `nodes`, `edges`,
`ingestion_report`, `query_answers`, `run_dir`, `duration_s`, `prompt_version`,
`suite_version`, `orchestrator_model`, `skill_model`, `cost_usd`, `in_tokens`, `out_tokens`.

### Changing a system prompt

Edit the relevant constant in the source and re-run — a new `prompts/vN/` is created
automatically with a diff note.

| Prompt | Location |
|---|---|
| Skill creation | `atlas_sage/tools/skill_tools.py` → `_CREATE_SKILL_SYSTEM` |
| Single-file ingestion | `atlas_sage/ingestion/pipeline.py` → `_INGESTION_SYSTEM` |
| Multi-file ingestion | `atlas_sage/ingestion/pipeline.py` → `_MULTI_FILE_INGESTION_SYSTEM` |
| Query | `atlas_sage/query/pipeline.py` → `_QUERY_SYSTEM` |

---

## What the harness does NOT do

- It does not share a LanceDB across runs — each test uses a fresh `tmp_path` database.
- It does not retry failed runs — fix the spec or prompt, then re-run.
- It does not diff node/edge content between runs — use `run_log.json` for trend
  analysis and inspect `runs/<timestamp>/output/` directories manually for content diffs.
