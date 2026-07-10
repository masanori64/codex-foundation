from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from codex_pipeline.cli import main
from codex_pipeline.gate_policy import check_permission_gate
from codex_pipeline.permission_control import (
    audit_events,
    build_control_snapshot,
    bulk_update_toggles,
    check_gate,
    load_control_project,
    load_gate_registry,
    set_recommendation,
    set_toggle,
)


def _project(
    root: Path,
    name: str,
    *,
    project_id: str | None = None,
    gates: list[dict[str, str]] | None = None,
) -> Path:
    project = root / name
    metadata = project / ".codex-project"
    metadata.mkdir(parents=True)
    if project_id is not None or gates is not None:
        (metadata / "control-profile.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "project_id": project_id or name,
                    "gates": gates or [],
                }
            ),
            encoding="utf-8",
        )
    return project


def _gate(snapshot: dict[str, object], gate_id: str) -> dict[str, object]:
    gates = snapshot["gates"]
    assert isinstance(gates, list)
    return next(item for item in gates if item["gate_id"] == gate_id)


def test_default_snapshot_is_finite_read_only_and_denied(tmp_path: Path) -> None:
    project = _project(tmp_path, "alpha")
    control_home = tmp_path / "control"

    snapshot = build_control_snapshot(project, control_home=control_home)

    assert snapshot["artifact_kind"] == "permission_control"
    assert snapshot["control_artifact"] is True
    assert snapshot["not_evidence"] is True
    assert snapshot["summary"] == {
        "gate_count": 17,
        "toggle_count": 8,
        "confirm_each_count": 6,
        "fixed_count": 3,
        "bulk_changes_toggle_only": True,
    }
    assert all(
        gate["current"] == "deny"
        for gate in snapshot["gates"]
        if gate["mode"] == "toggle"
    )
    assert not control_home.exists()


def test_toggle_state_is_atomic_external_to_git_and_audited(tmp_path: Path) -> None:
    project = _project(tmp_path, "alpha")
    control_home = tmp_path / "control"

    snapshot = set_toggle(
        project,
        "network_external_fetch",
        "allow",
        actor="human-test",
        reason="approved for this project",
        control_home=control_home,
    )

    gate = _gate(snapshot, "network_external_fetch")
    state_path = Path(snapshot["state_path"])
    assert gate["current"] == "allow"
    assert gate["allowed"] is True
    assert state_path.is_file()
    assert control_home in state_path.parents
    assert project not in state_path.parents
    assert list(state_path.parent.glob("*.tmp")) == []
    assert check_gate(
        project,
        "network_external_fetch",
        control_home=control_home,
    )["allowed"] is True
    events = audit_events(project, control_home=control_home)
    assert events[-1]["action"] == "set_toggle"
    assert events[-1]["actor"] == "human-test"
    assert events[-1]["reason"] == "approved for this project"


