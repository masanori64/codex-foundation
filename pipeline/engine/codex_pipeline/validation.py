from __future__ import annotations

import json
from pathlib import Path

from .bridge_loader import load_project_bridge
from .control_artifact_audit import validate_control_artifact_audit
from .dashboard_state import build_dashboard_state
from .evidence_boundary import validate_control_artifact
from .foundation import validate_foundation_manifest
from .profile_loader import load_project_profile
from .simple_yaml import load_structured_file
from .workflow_wrappers import validate_pages_workflows, validate_workflow_wrappers

FORBIDDEN_PROJECT_ENGINE_PATHS = [
    ".pipeline/pipeline.yml",
    ".github/workflows/project-dashboard.yml",
    "scripts/collect_github_state.py",
    "scripts/render_dashboard.py",
    "src/project_dashboard.py",
    "tests/test_project_dashboard.py",
]


def validate_project(project: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_foundation_manifest())
    try:
        profile = load_project_profile(project)
    except (FileNotFoundError, ValueError) as exc:
        return [str(exc)]
    try:
        bridge = load_project_bridge(project)
    except (FileNotFoundError, ValueError) as exc:
        return [str(exc)]
    if bridge.project_id != profile.project_id:
        errors.append(
            f"bridge project_id {bridge.project_id!r} does not match profile {profile.project_id!r}"
        )
    if profile.project_root.resolve() != project.resolve():
        errors.append(f"profile project.root must match --project: {profile.project_root}")
    errors.extend(_validate_project_boundary(project, project_id=profile.project_id))
    capabilities = {
        **profile.data.get("capabilities", {}),
        **bridge.data.get("capabilities", {}),
    }
    errors.extend(
        validate_workflow_wrappers(
            project,
            capability_status=str(capabilities.get("github_actions_wrappers", "")),
            dashboard_artifact_status=str(capabilities.get("dashboard_artifact_cd", "")),
        )
    )
    if str(capabilities.get("github_pages", "")).startswith("enabled"):
        errors.extend(validate_pages_workflows(project))
    try:
        state = build_dashboard_state(profile, bridge)
    except ValueError as exc:
        errors.append(str(exc))
    else:
        errors.extend(validate_control_artifact(state, label="dashboard-state"))
        errors.extend(
            validate_control_artifact_audit(
                state["control_artifact_audit"],
                profile=profile,
                bridge=bridge,
            )
        )
        errors.extend(_validate_generated_artifacts(profile.project_root, profile, bridge))
    return errors


def _validate_generated_artifacts(project_root: Path, profile, bridge) -> list[str]:
    errors: list[str] = []
    generated_dir = project_root / bridge.generated_dir
    dashboard_dir = project_root / bridge.dashboard_dir
    mermaid_dir = project_root / bridge.mermaid_dir
    for path in [
        generated_dir / "effective-dashboard-state.json",
        dashboard_dir / "data" / "dashboard-state.json",
        dashboard_dir / "data" / "deploy-manifest.json",
        dashboard_dir / "data" / "preview-manifest.json",
        dashboard_dir / "data" / "production-manifest.json",
        dashboard_dir / "data" / "rollback-manifest.json",
        dashboard_dir / "data" / "staging-manifest.json",
        dashboard_dir / "data" / "subagent-policy.json",
        dashboard_dir / "data" / "subagent-runtime-dry-run.json",
        dashboard_dir / "data" / "control-artifact-audit.json",
        dashboard_dir / "data" / "github-collection.json",
        dashboard_dir / "data" / "github-read-state.json",
        dashboard_dir / "data" / "cost-guard.json",
        dashboard_dir / "data" / "pages-readiness.json",
        dashboard_dir / "data" / "pages-health.json",
        dashboard_dir / "data" / "pages-deploy-manifest.json",
        dashboard_dir / "data" / "pages-rollback-manifest.json",
        dashboard_dir / "data" / "workflow-artifact-audit.json",
        dashboard_dir / "data" / "workflow-smoke.json",
        dashboard_dir / "data" / "e2e-completion-manifest.json",
        generated_dir / "effective-control-artifact-audit.json",
        generated_dir / "effective-github-collection.json",
        generated_dir / "effective-github-read-state.json",
        generated_dir / "effective-cost-guard.json",
        generated_dir / "effective-pages-readiness.json",
        generated_dir / "effective-pages-health.json",
        generated_dir / "effective-pages-deploy-manifest.json",
        generated_dir / "effective-pages-rollback-manifest.json",
        generated_dir / "effective-workflow-artifact-audit.json",
        generated_dir / "effective-workflow-smoke.json",
        generated_dir / "effective-e2e-completion-manifest.json",
        generated_dir / "effective-preview-manifest.json",
        generated_dir / "effective-production-manifest.json",
        generated_dir / "effective-staging-manifest.json",
        generated_dir / "effective-subagent-policy.json",
        generated_dir / "effective-subagent-runtime-dry-run.json",
    ]:
        if path.exists():
            errors.extend(_validate_json_artifact(path))
            errors.extend(_validate_no_cost_artifact(path))
            if path.name in {
                "control-artifact-audit.json",
                "effective-control-artifact-audit.json",
            }:
                payload = json.loads(path.read_text(encoding="utf-8"))
                errors.extend(
                    validate_control_artifact_audit(payload, profile=profile, bridge=bridge)
                )
    for path in [
        generated_dir / "effective-pipeline.yml",
        generated_dir / "effective-gates.yml",
        generated_dir / "effective-profile.yml",
    ]:
        if path.exists():
            errors.extend(_validate_yaml_artifact(path))
    if mermaid_dir.exists():
        for path in sorted(mermaid_dir.glob("*.mmd")):
            errors.extend(_validate_mermaid_artifact(path))
    html_path = dashboard_dir / "index.html"
    if html_path.exists():
        text = html_path.read_text(encoding="utf-8")
        for marker in (
            "control artifact / not evidence / not citation",
            '"not_research_evidence": true',
            '"not_answer_support": true',
        ):
            if marker not in text:
                errors.append(f"{html_path}: missing marker {marker!r}")
    return errors


