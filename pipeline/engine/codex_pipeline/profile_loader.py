from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .foundation import PIPELINE_ROOT
from .simple_yaml import load_structured_file

PROFILE_RELATIVE_PATH = Path(".codex-project") / "profile.yml"
PROFILE_SCHEMA_PATH = PIPELINE_ROOT / "schema" / "project-profile.schema.json"


@dataclass(frozen=True)
class ProjectProfile:
    path: Path
    data: dict[str, Any]

    @property
    def project_id(self) -> str:
        return str(self.data["project"]["id"])

    @property
    def project_name(self) -> str:
        return str(self.data["project"].get("name", self.project_id))

    @property
    def project_root(self) -> Path:
        return Path(str(self.data["project"]["root"]))

    @property
    def output_root(self) -> Path:
        return self.project_root / str(self.data["control_artifacts"]["output_root"])

    @property
    def generated_root(self) -> Path:
        return self.project_root / str(self.data["control_artifacts"]["generated_root"])


def load_project_profile(project: Path) -> ProjectProfile:
    path = project / PROFILE_RELATIVE_PATH
    if not path.exists():
        raise FileNotFoundError(f"project profile missing: {path}")
    data = load_structured_file(path)
    errors = validate_project_profile(data, path=path)
    if errors:
        raise ValueError("; ".join(errors))
    return ProjectProfile(path=path, data=data)


def validate_project_profile(data: dict[str, Any], *, path: Path | None = None) -> list[str]:
    label = str(path or "profile")
    errors: list[str] = []
    schema = load_structured_file(PROFILE_SCHEMA_PATH)
    required = set(schema["required"])
    errors.extend(_missing(label, data, required))
    if errors:
        return errors
    if data["schema_version"] != 1:
        errors.append(f"{label}: schema_version must be 1")
    project = _dict(data, "project", errors, label)
    constraints = _dict(data, "constraints", errors, label)
    artifacts = _dict(data, "control_artifacts", errors, label)
    _dict(data, "commands", errors, label)
    subagents = _dict(data, "subagents", errors, label)
    capabilities = data.get("capabilities", {})
    errors.extend(_missing(f"{label}.project", project, {"id", "name", "root", "domain"}))
    errors.extend(
        _missing(
            f"{label}.constraints",
            constraints,
            {
                "use_uv",
                "no_quota_provider_freeze",
                "evidence_boundary",
                "forbid_control_artifacts_as_evidence",
            },
        )
    )
    errors.extend(
        _missing(
            f"{label}.control_artifacts",
            artifacts,
            set(schema["control_artifacts_required"]),
        )
    )
    if constraints.get("no_quota_provider_freeze") is not True:
        errors.append(f"{label}: no_quota_provider_freeze must be true for Phase 0/1")
    if constraints.get("forbid_control_artifacts_as_evidence") is not True:
        errors.append(f"{label}: forbid_control_artifacts_as_evidence must be true")
    if artifacts.get("not_evidence") is not True:
        errors.append(f"{label}: control_artifacts.not_evidence must be true")
    if artifacts.get("not_citation") is not True:
        errors.append(f"{label}: control_artifacts.not_citation must be true")
    if artifacts.get("not_research_evidence") is not True:
        errors.append(f"{label}: control_artifacts.not_research_evidence must be true")
    if artifacts.get("not_answer_support") is not True:
        errors.append(f"{label}: control_artifacts.not_answer_support must be true")
    if not isinstance(subagents.get("allowed_roles", []), list):
        errors.append(f"{label}: subagents.allowed_roles must be a list")
    if capabilities and not isinstance(capabilities, dict):
        errors.append(f"{label}: capabilities must be an object")
    return errors


def _missing(label: str, data: dict[str, Any], required: set[str]) -> list[str]:
    missing = sorted(required - set(data))
    return [f"{label}: missing {', '.join(missing)}"] if missing else []


def _dict(data: dict[str, Any], key: str, errors: list[str], label: str) -> dict[str, Any]:
    value = data.get(key)
    if isinstance(value, dict):
        return value
    errors.append(f"{label}.{key}: must be an object")
    return {}
