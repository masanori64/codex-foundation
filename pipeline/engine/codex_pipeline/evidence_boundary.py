from __future__ import annotations

from collections.abc import Mapping
from typing import Any

FORBIDDEN_EVIDENCE_FIELDS = {
    "answer_support",
    "citation",
    "citations",
    "context_chunk",
    "evidence",
    "source_bundle",
}

CONTROL_ARTIFACT_KINDS = {
    "control_artifact_audit",
    "dashboard",
    "mermaid",
    "wbs",
    "chatgpt_output",
    "subagent_summary",
    "subagent_policy",
    "github_state",
    "deploy_manifest",
    "preview_manifest",
    "production_manifest",
    "rollback_manifest",
    "staging_manifest",
    "effective_gates",
    "effective_pipeline",
    "effective_profile",
}


def validate_control_artifact(payload: Mapping[str, Any], *, label: str = "artifact") -> list[str]:
    errors: list[str] = []
    if payload.get("control_artifact") is not True:
        errors.append(f"{label}: control_artifact must be true")
    if payload.get("not_evidence") is not True:
        errors.append(f"{label}: not_evidence must be true")
    if payload.get("not_research_evidence") is not True:
        errors.append(f"{label}: not_research_evidence must be true")
    if payload.get("not_citation") is not True:
        errors.append(f"{label}: not_citation must be true")
    if payload.get("not_answer_support") is not True:
        errors.append(f"{label}: not_answer_support must be true")
    if not payload.get("generated_by"):
        errors.append(f"{label}: generated_by is required")
    foundation_manifest = payload.get("foundation_manifest")
    if not isinstance(foundation_manifest, Mapping):
        errors.append(f"{label}: foundation_manifest is required")
    else:
        if not foundation_manifest.get("id"):
            errors.append(f"{label}: foundation_manifest.id is required")
        if not foundation_manifest.get("sha256"):
            errors.append(f"{label}: foundation_manifest.sha256 is required")
    for field in sorted(FORBIDDEN_EVIDENCE_FIELDS & set(payload)):
        errors.append(f"{label}: control artifact must not carry {field!r}")
    artifact_kind = str(payload.get("artifact_kind", "")).strip()
    if artifact_kind in CONTROL_ARTIFACT_KINDS and payload.get("answer_support_allowed") is True:
        errors.append(f"{label}: {artifact_kind} cannot allow answer support")
    return errors


def evidence_boundary_summary() -> dict[str, Any]:
    return {
        "control_artifacts_are_evidence": False,
        "control_artifacts_are_citations": False,
        "not_evidence": True,
        "not_research_evidence": True,
        "not_citation": True,
        "not_answer_support": True,
        "invariant": (
            "raw source != searchable document != search result != source bundle "
            "!= context chunk != citation != answer"
        ),
        "forbidden_sources": sorted(CONTROL_ARTIFACT_KINDS),
    }
