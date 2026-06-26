from __future__ import annotations

from pathlib import Path

from codex_pipeline.profile_loader import load_project_profile, validate_project_profile


def test_loads_research_x_profile() -> None:
    profile = load_project_profile(Path("C:/Users/maasa/research_x"))

    assert profile.project_id == "research_x"
    assert profile.data["constraints"]["no_quota_provider_freeze"] is True
    assert profile.data["control_artifacts"]["not_evidence"] is True
    assert profile.data["control_artifacts"]["not_research_evidence"] is True
    assert profile.data["control_artifacts"]["not_citation"] is True
    assert profile.data["control_artifacts"]["not_answer_support"] is True


def test_profile_rejects_control_artifacts_as_evidence() -> None:
    data = {
        "schema_version": 1,
        "project": {
            "id": "demo",
            "name": "demo",
            "root": "C:/tmp/demo",
            "domain": "demo",
        },
        "commands": {},
        "constraints": {
            "use_uv": True,
            "no_quota_provider_freeze": True,
            "evidence_boundary": "raw source != citation",
            "forbid_control_artifacts_as_evidence": False,
        },
        "control_artifacts": {
            "output_root": "docs/control/codex",
            "generated_root": ".codex-project/generated",
            "not_evidence": True,
            "not_citation": True,
        },
        "subagents": {"allowed_roles": []},
    }

    errors = validate_project_profile(data)

    assert "profile: forbid_control_artifacts_as_evidence must be true" in errors
