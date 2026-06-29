from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .foundation import control_marker


def build_preview_manifest(
    *,
    project_id: str,
    pages_health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="preview_manifest"),
        "project_id": project_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "target_type": "artifact_only",
        "preview_executed": False,
        "live_url": None,
        "artifact_name": "codex-preview-artifact",
        "smoke": {
            "status": "artifact_only_plan",
            "checks": [
                {"name": "dashboard_html_exists", "status": "planned"},
                {"name": "dashboard_state_exists", "status": "planned"},
                {"name": "not_evidence_notice", "status": "passed"},
                {"name": "preview_url_http_200", "status": "not_executed"},
            ],
        },
        "side_effects": {
            "provider_api_calls": False,
            "secrets_used": False,
            "github_api_calls": False,
            "pages_enabled": False,
            "repository_settings_changed": False,
            "preview_live_deploy": False,
            "staging_deploy": False,
            "production_deploy": False,
            "rollback_executed": False,
        },
        "fallback_policy": {
            "fork_pull_request": "artifact_only",
            "same_repo_branch": "static_pages_lane",
        },
        "blocked_execution_gates": [
            "secrets_credentials",
            "production_external_side_effect",
        ],
    }
