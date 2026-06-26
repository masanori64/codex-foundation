from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .bridge_loader import ProjectBridge
from .control_artifact_audit import build_control_artifact_audit
from .cost_guard import build_cost_guard_state
from .deploy_manifest import build_deploy_manifest
from .e2e_completion import build_e2e_completion_manifest
from .evidence_boundary import evidence_boundary_summary, validate_control_artifact
from .foundation import control_marker, foundation_manifest_summary, mermaid_marker_comment
from .gate_policy import capability_statuses, phase_1_gate_statuses
from .github_collection import build_github_collection_state
from .github_read_collector import load_github_read_state
from .mermaid_renderer import (
    effective_pipeline,
    render_ci_cd_lanes_mermaid,
    render_pipeline_mermaid,
    render_rollback_mermaid,
)
from .pages import (
    build_pages_deploy_manifest,
    build_pages_health_state,
    build_pages_readiness_state,
    build_pages_rollback_manifest,
    load_pages_health,
    load_pages_readiness,
    load_pages_rollback_manifest,
)
from .preview_manifest import build_preview_manifest
from .production_manifest import build_production_manifest
from .profile_loader import ProjectProfile
from .rollback_planner import build_rollback_manifest
from .simple_yaml import dumps
from .staging_manifest import build_staging_manifest
from .subagent_governance import build_subagent_policy
from .subagent_runtime import build_subagent_runtime_dry_run
from .workflow_artifact_audit import build_workflow_artifact_audit
from .workflow_smoke import build_workflow_smoke_state


