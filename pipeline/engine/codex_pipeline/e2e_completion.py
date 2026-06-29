from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from .bridge_loader import ProjectBridge
from .foundation import control_marker
from .profile_loader import ProjectProfile


def build_e2e_completion_manifest(
    profile: ProjectProfile,
    *,
    cost_guard: dict[str, Any],
    github_read_state: dict[str, Any],
    workflow_smoke: dict[str, Any],
    workflow_artifact_audit: dict[str, Any],
    subagent_runtime_dry_run: dict[str, Any],
    pages_readiness: dict[str, Any] | None = None,
    pages_health: dict[str, Any] | None = None,
    pages_rollback_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pages_readiness = pages_readiness or {}
    pages_health = pages_health or {}
    pages_rollback_manifest = pages_rollback_manifest or {}
    local_complete = _local_control_plane_complete(
        cost_guard=cost_guard,
        workflow_artifact_audit=workflow_artifact_audit,
        subagent_runtime_dry_run=subagent_runtime_dry_run,
    )
    remote = workflow_smoke.get("remote", {})
    remote_workflow = remote.get("workflow_run_observed") is True
    remote_artifact = remote.get("artifact_observed") is True
    remote_read_back = (
        github_read_state.get("status") == "passed"
        and remote.get("artifact_read_back") is True
    )
    dashboard_refreshed = (
        local_complete
        and remote_workflow
        and remote_artifact
        and remote_read_back
    )
    pages_complete = _static_pages_cd_complete(
        pages_health=pages_health,
        pages_rollback_manifest=pages_rollback_manifest,
    )
    if pages_complete:
        final_status = "complete_static_pages_cd_no_cost"
    elif dashboard_refreshed:
        final_status = "pending_static_pages_cd"
    else:
        final_status = "pending_remote_artifact_e2e"
    intermediate_smoke_status = (
        "complete_artifact_only_no_cost" if dashboard_refreshed else "pending"
    )
    safe_static_pages_rollback_executed = (
        pages_rollback_manifest.get("rollback_executed") is True
    )
    dangerous_rollback_classes_refused = _dangerous_rollback_classes_refused(
        pages_rollback_manifest,
    )
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="e2e_completion_manifest"),
        "generated_at": datetime.now(UTC).isoformat(),
        "project_id": profile.project_id,
        "completion": {
            "final_automatic_pipeline_status": final_status,
            "free_static_pages_cd_complete": final_status
            == "complete_static_pages_cd_no_cost",
            "active_completion_blockers": [],
            "intermediate_smoke_status": intermediate_smoke_status,
        },
        "completed_free_capabilities": {
            "public_repo_standard_github_actions": remote_workflow,
            "github_pages_static_deploy": pages_health.get("pages_enabled") is True,
            "dashboard_static_cd": pages_health.get("dashboard_pages_cd_passed") is True,
            "preview_static_cd": pages_health.get("preview_static_cd_passed") is True,
            "staging_static_cd": pages_health.get("staging_static_cd_passed") is True,
            "production_static_cd": pages_health.get("production_static_cd_passed") is True,
            "safe_static_pages_rollback": safe_static_pages_rollback_executed,
            "pages_url_readback": pages_health.get("pages_url_observed") is True,
        },
        "active_completion_blockers": [],
        "local_control_plane_complete": local_complete,
        "remote_artifact_workflow_executed": remote_workflow,
        "remote_artifact_created": remote_artifact,
        "remote_artifact_read_back": remote_read_back,
        "dashboard_refreshed_after_read_back": dashboard_refreshed,
        "workflow_smoke_status": workflow_smoke.get("status", "unknown"),
        "workflow_artifact_audit_status": workflow_artifact_audit.get("status", "unknown"),
        "subagent_runtime_dry_run_status": subagent_runtime_dry_run.get("status", "unknown"),
        "cost_guard_paid_execution": cost_guard.get("cost_policy", {}).get(
            "pipeline_contains_paid_execution",
            None,
        ),
        "intermediate_smoke_status": intermediate_smoke_status,
        "github_pages_enabled": pages_health.get("pages_enabled") is True,
        "pages_deploy_executed": pages_health.get("pages_health_check_passed") is True,
        "pages_url_observed": pages_health.get("pages_url_observed") is True,
        "pages_health_check_passed": pages_health.get("pages_health_check_passed") is True,
        "preview_static_cd_passed": pages_health.get("preview_static_cd_passed") is True,
        "staging_static_cd_passed": pages_health.get("staging_static_cd_passed") is True,
        "production_static_cd_passed": pages_health.get("production_static_cd_passed") is True,
        "safe_static_rollback_drill_passed": (
            pages_rollback_manifest.get("health", {}).get("status")
            in {"pending", "passed"}
        ),
        "safe_static_rollback_execution_passed": (
            safe_static_pages_rollback_executed
            and pages_rollback_manifest.get("health", {}).get("status") == "passed"
        ),
        "safe_static_pages_rollback_executed": safe_static_pages_rollback_executed,
        "dangerous_rollback_classes_refused": dangerous_rollback_classes_refused,
        "pages_readiness_status": pages_readiness.get("status", "not_checked"),
        "deploy_executed": False,
        "rollback_executed": False,
        "pages_enabled": False,
        "repository_settings_changed": False,
        "secrets_used": False,
        "pat_used": False,
        "deploy_key_used": False,
        "external_cloud_used": False,
        "db_migration_executed": False,
        "research_evidence_written": False,
        "provider_quota_used": False,
        "paid_usage_detected": False,
        "final_automatic_pipeline_status": final_status,
    }


