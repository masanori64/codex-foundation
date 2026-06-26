from __future__ import annotations

from typing import Any

from .bridge_loader import ProjectBridge
from .foundation import control_marker

READ_ONLY_METHODS = (
    "list_workflow_runs",
    "list_workflow_jobs",
    "list_workflow_artifacts",
    "get_pull_request_metadata",
    "get_commit_status",
)

FORBIDDEN_MUTATION_METHODS = (
    "create_issue",
    "create_pull_request",
    "update_repository_settings",
    "enable_pages",
    "create_deployment",
    "rerun_workflow",
    "cancel_workflow",
    "delete_artifact",
)


def build_github_collection_state(bridge: ProjectBridge) -> dict[str, Any]:
    github = bridge.data["github"]
    mode = str(github.get("mode", "local_only"))
    api_setting = github.get("api_enabled")
    api_enabled = api_setting is True or api_setting == "public_read"
    marker = control_marker(artifact_kind="github_state")
    state: dict[str, Any] = {
        "schema_version": 1,
        **marker,
        "repository": github.get("repository", ""),
        "default_branch": github.get("default_branch", ""),
        "mode": mode,
        "collection_mode": "disabled",
        "status": "disabled",
        "github_api_enabled": api_enabled,
        "github_api_mode": api_setting,
        "api_calls_executed": False,
        "token_used": False,
        "write_operations_available": False,
        "read_methods_available": list(READ_ONLY_METHODS),
        "mutation_methods_available": available_mutation_methods(),
        "forbidden_mutation_methods": list(FORBIDDEN_MUTATION_METHODS),
        "reason": "GitHub API collection is disabled by default.",
        "items": [],
    }
    if not api_enabled or mode == "local_only":
        return state
    if mode == "mock":
        state.update(
            {
                "collection_mode": "mock",
                "status": "mock",
                "reason": "Mock collection returns local control-plane fixtures only.",
            }
        )
        return state
    if mode == "read_only":
        state.update(
            {
                "collection_mode": "gated_read_only",
                "status": "requires_explicit_user_gate",
                "reason": "Read-only GitHub API collection requires an explicit current-task gate.",
            }
        )
        return state
    if mode == "public_repo_pages_static_cd":
        state.update(
            {
                "collection_mode": "public_read_state_available",
                "status": "public_read_enabled",
                "reason": (
                    "Public read-only GitHub collection is represented by "
                    "github_read_state; mutation methods remain unavailable."
                ),
            }
        )
        return state
    state.update(
        {
            "collection_mode": "unsupported",
            "status": "blocked",
            "reason": f"Unsupported GitHub collection mode: {mode}",
        }
    )
    return state


def available_mutation_methods() -> list[str]:
    return []