def build_dashboard_state(profile: ProjectProfile, bridge: ProjectBridge) -> dict[str, Any]:
    pipeline = effective_pipeline(profile.data)
    mermaid = {
        "pipeline": render_pipeline_mermaid(pipeline),
        "ci_cd_lanes": render_ci_cd_lanes_mermaid(pipeline),
        "rollback": render_rollback_mermaid(),
    }
    pages_readiness = load_pages_readiness(profile.project_root, bridge)
    if not pages_readiness:
        pages_readiness = build_pages_readiness_state(profile, bridge)
    pages_health = load_pages_health(profile.project_root, bridge)
    if not pages_health:
        pages_health = build_pages_health_state(profile, bridge)
    pages_deploy_manifest = build_pages_deploy_manifest(profile, bridge, pages_health)
    pages_rollback_manifest = load_pages_rollback_manifest(profile.project_root, bridge)
    if not pages_rollback_manifest:
        pages_rollback_manifest = build_pages_rollback_manifest(profile, bridge)
    deploy_manifest = build_deploy_manifest(project_id=profile.project_id)
    preview_manifest = build_preview_manifest(
        project_id=profile.project_id,
        pages_health=pages_health,
    )
    production_manifest = build_production_manifest(
        project_id=profile.project_id,
        pages_health=pages_health,
    )
    rollback_manifest = build_rollback_manifest(
        project_id=profile.project_id,
        pages_rollback_manifest=pages_rollback_manifest,
    )
    staging_manifest = build_staging_manifest(
        project_id=profile.project_id,
        pages_health=pages_health,
    )
    subagent_policy = build_subagent_policy(
        allowed_roles=profile.data["subagents"].get("allowed_roles", []),
    )
    control_artifact_audit = build_control_artifact_audit(profile, bridge)
    github_collection = build_github_collection_state(bridge)
    github_read_state = load_github_read_state(profile.project_root, bridge)
    cost_guard = build_cost_guard_state(
        profile,
        bridge,
        github_read_state=github_read_state,
    )
    workflow_artifact_audit = build_workflow_artifact_audit(
        profile.project_root,
        bridge,
        github_read_state=github_read_state,
    )
    workflow_smoke = build_workflow_smoke_state(
        profile.project_root,
        github_read_state=github_read_state,
    )
    subagent_runtime_dry_run = build_subagent_runtime_dry_run(subagent_policy)
    e2e_completion_manifest = build_e2e_completion_manifest(
        profile,
        cost_guard=cost_guard,
        github_read_state=github_read_state,
        workflow_smoke=workflow_smoke,
        workflow_artifact_audit=workflow_artifact_audit,
        subagent_runtime_dry_run=subagent_runtime_dry_run,
        pages_readiness=pages_readiness,
        pages_health=pages_health,
        pages_rollback_manifest=pages_rollback_manifest,
    )
    profile_capabilities = profile.data.get("capabilities", {})
    bridge_capabilities = bridge.data.get("capabilities", {})
    capabilities = capability_statuses(
        overrides={**profile_capabilities, **bridge_capabilities},
    )
    state = {
        "schema_version": 1,
        **control_marker(artifact_kind="dashboard"),
        "generated_at": datetime.now(UTC).isoformat(),
        "answer_support_allowed": False,
        "foundation": foundation_manifest_summary(),
        "project": {
            "id": profile.project_id,
            "name": profile.project_name,
            "root": str(profile.project_root),
            "domain": profile.data["project"]["domain"],
        },
        "collection": github_collection,
        "git": _git_state(profile.project_root),
        "profile": {
            "path": str(profile.path),
            "constraints": profile.data["constraints"],
        },
        "bridge": {
            "path": str(bridge.path),
            "outputs": bridge.data["outputs"],
            "github": bridge.data["github"],
        },
        "project_boundary": {
            "generic_pipeline_owner": "Codex foundation",
            "project_may_own_generic_engine": False,
            "allowed_project_surfaces": [
                ".codex-project/profile.yml",
                ".codex-project/bridge.yml",
                ".codex-project/generated",
                "docs/control/codex",
                "thin wrappers after explicit gate",
            ],
        },
        "gates": [gate.as_dict() for gate in phase_1_gate_statuses()],
        "capabilities": capabilities,
        "pipeline": pipeline,
        "dashboard": {
            "title": f"{profile.project_name} Codex HOTL Control Dashboard",
            "notice": "control artifact / not evidence / not citation",
            "mermaid": mermaid,
        },
        "subagents": {
            "owner": "Codex foundation",
            "raw_log_in_project": False,
            "allowed_roles": profile.data["subagents"].get("allowed_roles", []),
            "summaries": [],
            "policy": subagent_policy,
        },
        "deploy_manifest": deploy_manifest,
        "preview_manifest": preview_manifest,
        "production_manifest": production_manifest,
        "rollback_manifest": rollback_manifest,
        "staging_manifest": staging_manifest,
        "pages_readiness": pages_readiness,
        "pages_health": pages_health,
        "pages_deploy_manifest": pages_deploy_manifest,
        "pages_rollback_manifest": pages_rollback_manifest,
        "subagent_policy": subagent_policy,
        "control_artifact_audit": control_artifact_audit,
        "github_collection": github_collection,
        "github_read_state": github_read_state,
        "cost_guard": cost_guard,
        "workflow_artifact_audit": workflow_artifact_audit,
        "workflow_smoke": workflow_smoke,
        "subagent_runtime_dry_run": subagent_runtime_dry_run,
        "e2e_completion_manifest": e2e_completion_manifest,
        "evidence_boundary": evidence_boundary_summary(),
    }
    errors = validate_control_artifact(state, label="dashboard-state")
    if errors:
        raise ValueError("; ".join(errors))
    return state


