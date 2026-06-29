from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "FOUNDATION_REPO_MANIFEST.json"
MANIFEST_ROOT = "."
INCLUDE_DIRS = (
    ".github",
    "codex_improvement",
    "context_offloads",
    "pipeline",
    "project_plans",
    "prompt_contracts",
    "research_intake",
    "scripts",
    "tests",
)
INCLUDE_FILES = (
    ".gitattributes",
    ".gitignore",
    "README.md",
    "codex-foundation-registry.toml",
    "offline_canaries.py",
    "offline_canary_registry.json",
    "pyproject.toml",
    "skill_audit.py",
    "skill_factory.py",
    "skill_quality_audit.toml",
    "source-origin-inventory.md",
    "uv.lock",
    "vendor_sources.lock.md",
)
EXCLUDED_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "FOUNDATION_REPO_MANIFEST.json",
}
EXCLUDED_PARTS = {
    "audit",
    "attachments",
    "downloads",
    "project_reviews",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip", ".7z", ".tgz"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.check and args.write:
        parser.error("choose --check or --write, not both")
    if args.check:
        errors = validate_manifest()
        if errors:
            print("\n".join(errors))
            return 1
        print("foundation repo manifest ok")
        return 0

    manifest = build_manifest()
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {MANIFEST_PATH}")
    return 0


def build_manifest(*, generated_at: str | None = None) -> dict[str, Any]:
    files = [_file_record(path) for path in _manifest_paths()]
    return {
        "schema_version": 1,
        "foundation_id": "codex-foundation-repo",
        "artifact_kind": "foundation_repo_manifest",
        "generated_at": generated_at or datetime.now(UTC).isoformat(),
        "root": MANIFEST_ROOT,
        "control_artifact": True,
        "not_project_evidence": True,
        "not_research_evidence": True,
        "not_citation": True,
        "not_answer_support": True,
        "ci_workflow": ".github/workflows/foundation-ci.yml",
        "cd_mode": "github_actions_artifact",
        "paid_usage_detected": False,
        "provider_api_calls": False,
        "secrets_used": False,
        "files": files,
    }


def validate_manifest() -> list[str]:
    if not MANIFEST_PATH.exists():
        return [f"foundation repo manifest missing: {MANIFEST_PATH}"]
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"foundation repo manifest is not valid JSON: {exc}"]

    errors: list[str] = []
    if manifest.get("foundation_id") != "codex-foundation-repo":
        errors.append("foundation repo manifest id mismatch")
    if manifest.get("root") != MANIFEST_ROOT:
        errors.append("foundation repo manifest root must be repository-relative '.'")
    if manifest.get("control_artifact") is not True:
        errors.append("foundation repo manifest must be control_artifact")
    if manifest.get("cd_mode") != "github_actions_artifact":
        errors.append("foundation repo manifest cd_mode must be github_actions_artifact")
    for key in ("paid_usage_detected", "provider_api_calls", "secrets_used"):
        if manifest.get(key) is not False:
            errors.append(f"foundation repo manifest {key} must be false")

    expected = {path.relative_to(ROOT).as_posix(): path for path in _manifest_paths()}
    actual_records = manifest.get("files")
    if not isinstance(actual_records, list) or not actual_records:
        return errors + ["foundation repo manifest must include file records"]
    actual: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(actual_records):
        if not isinstance(record, dict):
            errors.append(f"file record {index} must be an object")
            continue
        rel = record.get("path")
        if not isinstance(rel, str):
            errors.append(f"file record {index} missing path")
            continue
        actual[rel] = record

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing:
        errors.append("foundation repo manifest missing files: " + ", ".join(missing[:20]))
    if extra:
        errors.append("foundation repo manifest extra files: " + ", ".join(extra[:20]))

    for rel, path in expected.items():
        record = actual.get(rel)
        if record is None:
            continue
        if record.get("sha256") != _sha256(path):
            errors.append(f"foundation repo manifest hash mismatch: {rel}")
        if record.get("bytes") != path.stat().st_size:
            errors.append(f"foundation repo manifest byte size mismatch: {rel}")
    return errors


def _manifest_paths() -> list[Path]:
    paths: list[Path] = []
    for name in INCLUDE_FILES:
        path = ROOT / name
        if path.exists():
            paths.append(path)
    for dirname in INCLUDE_DIRS:
        root = ROOT / dirname
        if not root.exists():
            continue
        paths.extend(path for path in root.rglob("*") if _include_path(path))
    return sorted(set(paths), key=lambda path: path.relative_to(ROOT).as_posix())


def _include_path(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    return not any(part in EXCLUDED_NAMES or part in EXCLUDED_PARTS for part in path.parts)


def _file_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
