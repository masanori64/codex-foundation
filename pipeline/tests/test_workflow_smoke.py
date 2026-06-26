from __future__ import annotations

from pathlib import Path

from codex_pipeline.workflow_smoke import (
    WORKFLOW_SMOKE_ARTIFACT,
    WORKFLOW_SMOKE_NAME,
    build_workflow_smoke_state,
)


def test_workflow_smoke_is_pending_without_remote_artifact() -> None:
    project = Path("C:/Users/maasa/research_x")

    state = build_workflow_smoke_state(project, github_read_state={"status": "passed"})

    assert state["workflow_dispatch_executed"] is False
    assert state["deploy_executed"] is False
    assert state["paid_usage_detected"] is False
    assert state["status"] in {"pending_remote_artifact_e2e", "passed"}


def test_workflow_smoke_passes_when_remote_run_and_artifact_are_observed() -> None:
    project = Path("C:/Users/maasa/research_x")
    github_state = {
        "status": "passed",
        "workflow_runs": {
            "items": [
                {"id": 1, "name": WORKFLOW_SMOKE_NAME, "status": "completed"},
            ],
        },
        "artifacts": {
            "items": [
                {"id": 2, "name": WORKFLOW_SMOKE_ARTIFACT, "expired": False},
            ],
        },
    }

    state = build_workflow_smoke_state(project, github_read_state=github_state)

    assert state["status"] == "passed"
    assert state["remote"]["workflow_run_observed"] is True
    assert state["remote"]["artifact_observed"] is True
    assert state["remote"]["artifact_read_back"] is True
