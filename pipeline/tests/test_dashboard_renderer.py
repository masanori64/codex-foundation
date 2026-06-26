from __future__ import annotations

from pathlib import Path

from codex_pipeline.bridge_loader import load_project_bridge
from codex_pipeline.dashboard_renderer import render_dashboard_html
from codex_pipeline.dashboard_state import build_dashboard_state
from codex_pipeline.profile_loader import load_project_profile


def test_dashboard_state_and_html_are_control_artifacts() -> None:
    project = Path("C:/Users/maasa/research_x")
    profile = load_project_profile(project)
    bridge = load_project_bridge(project)

    state = build_dashboard_state(profile, bridge)
    html = render_dashboard_html(state)

    assert state["control_artifact"] is True
    assert state["not_evidence"] is True
    assert state["not_research_evidence"] is True
    assert state["not_citation"] is True
    assert state["not_answer_support"] is True
    assert state["foundation"]["sha256"]
    assert any(item["capability_id"] == "production_cd" for item in state["capabilities"])
    assert state["preview_manifest"]["target_type"] == "static_pages_lane"
    assert state["staging_manifest"]["target_type"] == "static_pages_lane"
    assert state["staging_manifest"]["dry_run"] is False
    assert state["production_manifest"]["target_type"] == "static_pages_production"
    assert state["production_manifest"]["execution_enabled"] is True
    assert state["rollback_manifest"]["scope"] == "safe_static_artifacts_only"
    assert state["rollback_manifest"]["drill"]["restore_executed"] is True
    assert state["subagent_policy"]["raw_log_in_project"] is False
    assert "commit" in state["subagent_policy"]["forbidden_actions"]
    assert state["subagent_runtime_dry_run"]["subagents_spawned"] is False
    assert state["cost_guard"]["answer"]["has_paid_execution_in_current_pipeline"] is False
    assert state["cost_guard"]["active_completion_blockers"] == []
    assert state["e2e_completion_manifest"]["active_completion_blockers"] == []
    assert state["e2e_completion_manifest"]["completion"]["free_static_pages_cd_complete"] is True
    assert state["workflow_artifact_audit"]["workflow_dispatch_executed"] is False
    assert state["workflow_smoke"]["workflow_dispatch_executed"] is False
    assert state["e2e_completion_manifest"]["local_control_plane_complete"] is True
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
