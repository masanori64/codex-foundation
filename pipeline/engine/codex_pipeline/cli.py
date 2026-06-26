from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .bridge_loader import load_project_bridge
from .cost_guard import build_cost_guard_state
from .dashboard_renderer import render_dashboard_html
from .dashboard_state import build_dashboard_state, write_dashboard_artifacts
from .foundation import PIPELINE_ROOT, write_foundation_manifest
from .gate_policy import capability_statuses, phase_1_gate_statuses
from .github_read_collector import (
    build_github_read_state,
    load_github_read_state,
    write_github_read_artifacts,
)
from .pages import (
    build_pages_deploy_manifest,
    build_pages_health_state,
    build_pages_readiness_state,
    build_pages_rollback_manifest,
    write_pages_health_artifacts,
    write_pages_readiness_artifacts,
    write_pages_rollback_artifacts,
)
from .profile_loader import load_project_profile
from .subagent_governance import build_subagent_policy
from .subagent_runtime import (
    build_subagent_runtime_dry_run,
    write_subagent_runtime_dry_run,
)
from .validation import validate_project
from .workflow_artifact_audit import (
    build_workflow_artifact_audit,
    write_workflow_artifact_audit,
)
from .workflow_smoke import build_workflow_smoke_state, write_workflow_smoke_artifacts
from .workflow_wrappers import (
    generate_pages_workflows,
    generate_workflow_wrappers,
    validate_pages_workflows,
    validate_workflow_wrappers,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in (
        "validate",
        "check-gates",
        "render-dashboard",
        "render-mermaid",
        "explain",
        "check-cost",
        "collect-github-read",
        "audit-workflow-artifacts",
        "audit-workflow-smoke",
        "subagent-dry-run",
        "generate-github-wrappers",
        "validate-github-wrappers",
        "generate-pages-workflows",
        "validate-pages-workflows",
        "check-pages-readiness",
        "read-back-pages",
        "record-pages-rollback",
        "final-audit",
    ):
        command = subparsers.add_parser(name)
        command.add_argument("--project", type=Path, required=True)
        command.add_argument("--foundation-root", type=Path)
        if name == "record-pages-rollback":
            command.add_argument("--target-ref", default="")
    manifest = subparsers.add_parser("write-foundation-manifest")
    manifest.add_argument("--known-project", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "write-foundation-manifest":
        manifest = write_foundation_manifest(known_projects=args.known_project)
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    project = args.project.resolve()
    requested_foundation_root = getattr(args, "foundation_root", None)
    if (
        requested_foundation_root is not None
        and requested_foundation_root.resolve() != PIPELINE_ROOT
    ):
        print(
            (
                "ERROR: --foundation-root does not match this codex-pipeline runtime: "
                f"requested={requested_foundation_root.resolve()} actual={PIPELINE_ROOT}"
            ),
            file=sys.stderr,
        )
        return 1
    if args.command == "validate":
        errors = validate_project(project)
        if errors:
            print(f"foundation root: {PIPELINE_ROOT}", file=sys.stderr)
            print(f"project root: {project}", file=sys.stderr)
            print(f"python executable: {sys.executable}", file=sys.stderr)
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"codex-pipeline validation ok: {project}")
        return 0
    if args.command == "check-gates":
        gates = [gate.as_dict() for gate in phase_1_gate_statuses()]
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "gates": gates,
                    "capabilities": capability_statuses(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "generate-github-wrappers":
        result = generate_workflow_wrappers(project)
        errors = validate_workflow_wrappers(
            project,
            capability_status="artifact_only",
            dashboard_artifact_status="artifact_only",
        )
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "generate-pages-workflows":
        result = generate_pages_workflows(project)
        errors = validate_pages_workflows(project)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "validate-github-wrappers":
        profile = load_project_profile(project)
        bridge = load_project_bridge(project)
        capabilities = {
            **profile.data.get("capabilities", {}),
            **bridge.data.get("capabilities", {}),
        }
        errors = validate_workflow_wrappers(
            project,
            capability_status=str(capabilities.get("github_actions_wrappers", "")),
            dashboard_artifact_status=str(capabilities.get("dashboard_artifact_cd", "")),
        )
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"github workflow wrappers ok: {project}")
        return 0
    if args.command == "validate-pages-workflows":
        errors = validate_pages_workflows(project)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"github pages workflows ok: {project}")
        return 0
    if args.command == "check-pages-readiness":
        profile = load_project_profile(project)
        bridge = load_project_bridge(project)
        state = build_pages_readiness_state(profile, bridge, execute=True)
        write_pages_readiness_artifacts(profile, bridge, state)
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "read-back-pages":
        profile = load_project_profile(project)
        bridge = load_project_bridge(project)
        health = build_pages_health_state(profile, bridge, execute=True)
        deploy_manifest = build_pages_deploy_manifest(profile, bridge, health)
        write_pages_health_artifacts(profile, bridge, health, deploy_manifest)
        print(json.dumps(health, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "record-pages-rollback":
        profile = load_project_profile(project)
        bridge = load_project_bridge(project)
        state = build_pages_rollback_manifest(
            profile,
            bridge,
            rollback_executed=True,
            target_ref=args.target_ref,
        )
        write_pages_rollback_artifacts(profile, bridge, state)
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "check-cost":
        profile = load_project_profile(project)
        bridge = load_project_bridge(project)
        github_read_state = load_github_read_state(project, bridge)
        state = build_cost_guard_state(
            profile,
            bridge,
            github_read_state=github_read_state,
        )
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "final-audit":
        profile = load_project_profile(project)
        bridge = load_project_bridge(project)
        state = build_dashboard_state(profile, bridge)
        errors = []
        e2e = state["e2e_completion_manifest"]
        if e2e.get("final_automatic_pipeline_status") != "complete_static_pages_cd_no_cost":
            errors.append("final_automatic_pipeline_status is not complete_static_pages_cd_no_cost")
        for key in (
            "paid_usage_detected",
            "provider_quota_used",
            "secrets_used",
            "pat_used",
            "deploy_key_used",
            "external_cloud_used",
            "db_migration_executed",
            "research_evidence_written",
        ):
            if e2e.get(key) is not False:
                errors.append(f"{key} must be false")
        if state["project_boundary"]["project_may_own_generic_engine"] is not False:
            errors.append("project boundary does not forbid generic engine ownership")
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"final audit ok: {project}")
        return 0
    if args.command == "collect-github-read":
        profile = load_project_profile(project)
        bridge = load_project_bridge(project)
        state = build_github_read_state(project, bridge, execute=True)
        write_github_read_artifacts(profile, bridge, state)
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "audit-workflow-artifacts":
        profile = load_project_profile(project)
        bridge = load_project_bridge(project)
        github_read_state = load_github_read_state(project, bridge)
        state = build_workflow_artifact_audit(
            project,
            bridge,
            github_read_state=github_read_state,
        )
        write_workflow_artifact_audit(profile, bridge, state)
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "audit-workflow-smoke":
        profile = load_project_profile(project)
        bridge = load_project_bridge(project)
        github_read_state = load_github_read_state(project, bridge)
        state = build_workflow_smoke_state(
            project,
            github_read_state=github_read_state,
        )
        write_workflow_smoke_artifacts(profile, bridge, state)
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "subagent-dry-run":
        profile = load_project_profile(project)
        bridge = load_project_bridge(project)
        subagent_policy = build_subagent_policy(
            allowed_roles=profile.data["subagents"].get("allowed_roles", []),
        )
        state = build_subagent_runtime_dry_run(subagent_policy)
        write_subagent_runtime_dry_run(profile, bridge, state)
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command in {"render-dashboard", "render-mermaid", "explain"}:
        profile = load_project_profile(project)
        bridge = load_project_bridge(project)
        state = build_dashboard_state(profile, bridge)
        write_dashboard_artifacts(profile, bridge, state)
        dashboard_dir = profile.project_root / bridge.dashboard_dir
        if args.command == "render-dashboard":
            dashboard_dir.mkdir(parents=True, exist_ok=True)
            (dashboard_dir / "index.html").write_text(
                render_dashboard_html(state),
                encoding="utf-8",
                newline="\n",
            )
            print(f"rendered dashboard: {dashboard_dir / 'index.html'}")
            return 0
        if args.command == "render-mermaid":
            mermaid_dir = profile.project_root / bridge.mermaid_dir
            print(f"rendered mermaid: {mermaid_dir}")
            return 0
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    parser.error(f"unhandled command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
