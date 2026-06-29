from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .foundation import control_marker


def build_staging_manifest(
    *,
    project_id: str,
    pages_health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="staging_manifest"),
        "project_id": project_id,
        "environment_name": "staging",
        "generated_at": datetime.now(UTC).isoformat(),
        "target_type": "safe_static_plan",
        "dry_run": True,
        "staging_deploy_executed": False,
        "live_url": None,
        "previous_known_good": {
            "resolved": False,
            "pointer": None,
            "strategy": "latest_successful_staging_pages_snapshot",
        },
        "health": {
            "status": "dry_run_plan",
            "checks": [
                {"name": "dashboard_html_exists", "status": "planned"},
                {"name": "dashboard_state_exists", "status": "planned"},
                {"name": "preview_manifest_exists", "status": "planned"},
                {"name": "not_evidence_notice", "status": "passed"},
                {"name": "staging_url_http_200", "status": "not_executed"},
            ],
        },
        "side_effects": {
            "provider_api_calls": False,
            "secrets_used": False,
            "github_api_calls": False,
            "pages_enabled": False,
            "repository_settings_changed": False,
            "environment_created": False,
            "staging_live_deploy": False,
            "production_deploy": False,
            "rollback_executed": False,
        },
        "required_gates_before_execution": [
            "secrets_credentials",
            "production_external_side_effect",
        ],
    }
