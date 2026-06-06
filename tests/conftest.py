"""Pytest configuration for ATLAS-SAGE.

Model config comes from env vars (same source as the CLI — no separate preset system).
Set ATLAS_ORCHESTRATOR_MODEL and ATLAS_SKILL_MODEL in your .env before running tests.

Run with -s to see orchestrator tool traces (INFO logs).
"""

from __future__ import annotations

import logging


def pytest_configure(config):
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("atlas_sage").setLevel(logging.INFO)
