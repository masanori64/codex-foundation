from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .simple_yaml import load_structured_file

PIPELINE_ROOT = Path(__file__).resolve().parents[2]
POLICY_ROOT = PIPELINE_ROOT / "policies"

BLOCKING_GATES = {
    "provider_api_quota": (
        "Provider/API/quota use, including paid, free-tier, trial-credit, "
        "or zero-dollar quota."
    ),
    "secrets_credentials": (
        "Secrets, credentials, PATs, deploy keys, environment secrets, or account login."
    ),
    "mcp_plugin_hook_enablement": "MCP, plugin, connector, or hook enablement/change.",
    "destructive_action": (
        "Delete, purge, force-push, irreversible overwrite, or destructive data action."
    ),
    "irreversible_db_migration": (
        "DB migration or data mutation that cannot be rolled back automatically."
    ),
    "production_external_side_effect": (
        "Production action with external side effects beyond safe static deploy."
    ),
}

DEFAULT_CAPABILITIES = {
    "github_api_read": "disabled",
    "github_api_write": "disabled",
    "github_actions_wrappers": "disabled",
    "dashboard_artifact_cd": "disabled",
    "preview_cd": "disabled",
    "staging_cd": "disabled",
    "production_cd": "disabled",
    "rollback_execution": "disabled",
    "github_pages": "disabled",
    "repository_settings_change": "disabled",
    "provider_api_calls": "disabled",
    "mcp_plugin_hook_enablement": "disabled",
}


@dataclass(frozen=True)
class GateStatus:
    gate_id: str
    status: str
    severity: str
    reason: str
    allowed_without_gate: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_gate_policy() -> dict[str, Any]:
    path = POLICY_ROOT / "hotl-gates.yml"
    return load_structured_file(path)


def phase_1_gate_statuses() -> list[GateStatus]:
    return [
        GateStatus(
            gate_id=gate_id,
            status="requires_explicit_user_gate",
            severity="blocking",
            reason=reason,
            allowed_without_gate=False,
        )
        for gate_id, reason in BLOCKING_GATES.items()
    ]


def capability_statuses(overrides: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    values = dict(DEFAULT_CAPABILITIES)
    if overrides:
        for key, value in overrides.items():
            values[str(key)] = str(value)
    return [
        {
            "capability_id": key,
            "status": status,
            "allowed_without_gate": _allowed_without_gate(status),
            "reason": _capability_reason(key, status),
        }
        for key, status in values.items()
    ]


def _capability_reason(key: str, status: str) -> str:
    if status == "disabled":
        return (
            "Disabled by default for Phase 2 hardening; "
            "explicit gate required before enablement."
        )
    if status == "hard_blocked_paid":
        return (
            f"Capability {key} is a paid/quota boundary and is not part of the "
            "completed free static Pages CD pipeline."
        )
    if status == "outside_free_static_pages_cd":
        return (
            f"Capability {key} is not used by the completed free static Pages CD "
            "pipeline and is not an active completion blocker."
        )
    if status in {
        "enabled",
        "public_read_enabled",
        "pages_static_cd_only",
        "static_pages_lane_enabled",
        "static_pages_enabled",
        "safe_static_pages_enabled",
        "enabled_public_static",
        "free_pages_source_setup_only",
    }:
        return (
            f"Capability {key} is allowed for free public static Pages CD; "
            "paid/provider/secret/DB paths remain forbidden."
        )
    return f"Capability {key} is {status}; verify gate policy before use."


def _allowed_without_gate(status: str) -> bool:
    return status in {
        "enabled",
        "public_read_enabled",
        "pages_static_cd_only",
        "static_pages_lane_enabled",
        "static_pages_enabled",
        "safe_static_pages_enabled",
        "enabled_public_static",
        "free_pages_source_setup_only",
    }


def check_requested_actions(actions: list[str]) -> list[GateStatus]:
    normalized = {action.casefold().replace("-", "_") for action in actions}
    hits = []
    for gate_id, reason in BLOCKING_GATES.items():
        if gate_id in normalized:
            hits.append(
                GateStatus(
                    gate_id=gate_id,
                    status="blocked",
                    severity="blocking",
                    reason=reason,
                    allowed_without_gate=False,
                )
            )
    return hits