def write_e2e_completion_manifest(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    state: dict[str, Any],
) -> None:
    paths = [
        profile.project_root / bridge.dashboard_dir / "data" / "e2e-completion-manifest.json",
        profile.project_root / bridge.generated_dir / "effective-e2e-completion-manifest.json",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, state)


def _local_control_plane_complete(
    *,
    cost_guard: dict[str, Any],
    workflow_artifact_audit: dict[str, Any],
    subagent_runtime_dry_run: dict[str, Any],
) -> bool:
    cost_policy = cost_guard.get("cost_policy", {})
    return (
        cost_policy.get("pipeline_contains_paid_execution") is False
        and cost_policy.get("paid_usage_detected") is False
        and workflow_artifact_audit.get("status") == "passed"
        and workflow_artifact_audit.get("deploy_executed") is False
        and workflow_artifact_audit.get("paid_usage_detected") is False
        and subagent_runtime_dry_run.get("status") == "passed"
        and subagent_runtime_dry_run.get("subagents_spawned") is False
        and subagent_runtime_dry_run.get("model_runner_started") is False
    )


def _static_pages_cd_complete(
    *,
    pages_health: dict[str, Any],
    pages_rollback_manifest: dict[str, Any],
) -> bool:
    return (
        pages_health.get("pages_health_check_passed") is True
        and pages_health.get("dashboard_pages_cd_passed") is True
        and pages_health.get("preview_static_cd_passed") is True
        and pages_health.get("staging_static_cd_passed") is True
        and pages_health.get("production_static_cd_passed") is True
        and pages_rollback_manifest.get("rollback_executed") is True
        and pages_rollback_manifest.get("health", {}).get("status") == "passed"
    )


def _dangerous_rollback_classes_refused(
    pages_rollback_manifest: dict[str, Any],
) -> bool:
    refused = pages_rollback_manifest.get("refused_rollback_classes", [])
    if not isinstance(refused, list):
        return False
    required = {
        "destructive_action",
        "db_restore",
        "provider_api_quota",
        "secrets_credentials",
        "external_cloud_deploy",
    }
    return required.issubset({str(item) for item in refused})


def _write_json(path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
