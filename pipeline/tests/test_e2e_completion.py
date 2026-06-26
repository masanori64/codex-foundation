from __future__ import annotations

from pathlib import Path

from codex_pipeline.e2e_completion import build_e2e_completion_manifest
from codex_pipeline.profile_loader import load_project_profile


def test_e2e_completion_is_pending_without_remote_artifact(codex_project: Path) -> None:
    profile = load_project_profile(codex_project)

    state = build_e2e_completion_manifest(
        profile,
        cost_guard=_cost_guard(),
        github_read_state={"status": "passed"},
        workflow_smoke={"status": "pending_remote_artifact_e2e", "remote": {}},
        workflow_artifact_audit=_workflow_audit(),
        subagent_runtime_dry_run=_subagent_dry_run(),
    )

    assert state["local_control_plane_complete"] is True
    assert state["remote_artifact_workflow_executed"] is False
    assert state["final_automatic_pipeline_status"] == "pending_remote_artifact_e2e"
    assert state["deploy_executed"] is False
    assert state["paid_usage_detected"] is False


def test_e2e_completion_passes_with_remote_artifact_loop(codex_project: Path) -> None:
    profile = load_project_profile(codex_project)

    state = build_e2e_completion_manifest(
        profile,
        cost_guard=_cost_guard(),
        github_read_state={"status": "passed"},
        workflow_smoke={
            "status": "passed",
            "remote": {
                "workflow_run_observed": True,
                "artifact_observed": True,
                "artifact_read_back": True,
            },
        },
        workflow_artifact_audit=_workflow_audit(),
        subagent_runtime_dry_run=_subagent_dry_run(),
    )

    assert state["remote_artifact_workflow_executed"] is True
    assert state["remote_artifact_created"] is True
    assert state["remote_artifact_read_back"] is True
    assert state["dashboard_refreshed_after_read_back"] is True
    assert state["intermediate_smoke_status"] == "complete_artifact_only_no_cost"
    assert state["final_automatic_pipeline_status"] == "pending_static_pages_cd"


def test_e2e_completion_passes_with_static_pages_cd_and_rollback(
    codex_project: Path,
) -> None:
    profile = load_project_profile(codex_project)

    state = build_e2e_completion_manifest(
        profile,
        cost_guard=_cost_guard(),
        github_read_state={"status": "passed"},
        workflow_smoke={
            "status": "passed",
            "remote": {
                "workflow_run_observed": True,
                "artifact_observed": True,
                "artifact_read_back": True,
            },
        },
        workflow_artifact_audit=_workflow_audit(),
        subagent_runtime_dry_run=_subagent_dry_run(),
        pages_health={
            "pages_health_check_passed": True,
            "dashboard_pages_cd_passed": True,
            "preview_static_cd_passed": True,
            "staging_static_cd_passed": True,
            "production_static_cd_passed": True,
            "pages_enabled": True,
            "pages_url_observed": True,
        },
        pages_rollback_manifest={
            "rollback_executed": True,
            "health": {"status": "passed"},
            "refused_rollback_classes": [
                "destructive_action",
                "db_restore",
                "provider_api_quota",
                "secrets_credentials",
                "external_cloud_deploy",
            ],
        },
    )

    assert state["final_automatic_pipeline_status"] == "complete_static_pages_cd_no_cost"
    assert state["completion"]["active_completion_blockers"] == []
    assert state["completion"]["free_static_pages_cd_complete"] is True
    assert state["github_pages_enabled"] is True
    assert state["safe_static_pages_rollback_executed"] is True
    assert state["safe_static_rollback_execution_passed"] is True
    assert state["dangerous_rollback_classes_refused"] is True


def _cost_guard() -> dict:
    return {
        "cost_policy": {
            "pipeline_contains_paid_execution": False,
            "paid_usage_detected": False,
        },
    }


def _workflow_audit() -> dict:
    return {
        "status": "passed",
        "deploy_executed": False,
        "paid_usage_detected": False,
    }


def _subagent_dry_run() -> dict:
    return {
        "status": "passed",
        "subagents_spawned": False,
        "model_runner_started": False,
    }
