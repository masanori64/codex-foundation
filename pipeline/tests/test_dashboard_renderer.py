from __future__ import annotations

from pathlib import Path

from codex_pipeline.bridge_loader import load_project_bridge
from codex_pipeline.dashboard_renderer import render_dashboard_html
from codex_pipeline.dashboard_state import build_dashboard_state
from codex_pipeline.profile_loader import load_project_profile
from codex_pipeline.workflow_wrappers import generate_workflow_wrappers


def test_dashboard_state_and_html_are_control_artifacts(codex_project: Path) -> None:
    generate_workflow_wrappers(codex_project)
    profile = load_project_profile(codex_project)
    bridge = load_project_bridge(codex_project)

    state = build_dashboard_state(profile, bridge)
    html = render_dashboard_html(state)

    assert state["control_artifact"] is True
    assert state["not_evidence"] is True
    assert state["not_research_evidence"] is True
    assert state["not_citation"] is True
    assert state["not_answer_support"] is True
    assert state["foundation"]["sha256"]
    assert any(item["capability_id"] == "production_cd" for item in state["capabilities"])
    assert state["preview_manifest"]["target_type"] == "artifact_only"
    assert state["preview_manifest"]["side_effects"]["pages_enabled"] is False
    assert state["staging_manifest"]["target_type"] == "safe_static_plan"
    assert state["staging_manifest"]["dry_run"] is True
    assert state["production_manifest"]["target_type"] == "production_plan"
    assert state["production_manifest"]["execution_enabled"] is False
    assert state["rollback_manifest"]["scope"] == "safe_static_artifacts_only"
    assert state["rollback_manifest"]["drill"]["restore_executed"] is False
    assert state["subagent_policy"]["raw_log_in_project"] is False
    assert "commit" in state["subagent_policy"]["forbidden_actions"]
    assert state["subagent_runtime_dry_run"]["subagents_spawned"] is False
    assert state["cost_guard"]["answer"]["has_paid_execution_in_current_pipeline"] is False
    assert state["cost_guard"]["active_completion_blockers"] == []
    assert (
        state["e2e_completion_manifest"]["completion"]["final_automatic_pipeline_status"]
        == "pending_remote_artifact_e2e"
    )
    assert state["e2e_completion_manifest"]["completion"]["free_static_pages_cd_complete"] is False
    assert state["workflow_artifact_audit"]["workflow_dispatch_executed"] is False
    assert state["workflow_smoke"]["workflow_dispatch_executed"] is False
    assert state["e2e_completion_manifest"]["local_control_plane_complete"] is True
    assert state["pages_health"]["status"] == "not_checked"
    assert state["pages_health"]["execute"] is False
    assert state["github_read_state"]["authentication"] == "none"
    assert state["control_artifact_audit"]["status"] == "passed"
    assert "chatgpt_output" in state["control_artifact_audit"]["blocked_control_sources"]
    assert "control artifact / not evidence / not citation" in html
    assert "never research evidence" in html
    assert "Capability Kill Switches" in html
    assert "Evidence Boundary Audit" in html
    assert "GitHub Read Smoke" in html
    assert "Paid Execution" in html
    assert "Artifact Smoke" in html
    assert "Workflow E2E" in html
    assert "E2E Completion" in html
    assert "Active Completion Blockers" in html
    assert "Free Static Pages CD" in html
    assert "Pages Readiness" in html
    assert "Pages Health" in html
    assert "Subagent Dry Run" in html
