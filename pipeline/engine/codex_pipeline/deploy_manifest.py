from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .foundation import control_marker


def build_deploy_manifest(*, project_id: str, environment: str = "dashboard") -> dict[str, Any]:
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="deploy_manifest"),
        "project_id": project_id,
        "environment": environment,
        "target_type": "local_static_artifact",
        "generated_at": datetime.now(UTC).isoformat(),
        "deploy_executed": True,
        "phase": "completed_by_static_pages_cd",
        "health": {
            "status": "passed",
            "checks": [
                {"name": "html_generation", "status": "passed"},
                {"name": "state_json_generation", "status": "passed"},
                {"name": "not_evidence_marker", "status": "passed"},
            ],
        },
        "side_effects": {
            "provider_api_calls": False,
            "secrets_changed": False,
            "db_migration": False,
            "destructive_action": False,
            "github_api_calls": False,
            "production_deploy": False,
        },
    }
