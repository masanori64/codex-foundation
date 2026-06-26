from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .foundation import control_marker

DEFAULT_STAGES = [
    {"id": "intake", "name": "Intake"},
    {"id": "plan", "name": "Plan"},
    {"id": "implement", "name": "Implement"},
    {"id": "verify", "name": "Verify"},
    {"id": "review", "name": "Review"},
    {"id": "release_ready", "name": "Release Ready"},
    {"id": "done", "name": "Done"},
    {"id": "gated", "name": "Gated"},
]

DEFAULT_TRANSITIONS = [
    {"from": "intake", "to": "plan"},
    {"from": "plan", "to": "implement"},
    {"from": "implement", "to": "verify"},
    {"from": "verify", "to": "review"},
    {"from": "review", "to": "release_ready"},
    {"from": "release_ready", "to": "done"},
    {"from": "plan", "to": "gated"},
    {"from": "implement", "to": "gated"},
    {"from": "verify", "to": "gated"},
]


def effective_pipeline(profile: Mapping[str, Any]) -> dict[str, Any]:
    marker = control_marker(artifact_kind="pipeline")
    return {
        "schema_version": 1,
        **marker,
        "project_id": profile["project"]["id"],
        "stages": DEFAULT_STAGES,
        "transitions": DEFAULT_TRANSITIONS,
        "lanes": [
            {"id": "local_validation", "name": "Local Validation", "automatic": True},
            {"id": "dashboard", "name": "Dashboard Generation", "automatic": True},
            {"id": "pages_dashboard", "name": "Pages Dashboard CD", "automatic": True},
            {"id": "preview", "name": "Preview Static CD", "automatic": True},
            {"id": "staging", "name": "Staging Static CD", "automatic": True},
            {"id": "production", "name": "Production Static CD", "automatic": True},
            {"id": "rollback", "name": "Safe Static Rollback", "automatic": False},
        ],
    }


def render_pipeline_mermaid(pipeline: Mapping[str, Any]) -> str:
    lines = ["flowchart LR"]
    for stage in pipeline["stages"]:
        lines.append(f'  {stage["id"]}["{_escape_label(stage.get("name", stage["id"]))}"]')
    for transition in pipeline["transitions"]:
        lines.append(f'  {transition["from"]} --> {transition["to"]}')
    lines.append('  note["control artifact / not evidence / not citation"]')
    lines.append("  note -.-> intake")
    return "\n".join(lines) + "\n"


def render_ci_cd_lanes_mermaid(pipeline: Mapping[str, Any]) -> str:
    lines = ["flowchart TD"]
    previous = None
    for lane in pipeline["lanes"]:
        node_id = lane["id"]
        label = f'{lane["name"]}\\nautomatic={str(lane["automatic"]).lower()}'
        lines.append(f'  {node_id}["{_escape_label(label)}"]')
        if previous:
            lines.append(f"  {previous} --> {node_id}")
        previous = node_id
    lines.append('  paid_gate["paid provider/API/quota boundary\\nnot part of free CD"]')
    lines.append("  production -. outside free static CD .-> paid_gate")
    return "\n".join(lines) + "\n"


def render_rollback_mermaid() -> str:
    return "\n".join(
        [
            "flowchart LR",
            '  current["current Pages static site"]',
            '  manifest["rollback manifest\\nsafe_static_pages"]',
            '  previous["previous known-good Pages snapshot"]',
            '  deploy["deploy previous static snapshot"]',
            "  current --> manifest --> previous",
            "  previous --> deploy",
            '  notice["control artifact / not evidence / not citation"]',
            "  notice -.-> manifest",
            "",
        ]
    )


def _escape_label(value: object) -> str:
    return str(value).replace('"', "'")