def write_dashboard_artifacts(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    state: dict[str, Any],
) -> None:
    project_root = profile.project_root
    dashboard_dir = project_root / bridge.dashboard_dir
    generated_dir = project_root / bridge.generated_dir
    mermaid_dir = project_root / bridge.mermaid_dir
    data_dir = dashboard_dir / "data"
    for path in (dashboard_dir, generated_dir, mermaid_dir, data_dir):
        path.mkdir(parents=True, exist_ok=True)

    _write_json(data_dir / "dashboard-state.json", state)
    _write_json(data_dir / "deploy-manifest.json", state["deploy_manifest"])
    _write_json(data_dir / "preview-manifest.json", state["preview_manifest"])
    _write_json(data_dir / "production-manifest.json", state["production_manifest"])
    _write_json(data_dir / "rollback-manifest.json", state["rollback_manifest"])
    _write_json(data_dir / "staging-manifest.json", state["staging_manifest"])
    _write_json(data_dir / "subagent-policy.json", state["subagent_policy"])
    _write_json(data_dir / "subagent-runtime-dry-run.json", state["subagent_runtime_dry_run"])
    _write_json(data_dir / "control-artifact-audit.json", state["control_artifact_audit"])
    _write_json(data_dir / "github-collection.json", state["github_collection"])
    _write_json(data_dir / "github-read-state.json", state["github_read_state"])
    _write_json(data_dir / "cost-guard.json", state["cost_guard"])
    _write_json(data_dir / "pages-readiness.json", state["pages_readiness"])
    _write_json(data_dir / "pages-health.json", state["pages_health"])
    _write_json(data_dir / "pages-deploy-manifest.json", state["pages_deploy_manifest"])
    _write_json(data_dir / "pages-rollback-manifest.json", state["pages_rollback_manifest"])
    _write_json(data_dir / "workflow-artifact-audit.json", state["workflow_artifact_audit"])
    _write_json(data_dir / "workflow-smoke.json", state["workflow_smoke"])
    _write_json(
        data_dir / "e2e-completion-manifest.json",
        state["e2e_completion_manifest"],
    )
    _write_json(generated_dir / "effective-dashboard-state.json", state)
    _write_json(
        generated_dir / "effective-control-artifact-audit.json",
        state["control_artifact_audit"],
    )
    _write_json(generated_dir / "effective-github-collection.json", state["github_collection"])
    _write_json(generated_dir / "effective-github-read-state.json", state["github_read_state"])
    _write_json(generated_dir / "effective-cost-guard.json", state["cost_guard"])
    _write_json(generated_dir / "effective-pages-readiness.json", state["pages_readiness"])
    _write_json(generated_dir / "effective-pages-health.json", state["pages_health"])
    _write_json(
        generated_dir / "effective-pages-deploy-manifest.json",
        state["pages_deploy_manifest"],
    )
    _write_json(
        generated_dir / "effective-pages-rollback-manifest.json",
        state["pages_rollback_manifest"],
    )
    _write_json(
        generated_dir / "effective-workflow-artifact-audit.json",
        state["workflow_artifact_audit"],
    )
    _write_json(
        generated_dir / "effective-workflow-smoke.json",
        state["workflow_smoke"],
    )
    _write_json(
        generated_dir / "effective-e2e-completion-manifest.json",
        state["e2e_completion_manifest"],
    )
    _write_json(generated_dir / "effective-preview-manifest.json", state["preview_manifest"])
    _write_json(generated_dir / "effective-production-manifest.json", state["production_manifest"])
    _write_json(generated_dir / "effective-staging-manifest.json", state["staging_manifest"])
    _write_json(generated_dir / "effective-subagent-policy.json", state["subagent_policy"])
    _write_json(
        generated_dir / "effective-subagent-runtime-dry-run.json",
        state["subagent_runtime_dry_run"],
    )
    (generated_dir / "effective-pipeline.yml").write_text(
        dumps(state["pipeline"]),
        encoding="utf-8",
        newline="\n",
    )
    (generated_dir / "effective-profile.yml").write_text(
        dumps(
            {
                "schema_version": 1,
                **control_marker(artifact_kind="effective_profile"),
                "project": state["project"],
                "commands": profile.data["commands"],
                "constraints": profile.data["constraints"],
                "capabilities": {
                    item["capability_id"]: item["status"]
                    for item in state["capabilities"]
                },
                "control_artifacts": profile.data["control_artifacts"],
                "subagents": state["subagents"],
                "bridge": state["bridge"],
                "project_boundary": state["project_boundary"],
            }
        ),
        encoding="utf-8",
        newline="\n",
    )
    (generated_dir / "effective-gates.yml").write_text(
        dumps(
            {
                "schema_version": 1,
                **control_marker(artifact_kind="effective_gates"),
                "gates": state["gates"],
                "capabilities": state["capabilities"],
            }
        ),
        encoding="utf-8",
        newline="\n",
    )
    for name, content in state["dashboard"]["mermaid"].items():
        (mermaid_dir / f"{name}.mmd").write_text(
            mermaid_marker_comment() + content,
            encoding="utf-8",
            newline="\n",
        )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _git_state(project_root: Path) -> dict[str, Any]:
    return {
        "branch": _run_git(project_root, ["branch", "--show-current"]) or "unknown",
        "commit": _run_git(project_root, ["rev-parse", "HEAD"]) or "unknown",
        "dirty": bool(_run_git(project_root, ["status", "--porcelain=v1"])),
    }


def _run_git(project_root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()