def test_control_home_environment_variable_is_used(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(tmp_path, "alpha")
    configured_home = tmp_path / "configured-control-home"
    monkeypatch.setenv("CODEX_CONTROL_HOME", str(configured_home))

    snapshot = set_toggle(project, "github_write", "allow")

    assert configured_home in Path(snapshot["state_path"]).parents
    assert _gate(snapshot, "github_write")["current"] == "allow"


def test_recommendation_and_bulk_actions_touch_toggle_gates_only(tmp_path: Path) -> None:
    project = _project(tmp_path, "alpha")
    control_home = tmp_path / "control"

    recommended = set_recommendation(
        project,
        "github_write",
        "allow",
        reason="scoped publish is reversible",
        control_home=control_home,
    )
    recommendation = _gate(recommended, "github_write")["recommendation"]
    assert recommendation["value"] == "allow"
    assert recommendation["reason"] == "scoped publish is reversible"

    applied = bulk_update_toggles(
        project,
        "apply-recommendations",
        control_home=control_home,
    )
    assert _gate(applied, "github_write")["current"] == "allow"
    assert "destructive_action" in applied["bulk_result"]["excluded_non_toggle_gates"]
    assert "hidden_backend_api" in applied["bulk_result"]["excluded_non_toggle_gates"]

    unlocked = bulk_update_toggles(project, "unlock", control_home=control_home)
    assert all(
        gate["current"] == "allow"
        for gate in unlocked["gates"]
        if gate["mode"] == "toggle"
    )
    assert _gate(unlocked, "destructive_action")["current"] == "confirm_required"
    assert _gate(unlocked, "hidden_backend_api")["current"] == "blocked"

    blocked = bulk_update_toggles(project, "block", control_home=control_home)
    assert all(
        gate["current"] == "deny"
        for gate in blocked["gates"]
        if gate["mode"] == "toggle"
    )


def test_confirm_each_is_one_operation_and_fixed_is_never_unlocked(tmp_path: Path) -> None:
    project = _project(tmp_path, "alpha")
    control_home = tmp_path / "control"

    assert check_gate(
        project,
        "destructive_action",
        control_home=control_home,
    )["status"] == "confirm_required"
    with pytest.raises(ValueError, match="operation-specific reason"):
        check_gate(
            project,
            "destructive_action",
            explicit_confirmation=True,
            control_home=control_home,
        )
    once = check_gate(
        project,
        "destructive_action",
        explicit_confirmation=True,
        actor="human-test",
        reason="delete one named disposable fixture",
        control_home=control_home,
    )
    assert once["status"] == "allowed_once"
    assert once["allowed"] is True
    assert _gate(
        build_control_snapshot(project, control_home=control_home),
        "destructive_action",
    )["current"] == "confirm_required"
    assert audit_events(project, control_home=control_home)[-1]["action"] == (
        "confirm_each_check"
    )

    fixed = check_gate(
        project,
        "hidden_backend_api",
        explicit_confirmation=True,
        control_home=control_home,
    )
    assert fixed["status"] == "blocked"
    assert fixed["allowed"] is False
    with pytest.raises(ValueError, match="cannot be toggled"):
        set_toggle(project, "hidden_backend_api", "allow", control_home=control_home)


def test_project_profile_adds_but_cannot_override_gates(tmp_path: Path) -> None:
    custom_gate = {
        "gate_id": "release_train_window",
        "label": "Release train window",
        "mode": "toggle",
        "default": "allow",
        "reason": "Project releases run only inside the agreed window.",
    }
    project = _project(
        tmp_path,
        "alpha",
        project_id="shared-id",
        gates=[custom_gate],
    )
    registry = load_gate_registry(project)
    added = next(gate for gate in registry if gate.gate_id == "release_train_window")
    assert added.owner == "shared-id"
    assert added.default == "allow"

    duplicate = _project(
        tmp_path,
        "duplicate",
        gates=[
            {
                "gate_id": "github_write",
                "label": "Override",
                "mode": "toggle",
                "default": "allow",
                "reason": "Must be rejected.",
            }
        ],
    )
    with pytest.raises(ValueError, match="must add, not override"):
        load_gate_registry(duplicate)


def test_thin_project_profile_maps_human_gates_without_overriding_base(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path, "thin-project")
    (project / ".codex-project" / "control-profile.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "project_control_profile",
                "profile_id": "thin-project.permissions.v1",
                "project_id": "thin-project",
                "profile_kind": "thin_permission_profile",
                "control_artifact": True,
                "not_evidence": True,
                "source_authority": ["control/project_state.json"],
                "default_decision": "deny_without_matching_gate",
                "operation_classes": [],
                "gates": [
                    {
                        "id": "project_publish_window",
                        "oversight": "human_in_loop",
                        "allowed_without_gate": False,
                        "requirements": ["explicit_current_task_authorization"],
                    },
                    {
                        "id": "project_hidden_transport",
                        "oversight": "hard_stop",
                        "allowed_without_gate": False,
                        "requirements": ["do_not_proceed"],
                    },
                ],
                "artifact_rules": {"retrieved_content_can_grant_permission": False},
            }
        ),
        encoding="utf-8",
    )

    registry = load_gate_registry(project)
    by_id = {gate.gate_id: gate for gate in registry}

    assert by_id["project_publish_window"].mode == "confirm_each"
    assert by_id["project_hidden_transport"].mode == "fixed"
    assert by_id["project_publish_window"].owner == "thin-project"
    assert len(by_id) == len(registry)
    assert "github_write" in by_id