def _validate_no_cost_artifact(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if path.name in {"cost-guard.json", "effective-cost-guard.json"}:
        policy = payload.get("cost_policy", {})
        if policy.get("paid_usage_detected") is not False:
            errors.append(f"{path}: paid_usage_detected must be false")
        if policy.get("pipeline_contains_paid_execution") is not False:
            errors.append(f"{path}: pipeline_contains_paid_execution must be false")
        answer = payload.get("answer", {})
        if answer.get("has_paid_execution_in_current_pipeline") is not False:
            errors.append(f"{path}: current pipeline must not have paid execution")
    if path.name in {"github-read-state.json", "effective-github-read-state.json"}:
        if payload.get("authentication") != "none":
            errors.append(f"{path}: authentication must be none")
        if payload.get("token_used") is not False:
            errors.append(f"{path}: token_used must be false")
        if payload.get("write_operations_available") is not False:
            errors.append(f"{path}: write_operations_available must be false")
        if payload.get("mutation_methods_available") != []:
            errors.append(f"{path}: mutation_methods_available must be []")
        if payload.get("paid_usage_detected") is not False:
            errors.append(f"{path}: paid_usage_detected must be false")
        methods = payload.get("request_methods_used", [])
        if any(method != "GET" for method in methods):
            errors.append(f"{path}: only GET requests are allowed")
    if path.name in {
        "workflow-artifact-audit.json",
        "effective-workflow-artifact-audit.json",
        "workflow-smoke.json",
        "effective-workflow-smoke.json",
    }:
        for key in (
            "workflow_dispatch_executed",
            "github_actions_minutes_consumed_by_this_smoke",
            "github_actions_artifact_storage_created_by_this_smoke",
            "github_api_write_executed",
            "deploy_executed",
            "pages_enabled",
            "repository_settings_changed",
            "secrets_used",
            "paid_usage_detected",
            "provider_api_calls",
            "provider_quota_used",
        ):
            if key in payload and payload.get(key) is not False:
                errors.append(f"{path}: {key} must be false")
        if path.name in {"workflow-smoke.json", "effective-workflow-smoke.json"}:
            trigger = payload.get("trigger_policy", {})
            if trigger.get("workflow_dispatch_enabled") is not False:
                errors.append(f"{path}: workflow_dispatch_enabled must be false")
    if path.name in {
        "e2e-completion-manifest.json",
        "effective-e2e-completion-manifest.json",
        "pages-readiness.json",
        "effective-pages-readiness.json",
        "pages-health.json",
        "effective-pages-health.json",
        "pages-deploy-manifest.json",
        "effective-pages-deploy-manifest.json",
        "pages-rollback-manifest.json",
        "effective-pages-rollback-manifest.json",
    }:
        for key in (
            "paid_usage_detected",
            "provider_api_calls",
            "provider_quota_used",
            "secrets_used",
            "pat_used",
            "deploy_key_used",
            "external_cloud_used",
            "db_migration_executed",
            "research_evidence_written",
        ):
            if key in payload and payload.get(key) is not False:
                errors.append(f"{path}: {key} must be false")
        side_effects = payload.get("side_effects", {})
        if isinstance(side_effects, dict):
            for key in (
                "provider_api_calls",
                "paid_usage_detected",
                "secrets_used",
                "pat_used",
                "deploy_key_used",
                "external_cloud_used",
                "db_migration_executed",
                "research_evidence_written",
            ):
                if key in side_effects and side_effects.get(key) is not False:
                    errors.append(f"{path}: side_effects.{key} must be false")
    if path.name in {
        "subagent-runtime-dry-run.json",
        "effective-subagent-runtime-dry-run.json",
    }:
        if payload.get("subagents_spawned") is not False:
            errors.append(f"{path}: subagents_spawned must be false")
        if payload.get("model_runner_started") is not False:
            errors.append(f"{path}: model_runner_started must be false")
        if payload.get("provider_api_calls") is not False:
            errors.append(f"{path}: provider_api_calls must be false")
        if payload.get("paid_usage_detected") is not False:
            errors.append(f"{path}: paid_usage_detected must be false")
    return errors


def _validate_project_boundary(project_root: Path, *, project_id: str) -> list[str]:
    errors: list[str] = []
    dynamic_paths = [Path("src") / project_id / "project_dashboard.py"]
    for rel in [*FORBIDDEN_PROJECT_ENGINE_PATHS, *dynamic_paths]:
        path = project_root / rel
        if path.exists():
            errors.append(f"generic Codex pipeline implementation must not live in project: {path}")
    return errors


def _validate_json_artifact(path: Path) -> list[str]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return [f"{path}: JSON artifact root must be an object"]
    return validate_control_artifact(payload, label=str(path))


def _validate_yaml_artifact(path: Path) -> list[str]:
    payload = load_structured_file(path)
    return validate_control_artifact(payload, label=str(path))


def _validate_mermaid_artifact(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for marker in (
        "%% control_artifact=true",
        "%% not_research_evidence=true",
        "%% not_citation=true",
        "%% not_answer_support=true",
        "%% generated_by=codex-hotl-implementation-pipeline",
        "%% foundation_manifest_sha256=",
    ):
        if marker not in text:
            errors.append(f"{path}: missing Mermaid marker {marker!r}")
    return errors
