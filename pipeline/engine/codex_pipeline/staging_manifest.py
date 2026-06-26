from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .foundation import control_marker


def build_staging_manifest(
    *,
    project_id: str,
    pages_health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pages_health = pages_health or {}
    passed = pages_health.get("staging_static_cd_passed") is True
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="staging_manifest"),
        "project_id": project_id,
        "environment_name": "staging",
        "generated_at": datetime.now(UTC).isoformat(),
        "target_type": "static_pages_lane",
        "dry_run": False,
        "staging_deploy_executed": passed,
        "live_url": pages_health.get("url_map", {}).get("staging"),
        "previous_known_good": {
            "resolved": passed,
            "pointer": pages_health.get("url_map", {}).get("staging") if passed else None,
            "strategy": "latest_successful_staging_pages_snapshot",
        },
        "health": {
            "status": "passed" if passed else "pending_pages_deploy",
            "checks": [
                {"name": "dashboard_html_exists", "status": "passed" if passed else "planned"},
                {"name": "dashboard_state_exists", "status": "passed" if passed else "planned"},
                {"name": "preview_manifest_exists", "status": "passed" if passed else "planned"},
                {"name": "not_evidence_notice", "status": "passed" if passed else "planned"},
                {"name": "staging_url_http_200", "status": "passed" if passed else "pending"},
            ],
        },
        "side_effects": {
            "provider_api_calls": False,
            "secrets_used": False,
            "github_api_calls": False,
            "pages_enabled": pages_health.get("pages_enabled") is True,
            "repository_settings_changed": False,
            "environment_created": False,
            "staging_live_deploy": passed,
            "production_deploy": False,
            "rollback_executed": False,
        },
        "required_gates_before_execution": [
            "secrets_credentials",
            "production_external_side_effect",
        ],
    }
