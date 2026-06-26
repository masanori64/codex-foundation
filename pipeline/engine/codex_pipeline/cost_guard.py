from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .bridge_loader import ProjectBridge
from .foundation import control_marker
from .profile_loader import ProjectProfile


def build_cost_guard_state(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    *,
    github_read_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    visibility = _github_visibility(github_read_state)
    actions_dispatch_status = _actions_dispatch_status(visibility)
    paid_or_quota_lanes = [
        "provider_api_quota",
        "paid_cloud",
        "model_runner",
    ]
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="cost_guard"),
        "generated_at": datetime.now(UTC).isoformat(),
        "project_id": profile.project_id,
        "repository": {
            "bridge_repository": bridge.data["github"].get("repository", ""),
            "observed_repository": _observed_repository(github_read_state),
            "visibility": visibility,
        },
        "cost_policy": {
            "paid_usage_detected": False,
            "pipeline_contains_paid_execution": False,
            "free_tier_quota_consumption_allowed": False,
            "provider_api_quota_allowed": False,
            "secrets_or_pat_allowed": False,
            "static_pages_deploy_allowed": visibility == "public",
            "safe_static_rollback_allowed": visibility == "public",
            "repository_settings_change_allowed": visibility == "public",
            "repository_settings_change_scope": "free_pages_source_setup_only",
            "install_allowed_when_no_paid_quota": True,
            "mcp_plugin_hook_allowed": False,
            "db_migration_allowed": False,
        },
        "allowed_no_cost_actions": [
            {
                "action_id": "local_static_validation",
                "status": "allowed",
                "cost_class": "local_only",
                "reason": "Runs on this machine only and does not call providers.",
            },
            {
                "action_id": "github_rest_public_read_unauthenticated",
                "status": "allowed_when_public_data_is_accessible",
                "cost_class": "rate_limit_only",
                "reason": "Uses unauthenticated GET requests for public repository metadata only.",
            },
            {
                "action_id": "github_actions_artifact_static_audit",
                "status": "allowed",
                "cost_class": "local_only",
                "reason": "Validates committed workflow wrappers without dispatching a run.",
            },
            {
                "action_id": "github_actions_artifact_push_smoke_public_repo",
                "status": _actions_push_smoke_status(visibility),
                "cost_class": "public_repo_standard_runner",
                "reason": _actions_push_smoke_reason(visibility),
            },
            {
                "action_id": "github_actions_workflow_dispatch_public_repo",
                "status": actions_dispatch_status,
                "cost_class": "public_repo_standard_runner",
                "reason": _actions_dispatch_reason(visibility),
            },
            {
                "action_id": "github_pages_public_repo_static_cd",
                "status": _pages_static_status(visibility),
                "cost_class": "github_free_public_repo_pages",
                "reason": _pages_static_reason(visibility),
            },
            {
                "action_id": "pages_static_preview_staging_production_lanes",
                "status": _pages_static_status(visibility),
                "cost_class": "github_free_public_repo_pages",
                "reason": (
                    "Path-based preview/staging/production lanes use the same public "
                    "GitHub Pages project site."
                ),
            },
            {
                "action_id": "safe_static_pages_rollback",
                "status": _pages_static_status(visibility),
                "cost_class": "github_free_public_repo_pages",
                "reason": (
                    "Rollback redeploys a previous static Pages snapshot and does not "
                    "touch providers, DBs, or secrets."
                ),
            },
            {
                "action_id": "subagent_runtime_dry_run",
                "status": "allowed",
                "cost_class": "local_only",
                "reason": "Checks the subagent contract without spawning workers or model runners.",
            },
        ],
        "allowed_no_cost_smokes": [
            "local_static_validation",
            "github_rest_public_read_unauthenticated",
            "github_actions_artifact_static_audit",
            "github_actions_artifact_push_smoke_public_repo",
            "subagent_runtime_dry_run",
        ],
        "paid_or_quota_lanes_present": paid_or_quota_lanes,
        "active_completion_blockers": [],
        "hard_blocked_paid": [
            {
                "action_id": "paid_provider_api_quota",
                "status": "hard_blocked_paid",
                "cost_class": "paid_or_quota_provider",
                "reason": (
                    "Paid or quota-consuming provider/API use is outside the completed "
                    "free static Pages CD pipeline."
                ),
            },
            {
                "action_id": "paid_cloud",
                "status": "hard_blocked_paid",
                "cost_class": "paid_cloud",
                "reason": "Paid cloud deploys are not part of the free GitHub Pages CD path.",
            },
            {
                "action_id": "paid_model_runner",
                "status": "hard_blocked_paid",
                "cost_class": "paid_or_quota_model_runner",
                "reason": "Model runners can consume paid/quota resources and are not used here.",
            },
        ],
        "not_used_outside_free_static_pages_cd": [
            {
                "action_id": "secrets_pat_deploy_key_environment_secret",
                "status": "not_used_outside_free_static_pages_cd",
                "cost_class": "credential_gate",
                "reason": (
                    "The completed free static Pages CD pipeline does not require secrets, "
                    "PATs, deploy keys, or environment secrets."
                ),
            },
            {
                "action_id": "db_migration",
                "status": "not_used_outside_free_static_pages_cd",
                "cost_class": "stateful_data_change",
                "reason": (
                    "Static Pages CD publishes control artifacts and performs no "
                    "DB migration."
                ),
            },
            {
                "action_id": "destructive_action",
                "status": "not_used_outside_free_static_pages_cd",
                "cost_class": "destructive_state_change",
                "reason": "Static Pages CD does not require destructive or irreversible actions.",
            },
            {
                "action_id": "external_cloud_deploy",
                "status": "not_used_outside_free_static_pages_cd",
                "cost_class": "external_cloud",
                "reason": "The deployment target is GitHub Pages, not an external cloud service.",
            },
            {
                "action_id": "mcp_plugin_hook_changes",
                "status": "outside_scope_for_this_pipeline",
                "cost_class": "external_or_stateful_setup",
                "reason": (
                    "MCP, plugin, and hook configuration changes are not required by the "
                    "completed free static Pages CD pipeline."
                ),
            },
        ],
        "answer": {
            "has_paid_execution_in_current_pipeline": False,
            "has_billing_sensitive_plan_lanes": False,
            "plain_language": (
                "The free static Pages CD pipeline is complete. It used public GitHub "
                "Actions standard runners and GitHub Pages, and it did not use paid "
                "provider quota, secrets, external cloud deploys, model runners, or DB "
                "migrations. Paid/quota provider paths remain hard blocked; secrets, DB, "
                "destructive, external-cloud, MCP, plugin, and hook paths are not used "
                "and outside this pipeline, not active completion blockers."
            ),
        },
    }


