from __future__ import annotations

from typing import Any

from .foundation import control_marker

DEFAULT_ALLOWED_ROLES = [
    "impact_mapper",
    "pr_reviewer",
    "ci_log_auditor",
    "release_auditor",
]


def build_subagent_policy(*, allowed_roles: list[str]) -> dict[str, Any]:
    roles = allowed_roles or DEFAULT_ALLOWED_ROLES
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="subagent_policy"),
        "owner": "Codex foundation",
        "raw_log_in_project": False,
        "allowed_roles": roles,
        "lifecycle": {
            "mode": "read_only",
            "spawned_by_default": False,
            "short_lived": True,
            "parent_integrates_outputs": True,
        },
        "summary_contract": {
            "schema": "schema/subagent-report.schema.json",
            "raw_logs_allowed": False,
            "sanitized_summary_required": True,
            "control_artifact": True,
            "not_evidence": True,
            "not_citation": True,
        },
        "forbidden_actions": [
            "commit",
            "push",
            "deploy",
            "rollback_execution",
            "github_api_mutation",
            "provider_api_quota",
            "secret_access",
            "mcp_plugin_hook_enablement",
            "destructive_action",
            "create_project_evidence",
        ],
        "summaries": [],
    }
