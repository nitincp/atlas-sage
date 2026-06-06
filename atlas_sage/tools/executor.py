"""Skill executor — runs the extraction_script from a skill document.

Supports two runtimes determined by the skill's execution_environment field:
  python / python+dotnet / python+node
      exec() the script in a Python namespace.
      Variables pre-set: source_code (str), file_path (str).
      Script must assign: result = [list of node dicts]

  node
      Write the script to a temp .js file and invoke with Node.js.
      file_path is passed as process.argv[2].
      Script must write JSON to stdout: process.stdout.write(JSON.stringify(result))
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile

from ..store.store import AtlasStore

# Resolve the project root (two levels up from this file: atlas_sage/tools/ → project root)
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
_NODE_MODULES = _PROJECT_ROOT / "node_modules"


def execute_skill(skill_id: str, file_path: str, store: AtlasStore) -> list[dict]:
    """Load skill, read file, run extraction_script, return raw nodes."""
    skill = store.get_skill(skill_id)
    if skill is None:
        raise ValueError(f"Skill not found: {skill_id}")

    env = skill.get("execution_environment", "python")

    if env == "node":
        return _exec_node(skill, file_path)
    else:
        return _exec_python(skill, file_path)


def _exec_python(skill: dict, file_path: str) -> list[dict]:
    with open(file_path, encoding="utf-8") as fh:
        source_code = fh.read()

    namespace: dict = {"source_code": source_code, "file_path": file_path}
    exec(skill["extraction_script"], namespace)  # noqa: S102

    result = namespace.get("result")
    if result is None:
        raise RuntimeError(
            f"Skill '{skill['name']}' extraction_script did not set `result`. "
            "The script must assign a list of node dicts to `result`."
        )
    if not isinstance(result, list):
        raise RuntimeError(f"Skill '{skill['name']}' `result` must be a list, got {type(result)}")
    return result


def _exec_node(skill: dict, file_path: str) -> list[dict]:
    if not shutil.which("node"):
        raise RuntimeError(
            "node not found on PATH — install Node.js, then run the skill's install_cmd:\n"
            f"  {skill.get('install_cmd', 'npm install ...')}"
        )

    script = skill["extraction_script"]
    tmp = tempfile.NamedTemporaryFile(suffix=".js", mode="w", delete=False)
    try:
        tmp.write(script)
        tmp.close()
        env = os.environ.copy()
        # Expose project node_modules so skills can require postcss, ts-morph, etc.
        if _NODE_MODULES.exists():
            existing = env.get("NODE_PATH", "")
            env["NODE_PATH"] = str(_NODE_MODULES) + (f":{existing}" if existing else "")
        output = subprocess.check_output(
            ["node", tmp.name, file_path],
            text=True,
            timeout=30,
            stderr=subprocess.PIPE,
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Node.js skill '{skill['name']}' failed (exit {exc.returncode}):\n{exc.stderr}"
        ) from exc
    finally:
        os.unlink(tmp.name)

    try:
        result = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Node.js skill '{skill['name']}' produced invalid JSON:\n{output[:500]}"
        ) from exc

    if not isinstance(result, list):
        raise RuntimeError(f"Node.js skill '{skill['name']}' must output a JSON array, got {type(result)}")
    return result
