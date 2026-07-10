from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import time
import uuid
from collections.abc import Callable, Iterator, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .foundation import PIPELINE_ROOT, control_marker
from .simple_yaml import load_structured_file

CONTROL_HOME_ENV = "CODEX_CONTROL_HOME"
CONTROL_PROFILE_RELATIVE_PATH = Path(".codex-project") / "control-profile.json"
PROJECT_PROFILE_RELATIVE_PATH = Path(".codex-project") / "profile.yml"
REGISTRY_PATH = PIPELINE_ROOT / "policies" / "permission-control-registry.json"

GATE_MODES = frozenset({"toggle", "confirm_each", "fixed"})
TOGGLE_VALUES = frozenset({"allow", "deny"})
GATE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
LOCK_WAIT_SECONDS = 5.0
STALE_LOCK_SECONDS = 30.0


@dataclass(frozen=True)
class GateDefinition:
    gate_id: str
    label: str
    mode: str
    reason: str
    default: str | None
    owner: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ControlProject:
    project_id: str
    project_root: Path
    project_key: str
    control_profile_path: Path

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.project_id,
            "root": str(self.project_root),
            "key": self.project_key,
            "control_profile": str(self.control_profile_path),
            "control_profile_exists": self.control_profile_path.exists(),
        }


def control_home_path(control_home: str | Path | None = None) -> Path:
    if control_home is not None:
        return Path(control_home).expanduser().resolve()
    configured = os.environ.get(CONTROL_HOME_ENV, "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex" / "control").resolve()


def load_control_project(project_root: str | Path) -> ControlProject:
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"project root not found: {root}")
    control_profile_path = root / CONTROL_PROFILE_RELATIVE_PATH
    control_profile = _load_control_profile(control_profile_path)
    profile_project_id = _project_id_from_existing_profile(root)
    control_project_id = str(control_profile.get("project_id") or "").strip()
    if profile_project_id and control_project_id and profile_project_id != control_project_id:
        raise ValueError(
            "control profile project_id does not match .codex-project/profile.yml: "
            f"{control_project_id!r} != {profile_project_id!r}"
        )
    project_id = control_project_id or profile_project_id or root.name
    if not project_id:
        raise ValueError("project_id must not be empty")
    normalized_root = os.path.normcase(str(root))
    root_hash = hashlib.sha256(normalized_root.encode("utf-8")).hexdigest()[:32]
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "-", project_id).strip("-.") or "project"
    safe_id = safe_id[:80].rstrip("-.") or "project"
    return ControlProject(
        project_id=project_id,
        project_root=root,
        project_key=f"{safe_id}-{root_hash}",
        control_profile_path=control_profile_path,
    )


def load_gate_registry(project_root: str | Path) -> tuple[GateDefinition, ...]:
    project = load_control_project(project_root)
    registry = _load_json_object(REGISTRY_PATH, label="permission control registry")
    if registry.get("schema_version") != 1:
        raise ValueError("permission control registry schema_version must be 1")
    if registry.get("registry_id") != "codex-permission-control-v1":
        raise ValueError("permission control registry_id is invalid")
    raw_gates = registry.get("gates")
    if not isinstance(raw_gates, list) or not raw_gates:
        raise ValueError("permission control registry must contain a finite non-empty gates list")
    definitions = [_gate_from_raw(raw, owner="foundation") for raw in raw_gates]
    seen = {gate.gate_id for gate in definitions}
    if len(seen) != len(definitions):
        raise ValueError("permission control registry contains duplicate gate_id values")

    profile = _load_control_profile(project.control_profile_path)
    for raw in profile.get("gates", []):
        gate = _gate_from_raw(raw, owner=project.project_id)
        if gate.gate_id in seen:
            raise ValueError(
                f"project control profile must add, not override, gate {gate.gate_id!r}"
            )
        definitions.append(gate)
        seen.add(gate.gate_id)
    return tuple(definitions)


