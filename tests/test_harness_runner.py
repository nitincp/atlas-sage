"""Sprint validation runner — auto-discovers all SprintSpecs from test_harness/specs/.

To add a new sprint: create test_harness/specs/sprintN.py with SPEC = SprintSpec(...).
No changes to this file needed.

Run:
    pytest tests/test_harness_runner.py -v -s              # all sprints
    pytest tests/test_harness_runner.py -v -s -k sprint2   # one sprint
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from atlas_sage.testing.runner import SprintSpec, run_sprint

_SPECS_DIR = Path(__file__).parent.parent / "test_harness" / "specs"


def _load_specs() -> list[SprintSpec]:
    specs: list[SprintSpec] = []
    if not _SPECS_DIR.exists():
        return specs
    for spec_file in sorted(_SPECS_DIR.glob("*.py")):
        mod_spec = importlib.util.spec_from_file_location(spec_file.stem, spec_file)
        mod = importlib.util.module_from_spec(mod_spec)
        mod_spec.loader.exec_module(mod)
        if hasattr(mod, "SPEC"):
            specs.append(mod.SPEC)
    return specs


@pytest.fixture
def config():
    try:
        from atlas_sage.config import Config
        return Config()
    except EnvironmentError as exc:
        pytest.skip(str(exc))


@pytest.mark.parametrize("spec", _load_specs(), ids=lambda s: s.name)
def test_sprint(spec: SprintSpec, config, tmp_path):
    db_path = str(tmp_path / "db")
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    for name, content in spec.files.items():
        (src_dir / name).write_text(content)

    artifact = run_sprint(spec, config, db_path, str(src_dir))
    print(
        f"\n{spec.name}: {len(artifact.nodes)} nodes | {len(artifact.edges)} edges"
        f" | {artifact.duration_s:.0f}s | ${artifact.cost_usd:.4f}"
    )
    print(f"  Skill: {artifact.skill.get('name')} ({artifact.skill.get('tool_name')})")
    if spec.required_execution_environment:
        print(f"  Env:   {artifact.skill.get('execution_environment')}")