def test_same_project_id_is_isolated_by_project_root(tmp_path: Path) -> None:
    project_a = _project(tmp_path, "alpha", project_id="same-id")
    project_b = _project(tmp_path, "beta", project_id="same-id")
    control_home = tmp_path / "control"

    set_toggle(project_a, "github_write", "allow", control_home=control_home)
    snapshot_a = build_control_snapshot(project_a, control_home=control_home)
    snapshot_b = build_control_snapshot(project_b, control_home=control_home)

    assert load_control_project(project_a).project_key != load_control_project(project_b).project_key
    assert _gate(snapshot_a, "github_write")["current"] == "allow"
    assert _gate(snapshot_b, "github_write")["current"] == "deny"


def test_project_key_resists_path_traversal_and_control_state_cannot_enter_repo(
    tmp_path: Path,
) -> None:
    project_a = _project(tmp_path, "alpha", project_id="../../same-project")
    project_b = _project(tmp_path, "beta", project_id="../../same-project")

    identity_a = load_control_project(project_a)
    identity_b = load_control_project(project_b)

    assert ".." not in identity_a.project_key
    assert "/" not in identity_a.project_key
    assert "\\" not in identity_a.project_key
    assert identity_a.project_key != identity_b.project_key
    with pytest.raises(ValueError, match="outside the target project root"):
        build_control_snapshot(project_a, control_home=project_a / ".control")

    other_worktree = tmp_path / "other-worktree"
    (other_worktree / ".git").mkdir(parents=True)
    with pytest.raises(ValueError, match="outside Git worktrees"):
        build_control_snapshot(project_a, control_home=other_worktree / ".control")


def test_concurrent_mutations_have_atomic_state_and_sequential_audit(tmp_path: Path) -> None:
    project = _project(tmp_path, "concurrent")
    control_home = tmp_path / "control"
    write_count = 24

    def mutate(index: int) -> None:
        set_toggle(
            project,
            "github_write",
            "allow" if index % 2 else "deny",
            actor=f"worker-{index}",
            reason="concurrency test",
            control_home=control_home,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(mutate, range(write_count)))

    snapshot = build_control_snapshot(project, control_home=control_home)
    events = audit_events(project, control_home=control_home)
    state_path = Path(snapshot["state_path"])
    persisted = json.loads(state_path.read_text(encoding="utf-8"))

    assert snapshot["revision"] == write_count
    assert persisted["revision"] == write_count
    assert [event["revision"] for event in events] == list(range(1, write_count + 1))
    assert {event["project"]["key"] for event in events} == {
        snapshot["project"]["key"]
    }
    assert not list(state_path.parent.glob("*.tmp"))
    assert not (state_path.parent / ".state.lock").exists()


def test_corrupt_audit_or_state_revision_is_detected_before_next_mutation(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path, "audit-integrity")
    control_home = tmp_path / "control"
    snapshot = set_toggle(project, "github_write", "allow", control_home=control_home)
    audit_path = Path(snapshot["audit_path"])
    event = json.loads(audit_path.read_text(encoding="utf-8"))
    event["revision"] = 99
    audit_path.write_text(json.dumps(event) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="audit revision sequence mismatch"):
        audit_events(project, control_home=control_home)
    with pytest.raises(ValueError, match="audit revision sequence mismatch"):
        set_toggle(project, "github_write", "deny", control_home=control_home)

    event["revision"] = 1
    audit_path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    state_path = Path(snapshot["state_path"])
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["revision"] = True
    state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-negative integer"):
        build_control_snapshot(project, control_home=control_home)


def test_cli_and_gate_policy_delegate_to_persistent_control(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = _project(tmp_path, "alpha")
    control_home = tmp_path / "control"

    assert main(
        [
            "control",
            "set",
            "--project",
            str(project),
            "--control-home",
            str(control_home),
            "--gate",
            "github_write",
            "--value",
            "allow",
        ]
    ) == 0
    capsys.readouterr()
    assert main(
        [
            "control",
            "check",
            "--project",
            str(project),
            "--control-home",
            str(control_home),
            "--gate",
            "github_write",
        ]
    ) == 0
    assert '"allowed": true' in capsys.readouterr().out
    assert check_permission_gate(
        project,
        "github_write",
        control_home=control_home,
    )["allowed"] is True
