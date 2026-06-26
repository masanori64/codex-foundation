from __future__ import annotations

from codex_pipeline.gate_policy import (
    capability_statuses,
    check_requested_actions,
    phase_1_gate_statuses,
)


def test_phase_1_exposes_blocking_hotl_gates() -> None:
    gates = phase_1_gate_statuses()
    gate_ids = {gate.gate_id for gate in gates}

    assert "provider_api_quota" in gate_ids
    assert "secrets_credentials" in gate_ids
    assert "mcp_plugin_hook_enablement" in gate_ids
    assert "github_pages_enablement" not in gate_ids
    assert all(gate.allowed_without_gate is False for gate in gates)


def test_requested_provider_action_is_blocked() -> None:
    hits = check_requested_actions(["provider_api_quota"])

    assert hits[0].status == "blocked"
    assert hits[0].severity == "blocking"


def test_capabilities_are_disabled_by_default() -> None:
    capabilities = capability_statuses()
    statuses = {item["capability_id"]: item["status"] for item in capabilities}

    enabled = capability_statuses(
        {
            "production_cd": "static_pages_enabled",
            "rollback_execution": "safe_static_pages_enabled",
            "github_pages": "enabled_public_static",
        }
    )
    enabled_by_id = {item["capability_id"]: item for item in enabled}

    assert statuses["production_cd"] == "disabled"
    assert statuses["rollback_execution"] == "disabled"
    assert statuses["github_pages"] == "disabled"
    assert enabled_by_id["production_cd"]["allowed_without_gate"] is True
    assert enabled_by_id["rollback_execution"]["allowed_without_gate"] is True
    assert enabled_by_id["github_pages"]["allowed_without_gate"] is True
