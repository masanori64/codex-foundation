from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .foundation import PIPELINE_ROOT
from .simple_yaml import load_structured_file

BRIDGE_RELATIVE_PATH = Path(".codex-project") / "bridge.yml"
BRIDGE_SCHEMA_PATH = PIPELINE_ROOT / "schema" / "project-bridge.schema.json"


@dataclass(frozen=True)
class ProjectBridge:
    path: Path
    data: dict[str, Any]

    @property
    def project_id(self) -> str:
        return str(self.data["project_id"])

    @property
    def dashboard_dir(self) -> Path:
        return Path(str(self.data["outputs"]["dashboard_dir"]))

    @property
    def mermaid_dir(self) -> Path:
        return Path(str(self.data["outputs"]["mermaid_dir"]))

    @property
    def generated_dir(self) -> Path:
        return Path(str(self.data["outputs"]["generated_dir"]))


def load_project_bridge(project: Path) -> ProjectBridge:
    path = project / BRIDGE_RELATIVE_PATH
    if not path.exists():
        raise FileNotFoundError(f"project bridge missing: {path}")
    data = load_structured_file(path)
    errors = validate_project_bridge(data, path=path)
    if errors:
        raise ValueError("; ".join(errors))
    return ProjectBridge(path=path, data=data)


def validate_project_bridge(data: dict[str, Any], *, path: Path | None = None) -> list[str]:
    label = str(path or "bridge")
    errors: list[str] = []
    schema = load_structured_file(BRIDGE_SCHEMA_PATH)
    required = set(schema["required"])
    missing = sorted(required - set(data))
    if missing:
        return [f"{label}: missing {', '.join(missing)}"]
    if data["schema_version"] != 1:
        errors.append(f"{label}: schema_version must be 1")
    github = data.get("github")
    outputs = data.get("outputs")
    capabilities = data.get("capabilities", {})
    if not isinstance(github, dict):
        errors.append(f"{label}.github: must be an object")
        github = {}
    if not isinstance(outputs, dict):
        errors.append(f"{label}.outputs: must be an object")
        outputs = {}
    for key in schema["github_required"]:
        if key not in github:
            errors.append(f"{label}.github: missing {key}")
    if github.get("api_enabled") not in (False, "public_read"):
        errors.append(f"{label}: GitHub API must be false or public_read")
    for key in schema["outputs_required"]:
        if key not in outputs:
            errors.append(f"{label}.outputs: missing {key}")
    if capabilities and not isinstance(capabilities, dict):
        errors.append(f"{label}.capabilities: must be an object")
    return errors
