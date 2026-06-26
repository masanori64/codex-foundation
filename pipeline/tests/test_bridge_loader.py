from __future__ import annotations

from pathlib import Path

from codex_pipeline.bridge_loader import load_project_bridge, validate_project_bridge


def test_loads_research_x_bridge_with_public_read_pages_cd() -> None:
    bridge = load_project_bridge(Path("C:/Users/maasa/research_x"))

    assert bridge.project_id == "research_x"
    assert bridge.data["github"]["api_enabled"] == "public_read"
    assert bridge.data["capabilities"]["production_cd"] == "static_pages_enabled"
    assert str(bridge.dashboard_dir).replace("\\", "/") == "docs/control/codex/dashboard"


def test_bridge_rejects_github_api_in_phase_1() -> None:
    data = {
        "schema_version": 1,
        "project_id": "demo",
        "codex_foundation": "C:/Users/maasa/.codex",
        "github": {"mode": "local_only", "api_enabled": True},
        "outputs": {
            "dashboard_dir": "docs/control/codex/dashboard",
            "generated_dir": ".codex-project/generated",
            "mermaid_dir": "docs/control/codex/dashboard/mermaid",
        },
    }

    errors = validate_project_bridge(data)

    assert "bridge: GitHub API must be false or public_read" in errors
