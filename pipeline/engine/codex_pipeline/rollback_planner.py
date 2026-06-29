from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .foundation import control_marker


def build_rollback_manifest(
    *,
    project_id: str,
    environment: str = "production",
    pages_rollback_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="rollback_manifest"),
        "project_id": project_id,
        "environment": environment,
        "scope": "safe_static_artifacts_only",
        "dry_run": True,
        "rollback_executed": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "target": {
            "strategy": "previous_known_good_static_pages_snapshot",
            "resolved": False,
            "selection_mode": "safe_static_pages",
            "artifact_pointer": "docs/control/codex/dashboard/index.html",
            "reason": (
                "Rollback is restricted to static Pages control artifacts and refuses "
                "provider, secret, DB, destructive, and evidence paths."
            ),
        },
        "drill": {
            "status": "dry_run_plan",
            "restore_executed": False,
            "would_restore_paths": [
                "docs/control/codex/dashboard/",
                ".codex-project/generated/",
            ],
            "health": {
                "status": "planned",
                "checks": [
                    {"name": "static_artifact_exists", "status": "planned"},
                    {"name": "not_evidence_notice", "status": "passed"},
                    {"name": "no_database_restore", "status": "passed"},
                ],
            },
        },
        "side_effects": {
            "provider_api_calls": False,
            "secrets_changed": False,
            "db_migration": False,
            "db_restore": False,
            "destructive_action": False,
            "files_mutated": False,
            "production_deploy": False,
            "rollback_execution": False,
        },
        "refused_rollback_classes": [
            "destructive_action",
            "db_restore",
            "provider_api_quota",
            "secrets_credentials",
            "external_cloud_deploy",
            "research_evidence_write",
        ],
        "blocked_execution_gates": [
            "production_external_side_effect",
            "secrets_credentials",
            "destructive_action",
            "irreversible_db_migration",
            "repository_settings_change",
        ],
    }
