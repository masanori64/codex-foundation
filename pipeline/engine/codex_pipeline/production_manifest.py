from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .foundation import control_marker


def build_production_manifest(
    *,
    project_id: str,
    pages_health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="production_manifest"),
        "project_id": project_id,
        "environment_name": "production",
        "generated_at": datetime.now(UTC).isoformat(),
        "target_type": "production_plan",
        "execution_enabled": False,
        "production_deploy_executed": False,
        "live_url": None,
        "kill_switch": {
            "capability": "production_cd",
            "status": "static_pages_enabled",
            "execution_default": "disabled_in_pr_control_artifact",
        },
        "health": {
            "status": "production_plan",
            "checks": [
                {"name": "staging_manifest_exists", "status": "planned"},
                {"name": "previous_known_good_available", "status": "planned"},
                {"name": "not_evidence_notice", "status": "passed"},
                {"name": "production_url_http_200", "status": "not_executed"},
            ],
        },
        "side_effects": {
            "provider_api_calls": False,
            "secrets_used": False,
            "github_api_calls": False,
            "pages_enabled": False,
            "repository_settings_changed": False,
            "environment_created": False,
            "staging_deploy": False,
            "production_live_deploy": False,
            "rollback_executed": False,
        },
        "required_gates_before_execution": [
            "secrets_credentials",
            "production_external_side_effect",
        ],
    }
