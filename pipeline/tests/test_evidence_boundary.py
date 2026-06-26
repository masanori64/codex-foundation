from __future__ import annotations

from codex_pipeline.control_artifact_audit import audit_control_artifact_paths
from codex_pipeline.evidence_boundary import validate_control_artifact
from codex_pipeline.foundation import control_marker


def test_control_artifact_rejects_citation_fields() -> None:
    payload = {
        "citation": "not allowed",
        **control_marker(artifact_kind="dashboard"),
    }
    errors = validate_control_artifact(
        payload,
        label="dashboard",
    )

    assert "dashboard: control artifact must not carry 'citation'" in errors


def test_control_artifact_requires_not_citation() -> None:
    errors = validate_control_artifact(
        {"control_artifact": True, "not_evidence": True},
        label="mermaid",
    )

    assert "mermaid: not_citation must be true" in errors
    assert "mermaid: not_research_evidence must be true" in errors
    assert "mermaid: not_answer_support must be true" in errors


def test_control_artifact_audit_rejects_evidence_path_overlap() -> None:
    errors = audit_control_artifact_paths(
        control_paths=["docs/control/codex/dashboard/index.html"],
        evidence_path_prefixes=["docs/control/codex"],
    )

    assert errors == [
        "control-artifact-audit: control artifact path is inside "
        "evidence/citation path: docs/control/codex/dashboard/index.html "
        "under docs/control/codex"
    ]
