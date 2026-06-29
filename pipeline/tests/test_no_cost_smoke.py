from __future__ import annotations

from pathlib import Path

from codex_pipeline import pages
from codex_pipeline.bridge_loader import load_project_bridge
from codex_pipeline.cost_guard import build_cost_guard_state
from codex_pipeline.github_read_collector import _parse_github_repo, build_github_read_state
from codex_pipeline.pages import build_pages_readiness_state
from codex_pipeline.profile_loader import load_project_profile
from codex_pipeline.subagent_governance import build_subagent_policy
from codex_pipeline.subagent_runtime import (
    build_subagent_report_validation,
    build_subagent_runtime_dry_run,
)
from codex_pipeline.workflow_artifact_audit import build_workflow_artifact_audit
from codex_pipeline.workflow_wrappers import generate_workflow_wrappers


def test_no_cost_guard_has_no_paid_execution(codex_project: Path) -> None:
    profile = load_project_profile(codex_project)
    bridge = load_project_bridge(codex_project)

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


def test_github_read_placeholder_is_read_only_and_no_secret(codex_project: Path) -> None:
    bridge = load_project_bridge(codex_project)

    state = build_github_read_state(codex_project, bridge, execute=False)

    assert state["api_calls_executed"] is False
    assert state["authentication"] == "none"
    assert state["token_used"] is False
    assert state["write_operations_available"] is False
    assert state["mutation_methods_available"] == []
    assert state["paid_usage_detected"] is False


def test_github_read_repo_parser_accepts_github_remote_formats() -> None:
    assert _parse_github_repo("git@github.com:masanori64/codex-foundation.git") == (
        "masanori64/codex-foundation"
    )
    assert _parse_github_repo("https://github.com/masanori64/codex-foundation.git") == (
        "masanori64/codex-foundation"
    )
    assert _parse_github_repo("ssh://git@github.com/masanori64/codex-foundation.git") == (
        "masanori64/codex-foundation"
    )


def test_github_read_repo_parser_rejects_spoofed_github_substrings() -> None:
    remotes = [
        "https://example.test/next=https://github.com/masanori64/codex-foundation.git",
        "https://github.com.example.test/masanori64/codex-foundation.git",
        "ssh://git@github.com.example.test/masanori64/codex-foundation.git",
        "git@example.test:masanori64/codex-foundation.git",
    ]

    for remote in remotes:
        assert _parse_github_repo(remote) == ""


def test_workflow_artifact_audit_does_not_dispatch_workflow(codex_project: Path) -> None:
    generate_workflow_wrappers(codex_project)
    bridge = load_project_bridge(codex_project)

    state = build_workflow_artifact_audit(codex_project, bridge)

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


def test_subagent_report_validation_rejects_mutating_or_raw_log_reports() -> None:
    policy = build_subagent_policy(allowed_roles=["ci_log_auditor"])
    report = {
        "agent": "ci_log_auditor",
        "mode": "read_only",
        "status": "passed",
        "summary": "reviewed logs",
        "control_artifact": True,
        "not_evidence": True,
        "not_citation": True,
        "raw_log_in_project": True,
        "forbidden_actions_executed": ["push"],
        "provider_api_calls": False,
        "paid_usage_detected": False,
        "secrets_used": False,
    }

    state = build_subagent_report_validation(report, policy)

    assert state["status"] == "failed"
    assert state["subagents_spawned_by_validator"] is False
    assert state["provider_api_calls"] is False
    assert "subagent report raw_log_in_project must be false" in state["errors"]
    assert "subagent report must not execute forbidden actions" in state["errors"]


def test_pages_readiness_can_use_gh_cli_for_local_settings_verification(
    monkeypatch,
    codex_project: Path,
) -> None:
    profile = load_project_profile(codex_project)
    bridge = load_project_bridge(codex_project)

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
