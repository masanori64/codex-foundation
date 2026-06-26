from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .bridge_loader import ProjectBridge
from .foundation import control_marker
from .profile_loader import ProjectProfile
from .workflow_wrappers import WORKFLOW_DIR, WRAPPERS, validate_workflow_wrappers


def build_workflow_artifact_audit(
    project_root: Path,
    bridge: ProjectBridge,
    *,
    github_read_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    capabilities = bridge.data.get("capabilities", {})
    validation_errors = validate_workflow_wrappers(
        project_root,
        capability_status=str(capabilities.get("github_actions_wrappers", "")),
        dashboard_artifact_status=str(capabilities.get("dashboard_artifact_cd", "")),
    )
    workflow_files = []
    for output_name in WRAPPERS:
        path = project_root / WORKFLOW_DIR / output_name
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        workflow_files.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "artifact_upload": "actions/upload-artifact@v4" in text,
                "permissions_contents_read": "permissions:\n  contents: read" in text,
                "workflow_dispatch_declared": "\n  workflow_dispatch:" in text,
                "pull_request_declared": "\n  pull_request:" in text,
                "push_declared": "\n  push:" in text,
                "forbidden_live_deploy_markers": [
                    marker
                    for marker in (
                        "pages: write",
                        "id-token: write",
                        "deployments: write",
                        "environment:",
                        "gh api",
                        "curl https://api.github.com",
                        "secrets.",
                    )
                    if marker.casefold() in text.casefold()
                ],
            }
        )
    remote_artifacts = _remote_artifact_summary(github_read_state)
    status = "passed" if not validation_errors else "failed"
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="workflow_artifact_audit"),
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "artifact_only_static_smoke": status == "passed",
        "validation_errors": validation_errors,
        "workflow_dispatch_executed": False,
        "github_actions_minutes_consumed_by_this_smoke": False,
        "github_actions_artifact_storage_created_by_this_smoke": False,
        "github_api_write_executed": False,
        "deploy_executed": False,
        "pages_enabled": False,
        "repository_settings_changed": False,
        "secrets_used": False,
        "paid_usage_detected": False,
        "reason": (
            "This smoke validates artifact-only workflow wrappers locally and reads "
            "existing remote artifact metadata when available. It does not dispatch a workflow."
        ),
        "workflow_files": workflow_files,
        "remote_artifacts": remote_artifacts,
    }


def write_workflow_artifact_audit(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    state: dict[str, Any],
) -> None:
    paths = [
        profile.project_root / bridge.dashboard_dir / "data" / "workflow-artifact-audit.json",
        profile.project_root / bridge.generated_dir / "effective-workflow-artifact-audit.json",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, state)


def _remote_artifact_summary(github_read_state: dict[str, Any] | None) -> dict[str, Any]:
    if not github_read_state:
        return {"status": "not_collected", "total_count": None, "items": []}
    artifacts = github_read_state.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return {"status": "unavailable", "total_count": None, "items": []}
    return {
        "status": github_read_state.get("status", "unknown"),
        "total_count": artifacts.get("total_count"),
        "sample_count": artifacts.get("sample_count", 0),
        "items": artifacts.get("items", []),
        "artifact_only_smoke_present": any(
            item.get("name") == "codex-artifact-smoke"
            for item in artifacts.get("items", [])
            if isinstance(item, dict)
        ),
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
