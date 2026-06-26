from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .foundation import control_marker


def build_production_manifest(
    *,
    project_id: str,
    pages_health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pages_health = pages_health or {}
    passed = pages_health.get("production_static_cd_passed") is True
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="production_manifest"),
        "project_id": project_id,
        "environment_name": "production",
        "generated_at": datetime.now(UTC).isoformat(),
        "target_type": "static_pages_production",
        "execution_enabled": True,
        "production_deploy_executed": passed,
        "live_url": pages_health.get("url_map", {}).get("production"),
        "kill_switch": {
            "capability": "production_cd",
            "status": "static_pages_enabled",
            "execution_default": "enabled_for_free_static_pages",
        },
        "health": {
            "status": "passed" if passed else "pending_pages_deploy",
            "checks": [
                {"name": "staging_manifest_exists", "status": "passed" if passed else "planned"},
                {
                    "name": "previous_known_good_available",
                    "status": "passed" if passed else "planned",
                },
                {"name": "not_evidence_notice", "status": "passed" if passed else "planned"},
                {"name": "production_url_http_200", "status": "passed" if passed else "pending"},
            ],
        },
        "side_effects": {
            "provider_api_calls": False,
            "secrets_used": False,
            "github_api_calls": False,
            "pages_enabled": pages_health.get("pages_enabled") is True,
            "repository_settings_changed": False,
            "environment_created": False,
            "staging_deploy": pages_health.get("staging_static_cd_passed") is True,
            "production_live_deploy": passed,
            "rollback_executed": False,
        },
        "required_gates_before_execution": [
            "secrets_credentials",
            "production_external_side_effect",
        ],
    }