def build_control_snapshot(
    project_root: str | Path,
    *,
    control_home: str | Path | None = None,
) -> dict[str, Any]:
    project = load_control_project(project_root)
    registry = load_gate_registry(project.project_root)
    home = control_home_path(control_home)
    paths = _project_paths(project, home)
    state = _load_state(paths["state"], project=project, registry=registry)
    gates = []
    toggle_count = 0
    for gate in registry:
        recommendation = state["recommendations"].get(gate.gate_id)
        if gate.mode == "toggle":
            toggle_count += 1
            current = state["toggles"][gate.gate_id]
            allowed = current == "allow"
        elif gate.mode == "confirm_each":
            current = "confirm_required"
            allowed = False
        else:
            current = "blocked"
            allowed = False
        gates.append(
            {
                **gate.as_dict(),
                "current": current,
                "allowed": allowed,
                "recommendation": recommendation,
                "bulk_eligible": gate.mode == "toggle",
            }
        )
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="permission_control"),
        "registry_id": "codex-permission-control-v1",
        "project": project.as_dict(),
        "control_home": str(home),
        "state_path": str(paths["state"]),
        "audit_path": str(paths["audit"]),
        "revision": state["revision"],
        "updated_at": state["updated_at"],
        "gates": gates,
        "summary": {
            "gate_count": len(gates),
            "toggle_count": toggle_count,
            "confirm_each_count": sum(gate.mode == "confirm_each" for gate in registry),
            "fixed_count": sum(gate.mode == "fixed" for gate in registry),
            "bulk_changes_toggle_only": True,
        },
    }


def check_gate(
    project_root: str | Path,
    gate_id: str,
    *,
    explicit_confirmation: bool = False,
    actor: str = "human",
    reason: str = "",
    control_home: str | Path | None = None,
) -> dict[str, Any]:
    project = load_control_project(project_root)
    registry = {gate.gate_id: gate for gate in load_gate_registry(project.project_root)}
    gate = _required_gate(registry, gate_id)
    snapshot = build_control_snapshot(project.project_root, control_home=control_home)
    current = next(item for item in snapshot["gates"] if item["gate_id"] == gate_id)
    if gate.mode == "toggle":
        status = "allowed" if current["current"] == "allow" else "denied"
        allowed = status == "allowed"
    elif gate.mode == "confirm_each":
        if explicit_confirmation and not reason.strip():
            raise ValueError("confirm_each approval requires an operation-specific reason")
        allowed = explicit_confirmation
        status = "allowed_once" if allowed else "confirm_required"
        if allowed:
            _append_check_confirmation(
                project,
                gate,
                tuple(registry.values()),
                actor=actor,
                reason=reason,
                control_home=control_home,
            )
    else:
        status = "blocked"
        allowed = False
    return {
        "schema_version": 1,
        "project": project.as_dict(),
        "gate": current,
        "status": status,
        "allowed": allowed,
        "explicit_confirmation_used": gate.mode == "confirm_each" and allowed,
    }