def _github_visibility(github_read_state: dict[str, Any] | None) -> str:
    if not github_read_state:
        return "unknown"
    repo = github_read_state.get("repo", {})
    if isinstance(repo, dict):
        visibility = repo.get("visibility")
        if isinstance(visibility, str) and visibility:
            return visibility
        private = repo.get("private")
        if private is True:
            return "private"
        if private is False:
            return "public"
    return "unknown"


def _observed_repository(github_read_state: dict[str, Any] | None) -> str:
    if not github_read_state:
        return ""
    repo = github_read_state.get("repository", {})
    if isinstance(repo, dict):
        full_name = repo.get("full_name") or repo.get("selected")
        if isinstance(full_name, str):
            return full_name
    observed = github_read_state.get("observed_repository")
    return observed if isinstance(observed, str) else ""


def _actions_dispatch_status(visibility: str) -> str:
    if visibility == "public":
        return "not_executed_public_standard_runner_is_no_direct_charge_but_dispatch_is_write"
    if visibility == "private":
        return "blocked_private_repo_can_consume_included_or_billable_minutes_storage"
    return "blocked_until_repository_visibility_and_billing_are_known"


def _actions_push_smoke_status(visibility: str) -> str:
    if visibility == "public":
        return "allowed_public_standard_runner_artifact_only"
    if visibility == "private":
        return "blocked_private_repo_can_consume_included_or_billable_minutes_storage"
    return "blocked_until_repository_visibility_and_billing_are_known"


def _actions_dispatch_reason(visibility: str) -> str:
    if visibility == "public":
        return (
            "GitHub documents public-repository standard runner usage as no direct charge, "
            "but dispatching a workflow is still a GitHub write and creates Actions usage."
        )
    if visibility == "private":
        return "Private repositories can consume included minutes/storage and may become billable."
    return "Repository visibility or billing status was not proven by read-only collection."


def _actions_push_smoke_reason(visibility: str) -> str:
    if visibility == "public":
        return (
            "The repository is public and the workflow is restricted to standard "
            "artifact-only GitHub-hosted runner usage."
        )
    if visibility == "private":
        return "Private repositories can consume included minutes/storage and may become billable."
    return "Repository visibility or billing status was not proven by read-only collection."


def _pages_static_status(visibility: str) -> str:
    if visibility == "public":
        return "allowed_public_repo_github_pages_static_cd"
    if visibility == "private":
        return "blocked_private_repo_pages_may_require_paid_plan_or_quota"
    return "blocked_until_repository_visibility_and_pages_billing_are_known"


def _pages_static_reason(visibility: str) -> str:
    if visibility == "public":
        return (
            "GitHub Pages is available for public repositories on GitHub Free, and "
            "standard GitHub-hosted runner usage for public repositories is free."
        )
    if visibility == "private":
        return (
            "Private repository Pages availability depends on plan and may involve "
            "paid entitlement."
        )
    return "Repository visibility was not proven by read-only collection."
