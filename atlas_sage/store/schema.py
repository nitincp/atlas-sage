"""PyArrow schemas for all LanceDB tables.

Field names match the tool contract and CLAUDE.md store schema exactly.
"""

from __future__ import annotations

import pyarrow as pa

EMBEDDING_DIM = 3072  # gemini-embedding-001 (default output dim)

NODE_SCHEMA = pa.schema([
    pa.field("node_id", pa.string()),
    pa.field("language", pa.string()),
    pa.field("source_file", pa.string()),
    pa.field("chunk_type", pa.string()),
    pa.field("raw_cleaned", pa.large_string()),
    pa.field("summary", pa.large_string()),
    pa.field("community_id", pa.string()),
    pa.field("embedding", pa.list_(pa.float32(), EMBEDDING_DIM)),
    pa.field("created_at", pa.timestamp("us", tz="UTC")),
    pa.field("updated_at", pa.timestamp("us", tz="UTC")),
])

EDGE_SCHEMA = pa.schema([
    pa.field("edge_id", pa.string()),
    pa.field("source_node_id", pa.string()),
    pa.field("target_node_id", pa.string()),
    pa.field("type", pa.string()),
    pa.field("confidence", pa.string()),  # deterministic|probabilistic|inferred
    pa.field("evidence", pa.large_string()),
    pa.field("created_at", pa.timestamp("us", tz="UTC")),
])

COMMUNITY_SCHEMA = pa.schema([
    pa.field("community_id", pa.string()),
    pa.field("level", pa.int32()),
    pa.field("member_node_ids", pa.list_(pa.string())),
    pa.field("summary", pa.large_string()),
    pa.field("embedding", pa.list_(pa.float32(), EMBEDDING_DIM)),
    pa.field("updated_at", pa.timestamp("us", tz="UTC")),
])

CORRECTION_SCHEMA = pa.schema([
    pa.field("correction_id", pa.string()),
    pa.field("session_id", pa.string()),
    pa.field("target_type", pa.string()),  # node|edge|community
    pa.field("target_id", pa.string()),
    pa.field("original", pa.large_string()),
    pa.field("corrected", pa.large_string()),
    pa.field("captured_at", pa.timestamp("us", tz="UTC")),
])

SKILL_SCHEMA = pa.schema([
    pa.field("skill_id", pa.string()),
    pa.field("name", pa.string()),
    pa.field("file_types", pa.string()),              # JSON list: ["csharp", ".cs"]
    pa.field("tool_name", pa.string()),
    pa.field("execution_environment", pa.string()),   # python|node|python+dotnet|python+node
    pa.field("install_cmd", pa.string()),
    pa.field("extraction_script", pa.large_string()),
    pa.field("chunk_types", pa.string()),             # JSON list
    pa.field("edge_types", pa.string()),              # JSON list
    pa.field("limitations", pa.string()),             # JSON list
    pa.field("application_role", pa.large_string()),  # query-time weighting guidance
    pa.field("summarisation_instructions", pa.large_string()),  # per-chunk summarisation prompts
    pa.field("handbook", pa.large_string()),          # brief plain-English description
    pa.field("created_at", pa.timestamp("us", tz="UTC")),
    pa.field("version", pa.int32()),
])
