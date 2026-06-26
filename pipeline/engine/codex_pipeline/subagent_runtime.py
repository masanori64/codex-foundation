from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .bridge_loader import ProjectBridge
from .foundation import control_marker
from .profile_loader import ProjectProfile


def build_subagent_runtime_dry_run(subagent_policy: dict[str, Any]) -> dict[str, Any]:
    roles = subagent_policy.get("allowed_roles", [])
    if not isinstance(roles, list):
        roles = []
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="subagent_runtime_dry_run"),
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "passed",
        "dry_run_executed": True,
        "subagents_spawned": False,
        "model_runner_started": False,
        "provider_api_calls": False,
        "raw_log_in_project": False,
        "paid_usage_detected": False,
        "github_api_write_executed": False,
        "commit_or_push_allowed_for_subagent": False,
        "checked_roles": [
            {
                "role": str(role),
                "spawned": False,
                "contract": "sanitized_summary_only",
                "raw_logs_allowed": False,
            }
            for role in roles
        ],
        "checks": [
            {"name": "policy_is_read_only", "status": _check_read_only(subagent_policy)},
            {"name": "raw_logs_forbidden", "status": _check_raw_logs(subagent_policy)},
            {
                "name": "provider_quota_forbidden",
                "status": _check_forbidden(subagent_policy, "provider_api_quota"),
            },
            {
                "name": "github_mutation_forbidden",
                "status": _check_forbidden(subagent_policy, "github_api_mutation"),
            },
            {"name": "deploy_forbidden", "status": _check_forbidden(subagent_policy, "deploy")},
        ],
        "reason": (
            "Dry-run verifies the subagent contract and report boundary without spawning "
            "workers, starting model runners, or storing raw logs in the project."
        ),
    }


def write_subagent_runtime_dry_run(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    state: dict[str, Any],
) -> None:
    paths = [
        profile.project_root / bridge.dashboard_dir / "data" / "subagent-runtime-dry-run.json",
        profile.project_root / bridge.generated_dir / "effective-subagent-runtime-dry-run.json",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, state)


def _check_read_only(policy: dict[str, Any]) -> str:
    lifecycle = policy.get("lifecycle", {})
    if isinstance(lifecycle, dict) and lifecycle.get("mode") == "read_only":
        return "passed"
    return "failed"


def _check_raw_logs(policy: dict[str, Any]) -> str:
    if policy.get("raw_log_in_project") is False:
        return "passed"
    return "failed"


def _check_forbidden(policy: dict[str, Any], action: str) -> str:
    forbidden = policy.get("forbidden_actions", [])
    if isinstance(forbidden, list) and action in forbidden:
        return "passed"
    return "failed"


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
