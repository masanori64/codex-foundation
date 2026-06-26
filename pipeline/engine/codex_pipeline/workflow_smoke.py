from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .bridge_loader import ProjectBridge
from .foundation import control_marker
from .profile_loader import ProjectProfile

WORKFLOW_SMOKE_FILE = "codex-artifact-smoke.yml"
WORKFLOW_SMOKE_NAME = "Codex Artifact Smoke"
WORKFLOW_SMOKE_ARTIFACT = "codex-artifact-smoke"


def build_workflow_smoke_state(
    project_root: Path,
    *,
    github_read_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workflow_path = project_root / ".github" / "workflows" / WORKFLOW_SMOKE_FILE
    text = workflow_path.read_text(encoding="utf-8") if workflow_path.exists() else ""
    static_checks = _static_checks(workflow_path, text)
    remote = _remote_smoke_summary(github_read_state)
    status = _status(static_checks, remote)
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="workflow_smoke"),
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "workflow_file": str(workflow_path),
        "workflow_name": WORKFLOW_SMOKE_NAME,
        "artifact_name": WORKFLOW_SMOKE_ARTIFACT,
        "trigger_policy": {
            "push_enabled": "\n  push:" in text,
            "pull_request_enabled": "\n  pull_request:" in text,
            "workflow_dispatch_enabled": "\n  workflow_dispatch:" in text,
            "workflow_dispatch_executed_by_codex": False,
        },
        "static_checks": static_checks,
        "remote": remote,
        "github_api_write_executed": False,
        "workflow_dispatch_executed": False,
        "deploy_executed": False,
        "rollback_executed": False,
        "pages_enabled": False,
        "repository_settings_changed": False,
        "secrets_used": False,
        "provider_api_calls": False,
        "paid_usage_detected": False,
        "reason": _reason(status),
    }


def write_workflow_smoke_artifacts(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    state: dict[str, Any],
) -> None:
    paths = [
        profile.project_root / bridge.dashboard_dir / "data" / "workflow-smoke.json",
        profile.project_root / bridge.generated_dir / "effective-workflow-smoke.json",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, state)


def _static_checks(path: Path, text: str) -> list[dict[str, Any]]:
    checks = [
        ("workflow_file_exists", path.exists()),
        ("control_marker_present", "control_artifact=true" in text),
        ("top_level_contents_read", "permissions:\n  contents: read" in text),
        ("job_contents_read", "permissions:\n      contents: read" in text),
        ("push_trigger_present", "\n  push:" in text),
        ("pull_request_trigger_present", "\n  pull_request:" in text),
        ("workflow_dispatch_absent", "\n  workflow_dispatch:" not in text),
        ("artifact_upload_present", "actions/upload-artifact@v4" in text),
        ("no_pages_write", "pages: write" not in text.casefold()),
        ("no_id_token_write", "id-token: write" not in text.casefold()),
        ("no_deployments_write", "deployments: write" not in text.casefold()),
        ("no_secrets_context", "secrets." not in text.casefold()),
        ("no_environment", "environment:" not in text.casefold()),
        ("no_github_api_write", "gh api" not in text.casefold()),
        ("no_api_curl", "curl https://api.github.com" not in text.casefold()),
    ]
    return [
        {"name": name, "status": "passed" if passed else "failed"}
        for name, passed in checks
    ]


def _remote_smoke_summary(github_read_state: dict[str, Any] | None) -> dict[str, Any]:
    runs = _items(github_read_state, "workflow_runs")
    artifacts = _items(github_read_state, "artifacts")
    smoke_runs = [
        item
        for item in runs
        if item.get("name") in {WORKFLOW_SMOKE_NAME, WORKFLOW_SMOKE_FILE}
    ]
    smoke_artifacts = [
        item for item in artifacts if item.get("name") == WORKFLOW_SMOKE_ARTIFACT
    ]
    latest_run = smoke_runs[0] if smoke_runs else {}
    latest_artifact = smoke_artifacts[0] if smoke_artifacts else {}
    return {
        "github_read_status": _github_read_status(github_read_state),
        "workflow_run_observed": bool(smoke_runs),
        "artifact_observed": bool(smoke_artifacts),
        "artifact_read_back": bool(smoke_artifacts),
        "latest_run": latest_run,
        "latest_artifact": latest_artifact,
        "workflow_run_count_in_sample": len(smoke_runs),
        "artifact_count_in_sample": len(smoke_artifacts),
    }


def _items(github_read_state: dict[str, Any] | None, key: str) -> list[dict[str, Any]]:
    if not isinstance(github_read_state, dict):
        return []
    value = github_read_state.get(key, {})
    if not isinstance(value, dict):
        return []
    items = value.get("items", [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _github_read_status(github_read_state: dict[str, Any] | None) -> str:
    if isinstance(github_read_state, dict):
        return str(github_read_state.get("status", "unknown"))
    return "not_collected"


def _status(static_checks: list[dict[str, Any]], remote: dict[str, Any]) -> str:
    if any(check["status"] != "passed" for check in static_checks):
        return "failed_static_validation"
    if remote["workflow_run_observed"] and remote["artifact_observed"]:
        return "passed"
    return "pending_remote_artifact_e2e"


def _reason(status: str) -> str:
    if status == "passed":
        return "Artifact-only workflow has run remotely and the artifact metadata was read back."
    if status == "failed_static_validation":
        return "The artifact-only workflow file failed local static safety checks."
    return "The artifact-only workflow is locally valid but no remote artifact run is observed yet."


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
