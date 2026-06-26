from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PIPELINE_ROOT = Path(__file__).resolve().parents[2]
FOUNDATION_ID = "codex-hotl-implementation-pipeline"
FOUNDATION_MANIFEST = PIPELINE_ROOT / "FOUNDATION_MANIFEST.json"
FOUNDATION_AUDIT_LOG = PIPELINE_ROOT / "audit" / "foundation-events.jsonl"
FOUNDATION_REGISTRY = PIPELINE_ROOT.parent / "codex-foundation-registry.toml"

_MANIFEST_DIRS = ("engine", "policies", "schema", "scripts", "templates", "tests")
_MANIFEST_TOP_LEVEL = ("CHANGELOG.control.md", "README.md", "VERSION")
_EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
_EXCLUDED_NAMES = {"__pycache__", ".pytest_cache", "FOUNDATION_MANIFEST.json"}


def foundation_version() -> str:
    version_path = PIPELINE_ROOT / "VERSION"
    if version_path.exists():
        return version_path.read_text(encoding="utf-8").strip() or "0.1.0-local"
    return "0.1.0-local"


def build_foundation_manifest(
    *,
    known_projects: list[str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    files = [_file_record(path) for path in _manifest_paths()]
    return {
        "schema_version": 1,
        "foundation_id": FOUNDATION_ID,
        "version": foundation_version(),
        "generated_at": generated_at or datetime.now(UTC).isoformat(),
        "root": str(PIPELINE_ROOT),
        "control_artifact": True,
        "not_project_evidence": True,
        "not_research_evidence": True,
        "not_citation": True,
        "not_answer_support": True,
        "registered_in": str(FOUNDATION_REGISTRY),
        "known_projects": sorted(known_projects or []),
        "files": files,
    }


def write_foundation_manifest(
    *,
    known_projects: list[str] | None = None,
    audit: bool = True,
) -> dict[str, Any]:
    manifest = build_foundation_manifest(known_projects=known_projects)
    FOUNDATION_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    summary = foundation_manifest_summary()
    if audit:
        append_foundation_event(
            "foundation_manifest_written",
            {"file_count": len(manifest["files"]), "manifest_sha256": summary["sha256"]},
        )
    return manifest


def foundation_manifest_summary() -> dict[str, Any]:
    if not FOUNDATION_MANIFEST.exists():
        return {
            "id": FOUNDATION_ID,
            "version": foundation_version(),
            "path": str(FOUNDATION_MANIFEST),
            "sha256": "",
            "exists": False,
        }
    manifest = json.loads(FOUNDATION_MANIFEST.read_text(encoding="utf-8"))
    return {
        "id": str(manifest.get("foundation_id", FOUNDATION_ID)),
        "version": str(manifest.get("version", foundation_version())),
        "path": str(FOUNDATION_MANIFEST),
        "sha256": _sha256(FOUNDATION_MANIFEST),
        "exists": True,
    }


def control_marker(*, artifact_kind: str | None = None) -> dict[str, Any]:
    marker: dict[str, Any] = {
        "control_artifact": True,
        "not_evidence": True,
        "not_project_evidence": True,
        "not_research_evidence": True,
        "not_citation": True,
        "not_answer_support": True,
        "generated_by": FOUNDATION_ID,
        "foundation_manifest": foundation_manifest_summary(),
    }
    if artifact_kind:
        marker["artifact_kind"] = artifact_kind
    return marker


def validate_foundation_manifest() -> list[str]:
    errors: list[str] = []
    if not FOUNDATION_MANIFEST.exists():
        return [f"foundation manifest missing: {FOUNDATION_MANIFEST}"]
    try:
        manifest = json.loads(FOUNDATION_MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"foundation manifest is not valid JSON: {exc}"]
    if manifest.get("foundation_id") != FOUNDATION_ID:
        errors.append("foundation manifest id does not match registry candidate")
    if manifest.get("control_artifact") is not True:
        errors.append("foundation manifest must be control_artifact")
    if manifest.get("not_project_evidence") is not True:
        errors.append("foundation manifest must be not_project_evidence")
    if manifest.get("not_research_evidence") is not True:
        errors.append("foundation manifest must be not_research_evidence")
    if manifest.get("not_citation") is not True:
        errors.append("foundation manifest must be not_citation")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        errors.append("foundation manifest must include file records")
    else:
        for index, record in enumerate(files):
            if not isinstance(record, dict):
                errors.append(f"foundation manifest file record {index} must be an object")
                continue
            rel = record.get("path")
            digest = record.get("sha256")
            size = record.get("bytes")
            if not isinstance(rel, str) or not rel:
                errors.append(f"foundation manifest file record {index} missing path")
                continue
            target = PIPELINE_ROOT / rel
            if not target.exists():
                errors.append(f"foundation manifest file missing on disk: {rel}")
                continue
            if digest != _sha256(target):
                errors.append(f"foundation manifest hash mismatch: {rel}")
            if size != target.stat().st_size:
                errors.append(f"foundation manifest byte size mismatch: {rel}")
    return errors


def append_foundation_event(event_type: str, details: dict[str, Any] | None = None) -> None:
    FOUNDATION_AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": 1,
        "event_type": event_type,
        "created_at": datetime.now(UTC).isoformat(),
        "foundation_id": FOUNDATION_ID,
        "control_artifact": True,
        "not_project_evidence": True,
        "details": details or {},
    }
    with FOUNDATION_AUDIT_LOG.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def mermaid_marker_comment() -> str:
    summary = foundation_manifest_summary()
    return "\n".join(
        [
            "%% control_artifact=true",
            "%% not_research_evidence=true",
            "%% not_citation=true",
            "%% not_answer_support=true",
            f"%% generated_by={FOUNDATION_ID}",
            f"%% foundation_manifest_sha256={summary['sha256']}",
            "",
        ]
    )


def _manifest_paths() -> list[Path]:
    paths: list[Path] = []
    for name in _MANIFEST_TOP_LEVEL:
        path = PIPELINE_ROOT / name
        if path.exists():
            paths.append(path)
    for dirname in _MANIFEST_DIRS:
        root = PIPELINE_ROOT / dirname
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if _include_manifest_path(path):
                paths.append(path)
    return sorted(set(paths), key=lambda path: path.relative_to(PIPELINE_ROOT).as_posix())


def _include_manifest_path(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix in _EXCLUDED_SUFFIXES:
        return False
    if any(part in _EXCLUDED_NAMES for part in path.parts):
        return False
    try:
        path.relative_to(PIPELINE_ROOT)
    except ValueError:
        return False
    return True


def _file_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(PIPELINE_ROOT).as_posix(),
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
