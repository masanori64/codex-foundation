from __future__ import annotations

from pathlib import Path

from codex_pipeline import pages
from codex_pipeline.bridge_loader import load_project_bridge
from codex_pipeline.cost_guard import build_cost_guard_state
from codex_pipeline.github_read_collector import build_github_read_state
from codex_pipeline.pages import build_pages_readiness_state
from codex_pipeline.profile_loader import load_project_profile
from codex_pipeline.subagent_governance import build_subagent_policy
from codex_pipeline.subagent_runtime import build_subagent_runtime_dry_run
from codex_pipeline.workflow_artifact_audit import build_workflow_artifact_audit


def test_no_cost_guard_has_no_paid_execution() -> None:
    project = Path("C:/Users/maasa/research_x")
    profile = load_project_profile(project)
    bridge = load_project_bridge(project)

    state = build_cost_guard_state(profile, bridge)

    assert state["cost_policy"]["paid_usage_detected"] is False
    assert state["cost_policy"]["pipeline_contains_paid_execution"] is False
    assert state["answer"]["has_paid_execution_in_current_pipeline"] is False
    assert state["active_completion_blockers"] == []
    assert {item["status"] for item in state["hard_blocked_paid"]} == {
        "hard_blocked_paid"
    }
    assert {
        item["status"] for item in state["not_used_outside_free_static_pages_cd"]
    } == {
        "not_used_outside_free_static_pages_cd",
        "outside_scope_for_this_pipeline",
    }
    action_ids = {item["action_id"] for item in state["allowed_no_cost_actions"]}
    assert "github_rest_public_read_unauthenticated" in action_ids
    assert "github_pages_public_repo_static_cd" in action_ids


def test_github_read_placeholder_is_read_only_and_no_secret() -> None:
    project = Path("C:/Users/maasa/research_x")
    bridge = load_project_bridge(project)

    state = build_github_read_state(project, bridge, execute=False)

    assert state["api_calls_executed"] is False
    assert state["authentication"] == "none"
    assert state["token_used"] is False
    assert state["write_operations_available"] is False
    assert state["mutation_methods_available"] == []
    assert state["paid_usage_detected"] is False


def test_workflow_artifact_audit_does_not_dispatch_workflow() -> None:
    project = Path("C:/Users/maasa/research_x")
    bridge = load_project_bridge(project)

    state = build_workflow_artifact_audit(project, bridge)

    assert state["workflow_dispatch_executed"] is False
    assert state["github_actions_minutes_consumed_by_this_smoke"] is False
    assert state["github_api_write_executed"] is False
    assert state["deploy_executed"] is False
    assert state["paid_usage_detected"] is False


def test_subagent_runtime_dry_run_does_not_spawn_or_start_model_runner() -> None:
    policy = build_subagent_policy(allowed_roles=["ci_log_auditor"])

    state = build_subagent_runtime_dry_run(policy)

    assert state["dry_run_executed"] is True
    assert state["subagents_spawned"] is False
    assert state["model_runner_started"] is False
    assert state["provider_api_calls"] is False
    assert state["paid_usage_detected"] is False


def test_pages_readiness_can_use_gh_cli_for_local_settings_verification(
    monkeypatch,
) -> None:
    project = Path("C:/Users/maasa/research_x")
    profile = load_project_profile(project)
    bridge = load_project_bridge(project)

    def fake_get_json(url: str, *, timeout_seconds: float) -> dict:
        if url.endswith("/pages"):
            return {"ok": False, "status_code": 404, "payload": {}, "error": "Not Found"}
        return {
            "ok": True,
            "status_code": 200,
            "payload": {
                "private": False,
                "visibility": "public",
                "default_branch": "main",
            },
            "error": "",
        }

    def fake_get_gh_json(path: str, *, timeout_seconds: float) -> dict:
        return {
            "ok": True,
            "status_code": 200,
            "payload": {
                "html_url": "https://masanori64.github.io/research_x/",
                "build_type": "workflow",
                "source": {"branch": "main", "path": "/"},
            },
            "error": "",
        }

    monkeypatch.setattr(pages, "_get_json", fake_get_json)
    monkeypatch.setattr(pages, "_get_gh_json", fake_get_gh_json)

    state = build_pages_readiness_state(profile, bridge, execute=True)

    assert state["status"] == "passed"
    assert state["authentication"] == "gh_cli_local_verification"
    assert state["token_used"] is True
    assert state["pipeline_authentication_required"] == "none"
    assert state["pipeline_token_required"] is False
    assert state["free_static_cd"]["pages_source_setup_required"] is False
    assert state["paid_usage_detected"] is False
