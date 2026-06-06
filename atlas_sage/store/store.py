"""AtlasStore — LanceDB connection, table initialisation, and CRUD operations."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

import lancedb

from .schema import (
    COMMUNITY_SCHEMA,
    CORRECTION_SCHEMA,
    EDGE_SCHEMA,
    NODE_SCHEMA,
    SKILL_SCHEMA,
)

_TABLES = {
    "nodes": NODE_SCHEMA,
    "edges": EDGE_SCHEMA,
    "communities": COMMUNITY_SCHEMA,
    "corrections": CORRECTION_SCHEMA,
    "skills": SKILL_SCHEMA,
}


class AtlasStore:
    """Thin wrapper around LanceDB providing typed access to all ATLAS-SAGE tables."""

    def __init__(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        self._db = lancedb.connect(path)
        self._ensure_tables()

    # ── Table access ──────────────────────────────────────────────────────────

    def _ensure_tables(self) -> None:
        existing = set(self._db.list_tables().tables)
        for name, schema in _TABLES.items():
            if name not in existing:
                self._db.create_table(name, schema=schema)

    def _table(self, name: str):
        return self._db.open_table(name)

    # ── Nodes ─────────────────────────────────────────────────────────────────

    def write_node(self, node: dict[str, Any]) -> str:
        """Write a node to the store. Returns node_id."""
        now = _now()
        row = {
            "node_id": node["node_id"],
            "language": node.get("language", "unknown"),
            "source_file": node.get("source_file", ""),
            "chunk_type": node.get("chunk_type", "unknown"),
            "raw_cleaned": node.get("raw_cleaned", ""),
            "summary": node.get("summary", ""),
            "community_id": node.get("community_id", ""),
            "embedding": node.get("embedding", [0.0] * 1024),
            "created_at": now,
            "updated_at": now,
        }
        self._table("nodes").add([row])
        return node["node_id"]

    def get_node(self, node_id: str) -> dict | None:
        results = self._table("nodes").search().where(f"node_id = '{node_id}'").limit(1).to_list()
        return results[0] if results else None

    def vector_search(self, embedding: list[float], limit: int = 5) -> list[dict]:
        return self._table("nodes").search(embedding).limit(limit).to_list()

    # ── Edges ─────────────────────────────────────────────────────────────────

    def write_edge(self, edge: dict[str, Any]) -> str:
        row = {
            "edge_id": edge["edge_id"],
            "source_node_id": edge["source_node_id"],
            "target_node_id": edge["target_node_id"],
            "type": edge.get("type", "UNKNOWN"),
            "confidence": edge.get("confidence", "inferred"),
            "evidence": edge.get("evidence", ""),
            "created_at": _now(),
        }
        self._table("edges").add([row])
        return edge["edge_id"]

    def get_edges_for_node(self, node_id: str) -> list[dict]:
        return (
            self._table("edges")
            .search()
            .where(f"source_node_id = '{node_id}'")
            .to_list()
        )

    def get_incoming_edges(self, node_id: str) -> list[dict]:
        """Return edges where this node is the target (who depends on / calls this node)."""
        return (
            self._table("edges")
            .search()
            .where(f"target_node_id = '{node_id}'")
            .to_list()
        )

    def list_nodes(self, limit: int = 200) -> list[dict]:
        """Return all nodes (summary + metadata only, no embeddings)."""
        rows = self._table("nodes").search().limit(limit).to_list()
        for row in rows:
            row.pop("embedding", None)
        return rows

    # ── Skills ────────────────────────────────────────────────────────────────

    def write_skill(self, skill: dict[str, Any]) -> str:
        row = {
            "skill_id": skill["skill_id"],
            "name": skill.get("name", ""),
            "file_types": json.dumps(skill.get("file_types", [])),
            "tool_name": skill.get("tool_name", ""),
            "execution_environment": skill.get("execution_environment", "python"),
            "install_cmd": skill.get("install_cmd", ""),
            "extraction_script": skill.get("extraction_script", ""),
            "chunk_types": json.dumps(skill.get("chunk_types", [])),
            "edge_types": json.dumps(skill.get("edge_types", [])),
            "limitations": json.dumps(skill.get("limitations", [])),
            "application_role": skill.get("application_role", ""),
            "summarisation_instructions": skill.get("summarisation_instructions", ""),
            "handbook": skill.get("handbook", ""),
            "created_at": _now(),
            "version": skill.get("version", 1),
        }
        self._table("skills").add([row])
        return skill["skill_id"]

    def search_skills(self, file_types: list[str]) -> list[dict]:
        """Find skills that cover any of the given file types (exact match on stored JSON)."""
        all_skills = self._table("skills").search().to_list()
        matches = []
        for row in all_skills:
            stored_types = json.loads(row.get("file_types", "[]"))
            if any(ft in stored_types for ft in file_types):
                row["file_types"] = stored_types
                row["chunk_types"] = json.loads(row.get("chunk_types", "[]"))
                row["edge_types"] = json.loads(row.get("edge_types", "[]"))
                row["limitations"] = json.loads(row.get("limitations", "[]"))
                matches.append(row)
        return matches

    def get_skill(self, skill_id: str) -> dict | None:
        results = self._table("skills").search().where(f"skill_id = '{skill_id}'").limit(1).to_list()
        if not results:
            return None
        row = results[0]
        row["file_types"] = json.loads(row.get("file_types", "[]"))
        row["chunk_types"] = json.loads(row.get("chunk_types", "[]"))
        row["edge_types"] = json.loads(row.get("edge_types", "[]"))
        row["limitations"] = json.loads(row.get("limitations", "[]"))
        return row

    # ── Communities ───────────────────────────────────────────────────────────

    def write_community(self, community: dict[str, Any]) -> str:
        row = {
            "community_id": community["community_id"],
            "level": community.get("level", 0),
            "member_node_ids": community.get("member_node_ids", []),
            "summary": community.get("summary", ""),
            "embedding": community.get("embedding", [0.0] * 3072),
            "updated_at": _now(),
        }
        self._table("communities").add([row])
        return community["community_id"]

    def list_communities(self, limit: int = 100) -> list[dict]:
        rows = self._table("communities").search().limit(limit).to_list()
        for row in rows:
            row.pop("embedding", None)
        return rows

    def vector_search_communities(self, embedding: list[float], limit: int = 3) -> list[dict]:
        return self._table("communities").search(embedding).limit(limit).to_list()

    def update_node_community(self, node_id: str, community_id: str) -> None:
        self._table("nodes").update(
            where=f"node_id = '{node_id}'",
            values={"community_id": community_id},
        )

    def get_all_edges(self) -> list[dict]:
        return self._table("edges").search().to_list()

    # ── Corrections ───────────────────────────────────────────────────────────

    def write_correction(self, correction: dict[str, Any]) -> str:
        row = {
            "correction_id": correction["correction_id"],
            "session_id": correction.get("session_id", ""),
            "target_type": correction.get("target_type", "node"),
            "target_id": correction.get("target_id", ""),
            "original": correction.get("original", ""),
            "corrected": correction.get("corrected", ""),
            "captured_at": _now(),
        }
        self._table("corrections").add([row])
        return correction["correction_id"]

    def get_corrections(self, target_id: str) -> list[dict]:
        """Return all corrections stored against a node, edge, community id, or logical name."""
        return (
            self._table("corrections")
            .search()
            .where(f"target_id = '{target_id}'")
            .to_list()
        )

    def get_all_corrections(self) -> list[dict]:
        """Return every correction in the store."""
        return self._table("corrections").search().to_list()


def _now() -> datetime:
    return datetime.now(timezone.utc)
