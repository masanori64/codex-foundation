from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

FOUNDATION_ROOT = Path(__file__).resolve().parent
DEFAULT_REGISTRY = FOUNDATION_ROOT / "offline_canary_registry.json"

STATUSES = {
    "local_fixture_passed",
    "blocked_reference_only",
    "provider_gated_deferred",
    "deferred_needs_source_review",
}
DISALLOWED_ACTIONS = {
    "install",
    "network",
    "provider_call",
    "hook",
    "mcp",
    "plugin_enable",
    "connector_enable",
    "auto_write",
}


def validate_offline_canary_registry(path: Path = DEFAULT_REGISTRY) -> list[str]:
    if not path.exists():
        return [f"offline canary registry missing: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON: {exc}"]
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    policy = data.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    else:
        for key in DISALLOWED_ACTIONS:
            if policy.get(key) is not False:
                errors.append(f"policy.{key} must be false")
        if policy.get("not_evidence") is not True:
            errors.append("policy.not_evidence must be true")
    canaries = data.get("canaries")
    if not isinstance(canaries, list) or not canaries:
        errors.append("canaries must be a non-empty list")
        return errors
    seen: set[str] = set()
    for index, canary in enumerate(canaries, start=1):
        if not isinstance(canary, dict):
            errors.append(f"canaries[{index}] must be an object")
            continue
        _validate_canary(canary, index, seen, errors)
    return errors


def _validate_canary(
    canary: dict[str, Any],
    index: int,
    seen: set[str],
    errors: list[str],
) -> None:
    canary_id = str(canary.get("canary_id", "")).strip()
    if not canary_id:
        errors.append(f"canaries[{index}].canary_id is required")
        canary_id = f"<canary-{index}>"
    if canary_id in seen:
        errors.append(f"{canary_id}: duplicate canary_id")
    seen.add(canary_id)
    for key in ("source", "owner_plane", "decision"):
        if not str(canary.get(key, "")).strip():
            errors.append(f"{canary_id}: {key} is required")
    status = str(canary.get("status", ""))
    if status not in STATUSES:
        errors.append(f"{canary_id}: invalid status {status!r}")
    actions = canary.get("actions")
    if not isinstance(actions, dict):
        errors.append(f"{canary_id}: actions must be an object")
    else:
        for key in DISALLOWED_ACTIONS:
            if actions.get(key) is not False:
                errors.append(f"{canary_id}: actions.{key} must be false")
    if canary.get("not_evidence") is not True:
        errors.append(f"{canary_id}: not_evidence must be true")
    fixture_refs = canary.get("fixture_refs", [])
    if not isinstance(fixture_refs, list):
        errors.append(f"{canary_id}: fixture_refs must be a list")
        fixture_refs = []
    if status == "local_fixture_passed" and not fixture_refs:
        errors.append(f"{canary_id}: local_fixture_passed requires fixture_refs")
    if status != "local_fixture_passed" and not canary.get("blockers"):
        errors.append(f"{canary_id}: non-passing canary requires blockers")
    for fixture in fixture_refs:
        _validate_fixture_ref(canary_id, fixture, errors)
    if canary_id == "research_x_fake_ocr_fixture":
        for fixture in fixture_refs:
            if not isinstance(fixture, dict):
                continue
            raw_path = str(fixture.get("path", "")).strip()
            if "ocr_fixture_manifest.json" not in raw_path:
                errors.append(
                    f"{canary_id}: foundation must reference the research_x OCR manifest, "
                    "not implementation/test file hashes"
                )


def _validate_fixture_ref(
    canary_id: str,
    fixture: object,
    errors: list[str],
) -> None:
    if not isinstance(fixture, dict):
        errors.append(f"{canary_id}: fixture_ref must be an object")
        return
    raw_path = str(fixture.get("path", "")).strip()
    if not raw_path:
        errors.append(f"{canary_id}: fixture_ref.path is required")
        return
    path = Path(raw_path)
    if not path.exists():
        errors.append(f"{canary_id}: fixture_ref missing: {raw_path}")
        return
    expected_hash = str(fixture.get("sha256", "")).strip().lower()
    if expected_hash:
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            errors.append(f"{canary_id}: fixture_ref hash mismatch: {raw_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Codex foundation offline canaries.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args(argv)

    errors = validate_offline_canary_registry(args.registry)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"offline canary registry ok: {args.registry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
