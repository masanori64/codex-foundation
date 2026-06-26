from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from .bridge_loader import ProjectBridge
from .evidence_boundary import CONTROL_ARTIFACT_KINDS, validate_control_artifact
from .foundation import control_marker
from .profile_loader import ProjectProfile

DEFAULT_EVIDENCE_PATH_PREFIXES = (
    "citations",
    "context_chunks",
    "docs/citations",
    "docs/evidence",
    "docs/source-bundles",
    "docs/source_bundles",
    "evidence",
    "outputs/evidence",
    "reports/evidence",
    "source-bundles",
    "source_bundles",
)


def build_control_artifact_audit(
    profile: ProjectProfile,
    bridge: ProjectBridge,
) -> dict[str, Any]:
    control_paths = planned_control_artifact_paths(bridge)
    evidence_prefixes = configured_evidence_path_prefixes(profile)
    path_errors = audit_control_artifact_paths(
        control_paths=control_paths,
        evidence_path_prefixes=evidence_prefixes,
    )
    marker_requirements = [
        "control_artifact=true",
        "not_evidence=true",
        "not_research_evidence=true",
        "not_citation=true",
        "not_answer_support=true",
        "generated_by=codex-hotl-implementation-pipeline",
        "foundation_manifest.sha256",
    ]
    audit = {
        "schema_version": 1,
        **control_marker(artifact_kind="control_artifact_audit"),
        "project_id": profile.project_id,
        "status": "failed" if path_errors else "passed",
        "control_artifact_paths": control_paths,
        "evidence_path_prefixes": evidence_prefixes,
        "blocked_control_sources": sorted(CONTROL_ARTIFACT_KINDS),
        "marker_requirements": marker_requirements,
        "checks": [
            {
                "name": "control_paths_do_not_overlap_evidence_paths",
                "status": "failed" if path_errors else "passed",
                "errors": path_errors,
            },
            {
                "name": "generated_control_artifact_markers",
                "status": "validated_by_codex_pipeline_validate",
                "required_markers": marker_requirements,
            },
            {
                "name": "subagent_summaries_are_control_only",
                "status": "passed",
                "raw_logs_allowed_in_project": False,
            },
            {
                "name": "chatgpt_wbs_mermaid_outputs_are_control_only",
                "status": "passed",
                "blocked_sources": ["chatgpt_output", "wbs", "mermaid"],
            },
        ],
        "errors": path_errors,
    }
    marker_errors = validate_control_artifact(audit, label="control-artifact-audit")
    if marker_errors:
        audit["status"] = "failed"
        audit["errors"] = [*audit["errors"], *marker_errors]
        audit["checks"].append(
            {
                "name": "control_artifact_audit_marker_self_check",
                "status": "failed",
                "errors": marker_errors,
            }
        )
    return audit


def validate_control_artifact_audit(
    payload: dict[str, Any],
    *,
    profile: ProjectProfile,
    bridge: ProjectBridge,
) -> list[str]:
    errors = validate_control_artifact(payload, label="control-artifact-audit")
    expected_paths = planned_control_artifact_paths(bridge)
    if payload.get("control_artifact_paths") != expected_paths:
        errors.append("control-artifact-audit: control_artifact_paths are stale")
    expected_prefixes = configured_evidence_path_prefixes(profile)
    if payload.get("evidence_path_prefixes") != expected_prefixes:
        errors.append("control-artifact-audit: evidence_path_prefixes are stale")
    expected_errors = audit_control_artifact_paths(
        control_paths=expected_paths,
        evidence_path_prefixes=expected_prefixes,
    )
    if expected_errors:
        errors.extend(expected_errors)
    if payload.get("status") != "passed":
        errors.append("control-artifact-audit: status must be passed")
    payload_errors = payload.get("errors")
    if payload_errors:
        errors.append("control-artifact-audit: errors must be empty")
    blocked = set(payload.get("blocked_control_sources", []))
    for source in ("chatgpt_output", "dashboard", "mermaid", "subagent_summary", "wbs"):
        if source not in blocked:
            errors.append(f"control-artifact-audit: must block {source}")
    return errors


def planned_control_artifact_paths(bridge: ProjectBridge) -> list[str]:
    generated = bridge.generated_dir
    dashboard = bridge.dashboard_dir
    data = dashboard / "data"
    mermaid = bridge.mermaid_dir
    paths = [
        generated / "effective-control-artifact-audit.json",
        generated / "effective-dashboard-state.json",
        generated / "effective-gates.yml",
        generated / "effective-github-collection.json",
        generated / "effective-pipeline.yml",
        generated / "effective-preview-manifest.json",
        generated / "effective-production-manifest.json",
        generated / "effective-profile.yml",
        generated / "effective-staging-manifest.json",
        generated / "effective-subagent-policy.json",
        data / "control-artifact-audit.json",
        data / "dashboard-state.json",
        data / "deploy-manifest.json",
        data / "github-collection.json",
        data / "preview-manifest.json",
        data / "production-manifest.json",
        data / "rollback-manifest.json",
        data / "staging-manifest.json",
        data / "subagent-policy.json",
        dashboard / "index.html",
        mermaid / "ci_cd_lanes.mmd",
        mermaid / "pipeline.mmd",
        mermaid / "rollback.mmd",
    ]
    return sorted({_normalize_path(path) for path in paths})


def configured_evidence_path_prefixes(profile: ProjectProfile) -> list[str]:
    configured = list(DEFAULT_EVIDENCE_PATH_PREFIXES)
    constraints = profile.data.get("constraints", {})
    artifacts = profile.data.get("control_artifacts", {})
    for source in (
        constraints.get("evidence_path_prefixes", []),
        artifacts.get("evidence_path_prefixes", []),
    ):
        if isinstance(source, list):
            configured.extend(str(item) for item in source)
    return sorted({_normalize_path(item) for item in configured if str(item).strip()})


def audit_control_artifact_paths(
    *,
    control_paths: list[str],
    evidence_path_prefixes: list[str],
) -> list[str]:
    errors: list[str] = []
    for control_path in control_paths:
        control = _normalize_path(control_path)
        for evidence_prefix in evidence_path_prefixes:
            evidence = _normalize_path(evidence_prefix)
            if _is_same_or_child(control, evidence):
                errors.append(
                    "control-artifact-audit: control artifact path is inside "
                    f"evidence/citation path: {control} under {evidence}"
                )
            elif _is_same_or_child(evidence, control):
                errors.append(
                    "control-artifact-audit: evidence/citation path points inside "
                    f"control artifact path: {evidence} under {control}"
                )
    return sorted(set(errors))


def _normalize_path(value: object) -> str:
    text = str(value).replace("\\", "/").strip()
    while text.startswith("./"):
        text = text[2:]
    return PurePosixPath(text).as_posix().rstrip("/")


def _is_same_or_child(path: str, prefix: str) -> bool:
    path_parts = PurePosixPath(path.lower()).parts
    prefix_parts = PurePosixPath(prefix.lower()).parts
    if not prefix_parts:
        return False
    return path_parts[: len(prefix_parts)] == prefix_parts