def set_toggle(
    project_root: str | Path,
    gate_id: str,
    value: str,
    *,
    actor: str = "human",
    reason: str = "",
    control_home: str | Path | None = None,
) -> dict[str, Any]:
    decision = _toggle_value(value)
    project = load_control_project(project_root)
    registry = {gate.gate_id: gate for gate in load_gate_registry(project.project_root)}
    gate = _required_gate(registry, gate_id)
    if gate.mode != "toggle":
        raise ValueError(f"gate {gate_id!r} has mode {gate.mode!r} and cannot be toggled")

    def mutation(state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        previous = state["toggles"][gate_id]
        state["toggles"][gate_id] = decision
        return state, {
            "action": "set_toggle",
            "gate_id": gate_id,
            "previous": previous,
            "new": decision,
            "actor": actor,
            "reason": reason,
        }

    _mutate_project_state(project, tuple(registry.values()), mutation, control_home=control_home)
    return build_control_snapshot(project.project_root, control_home=control_home)


def set_recommendation(
    project_root: str | Path,
    gate_id: str,
    value: str,
    *,
    reason: str,
    actor: str = "codex",
    control_home: str | Path | None = None,
) -> dict[str, Any]:
    decision = _toggle_value(value)
    if not reason.strip():
        raise ValueError("recommendation reason is required")
    project = load_control_project(project_root)
    registry = {gate.gate_id: gate for gate in load_gate_registry(project.project_root)}
    gate = _required_gate(registry, gate_id)
    if gate.mode != "toggle":
        raise ValueError(f"gate {gate_id!r} has mode {gate.mode!r} and cannot be recommended")
    now = _utc_now()

    def mutation(state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        previous = state["recommendations"].get(gate_id)
        recommendation = {
            "value": decision,
            "reason": reason.strip(),
            "actor": actor,
            "updated_at": now,
        }
        state["recommendations"][gate_id] = recommendation
        return state, {
            "action": "set_recommendation",
            "gate_id": gate_id,
            "previous": previous,
            "new": recommendation,
            "actor": actor,
            "reason": reason.strip(),
        }

    _mutate_project_state(project, tuple(registry.values()), mutation, control_home=control_home)
    return build_control_snapshot(project.project_root, control_home=control_home)


def bulk_update_toggles(
    project_root: str | Path,
    action: str,
    *,
    actor: str = "human",
    reason: str = "",
    control_home: str | Path | None = None,
) -> dict[str, Any]:
    normalized_action = action.strip().casefold().replace("_", "-")
    normalized_action = {"unlock": "allow", "block": "deny"}.get(
        normalized_action,
        normalized_action,
    )
    if normalized_action not in {"allow", "deny", "apply-recommendations"}:
        raise ValueError("bulk action must be allow, deny, or apply-recommendations")
    project = load_control_project(project_root)
    registry = load_gate_registry(project.project_root)
    toggles = tuple(gate for gate in registry if gate.mode == "toggle")
    excluded = tuple(gate.gate_id for gate in registry if gate.mode != "toggle")

    def mutation(state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        changes: dict[str, dict[str, str]] = {}
        for gate in toggles:
            if normalized_action == "apply-recommendations":
                recommendation = state["recommendations"].get(gate.gate_id)
                if not recommendation:
                    continue
                target = recommendation["value"]
            else:
                target = normalized_action
            previous = state["toggles"][gate.gate_id]
            state["toggles"][gate.gate_id] = target
            if previous != target:
                changes[gate.gate_id] = {"previous": previous, "new": target}
        return state, {
            "action": f"bulk_{normalized_action}",
            "gate_id": None,
            "previous": None,
            "new": changes,
            "actor": actor,
            "reason": reason,
            "excluded_non_toggle_gates": list(excluded),
        }

    _mutate_project_state(project, registry, mutation, control_home=control_home)
    snapshot = build_control_snapshot(project.project_root, control_home=control_home)
    snapshot["bulk_result"] = {
        "action": normalized_action,
        "excluded_non_toggle_gates": list(excluded),
    }
    return snapshot


def audit_events(
    project_root: str | Path,
    *,
    control_home: str | Path | None = None,
) -> tuple[dict[str, Any], ...]:
    project = load_control_project(project_root)
    registry = load_gate_registry(project.project_root)
    paths = _project_paths(project, control_home_path(control_home))
    if not paths["directory"].exists():
        return ()
    with _project_lock(paths["lock"]):
        state = _load_state(paths["state"], project=project, registry=registry)
        return _validated_audit_events(
            paths["audit"],
            project=project,
            expected_revision=state["revision"],
        )


def _mutate_project_state(
    project: ControlProject,
    registry: tuple[GateDefinition, ...],
    mutation: Callable[[dict[str, Any]], tuple[dict[str, Any], dict[str, Any]]],
    *,
    control_home: str | Path | None,
) -> None:
    paths = _project_paths(project, control_home_path(control_home))
    paths["directory"].mkdir(parents=True, exist_ok=True)
    with _project_lock(paths["lock"]):
        state = _load_state(paths["state"], project=project, registry=registry)
        _validated_audit_events(
            paths["audit"],
            project=project,
            expected_revision=state["revision"],
        )
        next_state, audit = mutation(state)
        now = _utc_now()
        next_state["revision"] = int(state["revision"]) + 1
        next_state["updated_at"] = now
        _atomic_write_json(paths["state"], next_state)
        _append_audit(
            paths["audit"],
            {
                "schema_version": 1,
                "event_id": uuid.uuid4().hex,
                "created_at": now,
                "project": project.as_dict(),
                "revision": next_state["revision"],
                **audit,
            },
        )


def _append_check_confirmation(
    project: ControlProject,
    gate: GateDefinition,
    registry: tuple[GateDefinition, ...],
    *,
    actor: str,
    reason: str,
    control_home: str | Path | None,
) -> None:
    paths = _project_paths(project, control_home_path(control_home))
    paths["directory"].mkdir(parents=True, exist_ok=True)
    with _project_lock(paths["lock"]):
        state = _load_state(paths["state"], project=project, registry=registry)
        _validated_audit_events(
            paths["audit"],
            project=project,
            expected_revision=state["revision"],
        )
        _append_audit(
            paths["audit"],
            {
                "schema_version": 1,
                "event_id": uuid.uuid4().hex,
                "created_at": _utc_now(),
                "project": project.as_dict(),
                "revision": None,
                "action": "confirm_each_check",
                "gate_id": gate.gate_id,
                "previous": "confirm_required",
                "new": "allowed_once",
                "actor": actor,
                "reason": reason,
            },
        )


def _load_state(
    path: Path,
    *,
    project: ControlProject,
    registry: tuple[GateDefinition, ...],
) -> dict[str, Any]:
    defaults = {
        gate.gate_id: gate.default or "deny" for gate in registry if gate.mode == "toggle"
    }
    if not path.exists():
        return {
            "schema_version": 1,
            "project": project.as_dict(),
            "revision": 0,
            "updated_at": None,
            "toggles": defaults,
            "recommendations": {},
        }
    state = _load_json_object(path, label="permission control state")
    if state.get("schema_version") != 1:
        raise ValueError("permission control state schema_version must be 1")
    stored_project = state.get("project")
    if not isinstance(stored_project, Mapping) or stored_project.get("key") != project.project_key:
        raise ValueError("permission control state project identity mismatch")
    toggles = state.get("toggles")
    recommendations = state.get("recommendations")
    if not isinstance(toggles, dict) or not isinstance(recommendations, dict):
        raise ValueError("permission control state toggles and recommendations must be objects")
    reconciled_toggles = dict(defaults)
    for gate_id, value in toggles.items():
        if gate_id in defaults:
            reconciled_toggles[gate_id] = _toggle_value(str(value))
    allowed_toggle_ids = set(defaults)
    reconciled_recommendations = {}
    for gate_id, recommendation in recommendations.items():
        if gate_id not in allowed_toggle_ids or not isinstance(recommendation, dict):
            continue
        value = _toggle_value(str(recommendation.get("value", "")))
        reason = str(recommendation.get("reason") or "").strip()
        if not reason:
            continue
        reconciled_recommendations[gate_id] = {
            "value": value,
            "reason": reason,
            "actor": str(recommendation.get("actor") or "codex"),
            "updated_at": recommendation.get("updated_at"),
        }
    revision = state.get("revision", 0)
    if type(revision) is not int or revision < 0:
        raise ValueError("permission control state revision must be a non-negative integer")
    return {
        "schema_version": 1,
        "project": project.as_dict(),
        "revision": revision,
        "updated_at": state.get("updated_at"),
        "toggles": reconciled_toggles,
        "recommendations": reconciled_recommendations,
    }


def _project_paths(project: ControlProject, home: Path) -> dict[str, Path]:
    directory = (home / "projects" / project.project_key).resolve()
    if directory == project.project_root or directory.is_relative_to(project.project_root):
        raise ValueError(
            "permission control state must remain outside the target project root: "
            f"{directory}"
        )
    git_worktree = next(
        (
            candidate
            for candidate in (directory, *directory.parents)
            if (candidate / ".git").exists()
        ),
        None,
    )
    if git_worktree is not None:
        raise ValueError(
            "permission control state must remain outside Git worktrees: "
            f"{git_worktree}"
        )
    return {
        "directory": directory,
        "state": directory / "state.json",
        "audit": directory / "audit.jsonl",
        "lock": directory / ".state.lock",
    }


@contextlib.contextmanager
def _project_lock(path: Path) -> Iterator[None]:
    deadline = time.monotonic() + LOCK_WAIT_SECONDS
    descriptor: int | None = None
    while descriptor is None:
        try:
            candidate = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(candidate, f"pid={os.getpid()} created_at={_utc_now()}\n".encode())
            except BaseException:
                os.close(candidate)
                with contextlib.suppress(FileNotFoundError):
                    path.unlink()
                raise
            descriptor = candidate
        except (FileExistsError, PermissionError):
            try:
                age = time.time() - path.stat().st_mtime
            except FileNotFoundError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"timed out acquiring permission control lock: {path}"
                    ) from None
                time.sleep(0.02)
                continue
            if age > STALE_LOCK_SECONDS:
                with contextlib.suppress(FileNotFoundError):
                    path.unlink()
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"timed out waiting for permission control lock: {path}"
                ) from None
            time.sleep(0.02)
    try:
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        with contextlib.suppress(FileNotFoundError):
            path.unlink()


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def _append_audit(path: Path, event: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _validated_audit_events(
    path: Path,
    *,
    project: ControlProject,
    expected_revision: int,
) -> tuple[dict[str, Any], ...]:
    if not path.exists():
        if expected_revision:
            raise ValueError(
                "permission control audit is missing for persisted state revision "
                f"{expected_revision}"
            )
        return ()
    events = []
    event_ids: set[str] = set()
    revisions: list[int] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid control audit JSONL at line {line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"invalid control audit JSONL object at line {line_number}")
        if event.get("schema_version") != 1:
            raise ValueError(f"invalid control audit schema_version at line {line_number}")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id or event_id in event_ids:
            raise ValueError(f"invalid or duplicate control audit event_id at line {line_number}")
        event_ids.add(event_id)
        event_project = event.get("project")
        if not isinstance(event_project, Mapping) or event_project.get("key") != project.project_key:
            raise ValueError(f"control audit project identity mismatch at line {line_number}")
        revision = event.get("revision")
        if revision is not None:
            if type(revision) is not int or revision <= 0:
                raise ValueError(f"invalid control audit revision at line {line_number}")
            revisions.append(revision)
        events.append(event)
    expected_revisions = list(range(1, expected_revision + 1))
    if revisions != expected_revisions:
        raise ValueError(
            "permission control audit revision sequence mismatch: "
            f"expected={expected_revisions} actual={revisions}"
        )
    return tuple(events)


def _load_control_profile(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "project_id": "", "gates": []}
    profile = _load_json_object(path, label="project control profile")
    if profile.get("schema_version") != 1:
        raise ValueError("project control profile schema_version must be 1")
    if profile.get("profile_kind") == "thin_permission_profile":
        return _normalize_thin_control_profile(profile)
    allowed_keys = {"schema_version", "project_id", "gates"}
    unexpected = sorted(set(profile) - allowed_keys)
    if unexpected:
        raise ValueError("project control profile has unknown fields: " + ", ".join(unexpected))
    if not isinstance(profile.get("project_id"), str) or not profile["project_id"].strip():
        raise ValueError("project control profile project_id is required")
    gates = profile.get("gates")
    if not isinstance(gates, list):
        raise ValueError("project control profile gates must be a finite list")
    return profile


def _normalize_thin_control_profile(profile: dict[str, Any]) -> dict[str, Any]:
    allowed_keys = {
        "schema_version",
        "artifact_kind",
        "profile_id",
        "project_id",
        "profile_kind",
        "control_artifact",
        "not_evidence",
        "source_authority",
        "default_decision",
        "operation_classes",
        "gates",
        "artifact_rules",
    }
    unexpected = sorted(set(profile) - allowed_keys)
    if unexpected:
        raise ValueError("thin control profile has unknown fields: " + ", ".join(unexpected))
    project_id = profile.get("project_id")
    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("thin control profile project_id is required")
    if profile.get("control_artifact") is not True or profile.get("not_evidence") is not True:
        raise ValueError("thin control profile must be a non-evidence control artifact")
    raw_gates = profile.get("gates")
    if not isinstance(raw_gates, list):
        raise ValueError("thin control profile gates must be a finite list")

    gates: list[dict[str, Any]] = []
    mode_by_oversight = {"human_in_loop": "confirm_each", "hard_stop": "fixed"}
    for raw in raw_gates:
        if not isinstance(raw, dict):
            raise ValueError("every thin permission gate must be an object")
        unexpected_gate_fields = sorted(
            set(raw) - {"id", "oversight", "allowed_without_gate", "requirements"}
        )
        if unexpected_gate_fields:
            raise ValueError(
                "thin permission gate has unknown fields: "
                + ", ".join(unexpected_gate_fields)
            )
        gate_id = raw.get("id")
        oversight = raw.get("oversight")
        requirements = raw.get("requirements")
        if not isinstance(gate_id, str) or not GATE_ID_PATTERN.fullmatch(gate_id):
            raise ValueError(f"invalid thin permission gate id: {gate_id!r}")
        if oversight not in mode_by_oversight:
            raise ValueError(
                f"thin permission gate {gate_id!r} has unsupported oversight {oversight!r}"
            )
        if raw.get("allowed_without_gate") is not False:
            raise ValueError(
                f"thin permission gate {gate_id!r} must not be allowed without a gate"
            )
        if (
            not isinstance(requirements, list)
            or not requirements
            or not all(isinstance(item, str) and item.strip() for item in requirements)
        ):
            raise ValueError(
                f"thin permission gate {gate_id!r} requires a non-empty requirements list"
            )
        mode = mode_by_oversight[oversight]
        prefix = (
            "Operation-specific human confirmation required."
            if mode == "confirm_each"
            else "Hard stop; this project profile does not authorize the operation."
        )
        gates.append(
            {
                "gate_id": gate_id,
                "label": gate_id.replace("_", " ").capitalize(),
                "mode": mode,
                "reason": f"{prefix} Requirements: {', '.join(requirements)}.",
            }
        )
    return {
        "schema_version": 1,
        "project_id": project_id.strip(),
        "gates": gates,
    }


def _project_id_from_existing_profile(root: Path) -> str:
    path = root / PROJECT_PROFILE_RELATIVE_PATH
    if not path.exists():
        return ""
    data = load_structured_file(path)
    project = data.get("project")
    if not isinstance(project, dict):
        return ""
    return str(project.get("id") or "").strip()


def _gate_from_raw(raw: Any, *, owner: str) -> GateDefinition:
    if not isinstance(raw, dict):
        raise ValueError("every permission gate must be an object")
    allowed_keys = {"gate_id", "label", "mode", "reason", "default"}
    unexpected = sorted(set(raw) - allowed_keys)
    if unexpected:
        raise ValueError("permission gate has unknown fields: " + ", ".join(unexpected))
    for field in ("gate_id", "label", "mode", "reason"):
        if not isinstance(raw.get(field), str):
            raise ValueError(f"permission gate field {field!r} must be a string")
    raw_default = raw.get("default")
    if raw_default is not None and not isinstance(raw_default, str):
        raise ValueError("permission gate field 'default' must be a string")
    gate_id = raw["gate_id"].strip()
    label = raw["label"].strip()
    mode = raw["mode"].strip()
    reason = raw["reason"].strip()
    default = raw_default.strip() if raw_default is not None else None
    default = default or None
    if not GATE_ID_PATTERN.fullmatch(gate_id):
        raise ValueError(f"invalid permission gate_id: {gate_id!r}")
    if not label or not reason:
        raise ValueError(f"permission gate {gate_id!r} requires label and reason")
    if mode not in GATE_MODES:
        raise ValueError(f"permission gate {gate_id!r} has invalid mode {mode!r}")
    if mode == "toggle":
        default = _toggle_value(default or "deny")
    elif default is not None:
        raise ValueError(f"permission gate {gate_id!r} may set default only in toggle mode")
    return GateDefinition(
        gate_id=gate_id,
        label=label,
        mode=mode,
        reason=reason,
        default=default,
        owner=owner,
    )


def _required_gate(registry: Mapping[str, GateDefinition], gate_id: str) -> GateDefinition:
    try:
        return registry[gate_id]
    except KeyError as exc:
        raise KeyError(f"unknown permission gate: {gate_id}") from exc


def _toggle_value(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized not in TOGGLE_VALUES:
        raise ValueError("toggle value must be allow or deny")
    return normalized


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
