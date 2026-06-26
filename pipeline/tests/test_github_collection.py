from __future__ import annotations

from pathlib import Path

from codex_pipeline.bridge_loader import load_project_bridge
from codex_pipeline.github_collection import (
    available_mutation_methods,
    build_github_collection_state,
)


def test_github_collection_uses_public_read_without_mutation_methods() -> None:
    bridge = load_project_bridge(Path("C:/Users/maasa/research_x"))

    state = build_github_collection_state(bridge)

    assert state["collection_mode"] == "public_read_state_available"
    assert state["status"] == "public_read_enabled"
    assert state["api_calls_executed"] is False
    assert state["token_used"] is False
    assert state["write_operations_available"] is False
    assert state["mutation_methods_available"] == []


def test_github_collection_exposes_no_mutation_methods() -> None:
    assert available_mutation_methods() == []
