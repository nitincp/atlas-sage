"""Skill executor — runs the extraction_script from a skill document.

The script receives `source_code` and `file_path` in its namespace and must
assign a list of tool contract dicts to `result`.
"""

from __future__ import annotations

from ..store.store import AtlasStore


def execute_skill(skill_id: str, file_path: str, store: AtlasStore) -> list[dict]:
    """Load skill, read file, exec extraction_script, return raw nodes."""
    skill = store.get_skill(skill_id)
    if skill is None:
        raise ValueError(f"Skill not found: {skill_id}")

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
