from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import Any

FOUNDATION_ROOT = Path(__file__).resolve().parent
DEFAULT_AUDIT = FOUNDATION_ROOT / "skill_quality_audit.toml"
DEFAULT_PROJECT = Path("C:/Users/maasa/research_x")
BAD_AGENT_SKILL_ARXIV_LOCATOR_ID = "2605.13221"
BAD_AGENT_SKILL_ARXIV_LOCATOR_FORMS = (
    "https://arxiv.org/abs/2605.13221",
    "https://arxiv.org/html/2605.13221",
    "arxiv:2605.13221",
    "2605.13221",
)
SKILL_RISK_TERMS = (
    "api key",
    "browser",
    "connector",
    "curl",
    "hook",
    "mcp",
    "npm install",
    "pip install",
    "plugin",
    "provider",
)


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def validate_skill_audit(
    *,
    project_root: Path = DEFAULT_PROJECT,
    audit_path: Path = DEFAULT_AUDIT,
    foundation_root: Path = FOUNDATION_ROOT,
) -> list[str]:
    errors: list[str] = []
    if not audit_path.exists():
        return [f"audit missing: {audit_path}"]
    try:
        audit = load_toml(audit_path)
    except tomllib.TOMLDecodeError as exc:
        return [f"audit TOML parse failed: {exc}"]

    if audit.get("audit_version") != 2:
        errors.append("audit_version must be 2")
    if audit.get("owner") != "maasa/.codex":
        errors.append("owner must be maasa/.codex")

    _validate_policy(audit.get("policy"), errors)
    canonical_sources = _validate_canonical_sources(
        audit,
        project_root,
        foundation_root,
        errors,
    )
    manifest_names = _manifest_names(
        canonical_sources.get("repo_skill_manifest", project_root / ".codex/skill_manifest.lock"),
        errors,
    )

    _validate_project_does_not_own_audit(project_root, errors)
    _validate_repo_skill_tree(project_root, manifest_names, errors)
    _validate_repo_skill_groups(audit, manifest_names, errors)
    _validate_codex_watchlist(audit, canonical_sources, errors)
    _validate_retired_project_skills(audit, project_root, errors)
    _validate_not_second_registry(audit, errors)
    _validate_canonical_boundary_text(canonical_sources, errors)
    _validate_foundation_policy(canonical_sources, errors)
    _validate_foundation_source_provenance(foundation_root, canonical_sources, errors)
    _validate_active_foundation_skills(audit, canonical_sources, errors)
    _validate_foundation_registry_source_locks(canonical_sources, errors)
    return errors


def _validate_policy(policy: object, errors: list[str]) -> None:
    if not isinstance(policy, dict):
        errors.append("[policy] table is required")
        return
    expected_false = {
        "auto_rewrite_allowed",
        "provider_or_external_action_allowed",
    }
    for key in expected_false:
        if policy.get(key) is not False:
            errors.append(f"policy.{key} must be false")
    expected_true = {
        "skills_are_audit_targets_not_instructions",
        "audit_is_not_registry",
        "repo_skills_must_be_manifested",
        "codex_foundation_owns_cross_skill_audit",
        "retired_project_skills_must_stay_out_of_research_x_agents",
    }
    for key in expected_true:
        if policy.get(key) is not True:
            errors.append(f"policy.{key} must be true")


def _validate_canonical_sources(
    audit: dict[str, Any],
    project_root: Path,
    foundation_root: Path,
    errors: list[str],
) -> dict[str, Path]:
    raw_sources = audit.get("canonical_sources")
    if not isinstance(raw_sources, dict):
        errors.append("[canonical_sources] table is required")
        return {}
    required = {
        "target_project_default",
        "repo_skill_manifest",
        "research_x_adoption_registry",
        "research_x_vendor_sources",
        "codex_personal_skill_root",
        "codex_foundation_registry",
        "codex_foundation_vendor_sources",
        "retired_project_skill_archive",
    }
    missing = sorted(required - set(raw_sources))
    if missing:
        errors.append("canonical_sources missing: " + ", ".join(missing))

    resolved: dict[str, Path] = {}
    project_relative = {
        "repo_skill_manifest",
        "research_x_adoption_registry",
        "research_x_vendor_sources",
    }
    for key, value in raw_sources.items():
        value_str = str(value)
        if key in project_relative:
            path = _resolve_path(value_str, project_root)
        else:
            path = _resolve_path(value_str, foundation_root)
        resolved[str(key)] = path
        if not path.exists():
            errors.append(f"canonical_sources.{key} missing: {value_str}")
    return resolved


def _manifest_names(manifest_path: Path, errors: list[str]) -> set[str]:
    if not manifest_path.exists():
        errors.append(f"manifest missing: {manifest_path}")
        return set()
    manifest = load_toml(manifest_path)
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        errors.append("manifest entries must be a list")
        return set()
    return {
        str(entry["name"])
        for entry in entries
        if isinstance(entry, dict) and entry.get("entry_type") == "repo_skill"
    }


def _validate_project_does_not_own_audit(project_root: Path, errors: list[str]) -> None:
    forbidden = (
        project_root / "control" / "skill_quality_audit.toml",
        project_root / "scripts" / "validate_skill_quality_audit.py",
        project_root / "tests" / "skills" / "test_skill_quality_audit.py",
    )
    for path in forbidden:
        if path.exists():
            errors.append(f"project must not own Skill audit surface: {path}")


def _validate_repo_skill_tree(
    project_root: Path,
    manifest_names: set[str],
    errors: list[str],
) -> None:
    skill_root = project_root / ".agents" / "skills"
    if not skill_root.exists():
        errors.append(f"project skill root missing: {skill_root}")
        return
    discovered: set[str] = set()
    for child in sorted(path for path in skill_root.iterdir() if path.is_dir()):
        skill_path = child / "SKILL.md"
        if not skill_path.exists():
            errors.append(f"{child.name}: directory under .agents/skills has no SKILL.md")
            continue
        discovered.add(child.name)
        if child.name not in manifest_names:
            errors.append(f"{child.name}: SKILL.md exists but manifest has no repo_skill entry")
        text = skill_path.read_text(encoding="utf-8")
        if "## Manifest Obligations" in text:
            errors.append(
                f"{child.name}: manifest obligations belong in the manifest, not SKILL.md"
            )
    missing_from_tree = sorted(manifest_names - discovered)
    if missing_from_tree:
        errors.append(
            "manifest repo skills missing from .agents/skills: "
            + ", ".join(missing_from_tree)
        )


def _validate_repo_skill_groups(
    audit: dict[str, Any],
    manifest_names: set[str],
    errors: list[str],
) -> None:
    groups = audit.get("repo_skill_groups", [])
    if not isinstance(groups, list) or not groups:
        errors.append("at least one [[repo_skill_groups]] item is required")
        return

    grouped: set[str] = set()
    for group in groups:
        if not isinstance(group, dict):
            errors.append("repo_skill_groups item must be a table")
            continue
        name = str(group.get("name", ""))
        members = group.get("members", [])
        decision = str(group.get("decision", ""))
        preserve = str(group.get("preserve", ""))
        if not name:
            errors.append("repo_skill_groups item missing name")
        if not isinstance(members, list) or len(members) < 2:
            errors.append(f"{name}: repo_skill_groups.members needs at least two entries")
            continue
        grouped.update(str(member) for member in members)
        if not decision:
            errors.append(f"{name}: repo_skill_groups.decision is required")
        if not preserve:
            errors.append(f"{name}: repo_skill_groups.preserve is required")
        unknown = sorted(str(member) for member in members if str(member) not in manifest_names)
        if unknown:
            errors.append(f"{name}: unknown repo Skill members: {', '.join(unknown)}")

    missing_from_groups = sorted(manifest_names - grouped)
    if missing_from_groups:
        errors.append(
            "manifest repo skills missing from repo_skill_groups: "
            + ", ".join(missing_from_groups)
        )


def _validate_codex_watchlist(
    audit: dict[str, Any],
    canonical_sources: dict[str, Path],
    errors: list[str],
) -> None:
    watchlist = audit.get("codex_foundation_watchlist", [])
    if not isinstance(watchlist, list) or not watchlist:
        errors.append("at least one [[codex_foundation_watchlist]] item is required")
        return
    skill_root = canonical_sources.get("codex_personal_skill_root")
    registry_text = _read_optional(canonical_sources.get("codex_foundation_registry"))

    for item in watchlist:
        if not isinstance(item, dict):
            errors.append("codex_foundation_watchlist item must be a table")
            continue
        name = str(item.get("name", ""))
        members = item.get("members", [])
        if not name:
            errors.append("codex_foundation_watchlist item missing name")
        if not isinstance(members, list) or not members:
            errors.append(f"{name or '<watchlist>'}: members needs at least one entry")
            continue
        if not str(item.get("decision", "")).strip():
            errors.append(f"{name}: decision is required")

        for member in (str(member) for member in members):
            skill_path = skill_root / member / "SKILL.md" if skill_root else Path()
            if not skill_path.exists():
                errors.append(f"{member}: Codex personal Skill path missing")
                continue
            declared_name = _frontmatter_name(skill_path)
            if declared_name != member:
                errors.append(
                    f"{member}: SKILL.md frontmatter mismatch "
                    f"(watchlist={member!r}, skill={declared_name!r})"
                )
            if registry_text and member not in registry_text:
                errors.append(f"{member}: not referenced by foundation registry")


def _validate_retired_project_skills(
    audit: dict[str, Any],
    project_root: Path,
    errors: list[str],
) -> None:
    retired = audit.get("retired_project_skills", [])
    if not isinstance(retired, list) or not retired:
        errors.append("at least one [[retired_project_skills]] item is required")
        return
    active_skill_root = project_root / ".agents" / "skills"
    for item in retired:
        if not isinstance(item, dict):
            errors.append("retired_project_skills item must be a table")
            continue
        name = str(item.get("name", ""))
        path_value = str(item.get("path", ""))
        decision = str(item.get("decision", ""))
        if not name:
            errors.append("retired_project_skills item missing name")
        is_deleted_record = "deleted" in decision
        if "retired" not in decision and not is_deleted_record:
            errors.append(f"{name}: retired decision must mention retired or deleted")
        path = Path(path_value)
        if not is_deleted_record and not path.exists():
            errors.append(f"{name}: retired Skill archive missing: {path_value}")
        if (active_skill_root / name / "SKILL.md").exists():
            errors.append(f"{name}: retired Skill must not reenter active .agents/skills")


def _validate_retired_foundation_skills(
    audit: dict[str, Any],
    skill_root: Path,
    registry_candidates: list[dict[str, Any]],
    errors: list[str],
) -> None:
    retired = audit.get("retired_foundation_skills", [])
    if not isinstance(retired, list):
        errors.append("retired_foundation_skills must be a list when present")
        return
    for item in retired:
        if not isinstance(item, dict):
            errors.append("retired_foundation_skills item must be a table")
            continue
        name = str(item.get("name", ""))
        if not name:
            errors.append("retired_foundation_skills item missing name")
            continue
        if (skill_root / name / "SKILL.md").exists():
            errors.append(f"{name}: retired foundation Skill must not reenter active .codex/skills")
        registry_item = _candidate_for_surface(registry_candidates, name)
        if registry_item and registry_item.get("enabled") is True:
            errors.append(f"{name}: retired foundation Skill must not be enabled in registry")


def _validate_not_second_registry(audit: dict[str, Any], errors: list[str]) -> None:
    forbidden_top_level = {"entries", "required_fields", "quality_profiles", "overlap_groups"}
    present = sorted(forbidden_top_level & set(audit))
    if present:
        errors.append("audit must not recreate a full registry: " + ", ".join(present))


def _validate_canonical_boundary_text(
    canonical_sources: dict[str, Path],
    errors: list[str],
) -> None:
    vendor = canonical_sources.get("research_x_vendor_sources")
    if vendor and vendor.exists():
        text = vendor.read_text(encoding="utf-8")
        for phrase in (
            "not permission to install, clone, enable, or call",
            "Codex foundation candidates belong to `maasa/.codex`",
        ):
            if phrase not in text:
                errors.append(f"research_x_vendor_sources missing boundary phrase: {phrase}")


def _validate_foundation_policy(
    canonical_sources: dict[str, Path],
    errors: list[str],
) -> None:
    registry = canonical_sources.get("codex_foundation_registry")
    if registry and registry.exists():
        data = load_toml(registry)
        policy = data.get("policy", {})
        if not isinstance(policy, dict):
            errors.append("foundation registry [policy] table is required")
        else:
            if policy.get("auto_apply_allowed") is not False:
                errors.append("foundation registry auto_apply_allowed must be false")
            if policy.get("manual_gate_for_install_hook_mcp_plugin_connector") is not True:
                errors.append(
                    "foundation registry manual install/hook/MCP/plugin/connector gate "
                    "must be true"
                )

    vendor = canonical_sources.get("codex_foundation_vendor_sources")
    if vendor and vendor.exists():
        text = vendor.read_text(encoding="utf-8")
        for phrase in (
            "Provider-backed or cloud memory candidates require explicit",
            "Install, hook, MCP, plugin, connector",
        ):
            if phrase not in text:
                errors.append(f"codex foundation vendor lock missing boundary phrase: {phrase}")


def _validate_foundation_source_provenance(
    foundation_root: Path,
    canonical_sources: dict[str, Path],
    errors: list[str],
) -> None:
    inventory = foundation_root / "source-origin-inventory.md"
    inventory_text = _read_optional(inventory)
    required = (
        "`quarantined_bad_locator`: current arXiv content is unrelated "
        "UAV logistics scheduling"
    )
    if not inventory_text:
        errors.append(f"source-origin inventory missing: {inventory}")
    else:
        if BAD_AGENT_SKILL_ARXIV_LOCATOR_ID in inventory_text and required not in inventory_text:
            errors.append(
                "arXiv 2605.13221 must stay quarantined as a bad Agent "
                "Skills/security locator"
            )
        if "| codex-memory | https://github.com/tszaks/codex-memory |" in inventory_text:
            errors.append(
                "source-origin inventory must not describe old codex-memory as "
                "the canonical memory candidate; use Pallium with codex-memory as alias"
            )

    reviewed_paths = {
        "codex_foundation_registry": canonical_sources.get("codex_foundation_registry"),
        "codex_foundation_vendor_sources": canonical_sources.get(
            "codex_foundation_vendor_sources"
        ),
        "source_origin_inventory": inventory,
    }
    for label, path in reviewed_paths.items():
        text = _read_optional(path)
        if not text:
            continue
        allowed_quarantine = label == "source_origin_inventory" and (
            "quarantined_bad_locator" in text and required in text
        )
        if allowed_quarantine:
            continue
        for locator in BAD_AGENT_SKILL_ARXIV_LOCATOR_FORMS:
            if locator.casefold() in text.casefold():
                errors.append(
                    f"{label}: bad Agent Skills/security locator must not be active: {locator}"
                )
                break

    registry_path = canonical_sources.get("codex_foundation_registry")
    if registry_path and registry_path.exists():
        registry = load_toml(registry_path)
        candidates = registry.get("candidates", [])
        if isinstance(candidates, list):
            old_candidates = [
                item
                for item in candidates
                if isinstance(item, dict)
                and item.get("name") == "codex-memory"
                and item.get("source") == "https://github.com/tszaks/codex-memory"
            ]
            if old_candidates:
                errors.append(
                    "foundation registry must track Pallium as canonical and "
                    "codex-memory only as a legacy alias"
                )
            pallium = [
                item
                for item in candidates
                if isinstance(item, dict) and item.get("name") == "pallium"
            ]
            if not pallium:
                errors.append("foundation registry missing canonical pallium candidate")
            else:
                _validate_pallium_metadata(pallium[0], errors)

    vendor_path = canonical_sources.get("codex_foundation_vendor_sources")
    vendor_text = _read_optional(vendor_path)
    if vendor_text:
        if "| `codex-memory` | https://github.com/tszaks/codex-memory |" in vendor_text:
            errors.append(
                "foundation vendor lock must not keep old codex-memory as the canonical row"
            )
        if "| `pallium` | https://github.com/tszaks/pallium |" not in vendor_text:
            errors.append("foundation vendor lock missing canonical pallium row")


def _validate_active_foundation_skills(
    audit: dict[str, Any],
    canonical_sources: dict[str, Path],
    errors: list[str],
) -> None:
    skill_root = canonical_sources.get("codex_personal_skill_root")
    registry_path = canonical_sources.get("codex_foundation_registry")
    if not skill_root or not skill_root.exists() or not registry_path or not registry_path.exists():
        return

    registry = load_toml(registry_path)
    candidates = _registry_candidates(registry)
    _validate_retired_foundation_skills(audit, skill_root, candidates, errors)

    for skill_path in sorted(skill_root.glob("*/SKILL.md")):
        skill_name = skill_path.parent.name
        if skill_name == ".system":
            continue
        candidate = _candidate_for_surface(candidates, skill_name)
        if candidate is None:
            errors.append(f"{skill_name}: active foundation Skill missing registry candidate")
            continue
        if candidate.get("enabled") is not True:
            errors.append(f"{skill_name}: active foundation Skill candidate must be enabled")
        if candidate.get("adoption_shape") != "adopt":
            errors.append(f"{skill_name}: active foundation Skill adoption_shape must be adopt")
        source_state = str(candidate.get("source_state", ""))
        if "installed" not in source_state and "local" not in source_state:
            errors.append(
                f"{skill_name}: active foundation Skill source_state must be installed/local"
            )
        _validate_skill_semantics(skill_name, skill_path, candidate, errors)


def _validate_foundation_registry_source_locks(
    canonical_sources: dict[str, Path],
    errors: list[str],
) -> None:
    registry_path = canonical_sources.get("codex_foundation_registry")
    vendor_path = canonical_sources.get("codex_foundation_vendor_sources")
    if not registry_path or not registry_path.exists():
        return
    registry = load_toml(registry_path)
    candidates = _registry_candidates(registry)
    vendor_text = _read_optional(vendor_path)

    for candidate in candidates:
        name = str(candidate.get("name", ""))
        source = str(candidate.get("source", ""))
        source_state = str(candidate.get("source_state", ""))
        active_surface = str(candidate.get("active_surface", ""))
        enabled = candidate.get("enabled") is True
        if _looks_like_external_source(source):
            if vendor_text and name not in vendor_text and source not in vendor_text:
                errors.append(f"{name}: external source candidate missing from vendor lock")
            if enabled and "installed" not in source_state:
                errors.append(
                    f"{name}: external source candidate cannot be enabled without "
                    "installed source_state"
                )
            if enabled and active_surface == "staging":
                errors.append(f"{name}: enabled external candidate cannot use staging surface")
        if "source_locked" in source_state and enabled and active_surface == "staging":
                errors.append(f"{name}: source-locked staging candidate must stay disabled")


def _validate_pallium_metadata(candidate: dict[str, Any], errors: list[str]) -> None:
    expected = {
        "surface_alias": "codex-memory",
        "canonical_url": "https://github.com/tszaks/pallium",
        "legacy_url": "https://github.com/tszaks/codex-memory",
        "source_kind": "repo_intelligence",
        "review_status": "blocked_reference_only",
        "license": "unverified",
        "retrieved_at": "2026-06-26",
    }
    for key, value in expected.items():
        if candidate.get(key) != value:
            errors.append(f"pallium candidate metadata {key} must be {value!r}")
    if candidate.get("redirect_chain") != [
        "https://github.com/tszaks/codex-memory",
        "https://github.com/tszaks/pallium",
    ]:
        errors.append("pallium candidate redirect_chain must preserve old and canonical URLs")


def _validate_skill_semantics(
    skill_name: str,
    skill_path: Path,
    candidate: dict[str, Any],
    errors: list[str],
) -> None:
    text = skill_path.read_text(encoding="utf-8")
    frontmatter = _frontmatter_fields(skill_path)
    description = frontmatter.get("description", "")
    if len(description.split()) < 6:
        errors.append(f"{skill_name}: description must name a concrete trigger and behavior")
    if "## Use When" not in text:
        errors.append(f"{skill_name}: SKILL.md must include ## Use When")
    if "## Do Not Use" not in text:
        errors.append(f"{skill_name}: SKILL.md must include ## Do Not Use When")
    normalized = text.casefold()
    risk_terms = sorted(term for term in SKILL_RISK_TERMS if term in normalized)
    if risk_terms and not _skill_text_has_gate(normalized):
        errors.append(
            f"{skill_name}: risky terms need explicit approval/gating language: "
            + ", ".join(risk_terms)
        )
    source = str(candidate.get("source", ""))
    if _looks_like_external_source(source) and "source_locked" not in str(
        candidate.get("source_state", "")
    ):
        errors.append(f"{skill_name}: externally sourced active Skill must be source-locked")


def _skill_text_has_gate(normalized_text: str) -> bool:
    return any(
        phrase in normalized_text
        for phrase in (
            "approval",
            "approved",
            "explicit",
            "explicitly",
            "forbid",
            "forbidden",
            "gate",
            "gated",
            "never",
        )
    )


def _registry_candidates(registry: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = registry.get("candidates", [])
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def _candidate_for_surface(
    candidates: list[dict[str, Any]],
    surface_name: str,
) -> dict[str, Any] | None:
    for candidate in candidates:
        names = {
            str(candidate.get("name", "")),
            str(candidate.get("surface_alias", "")),
            str(candidate.get("source_alias", "")),
        }
        if surface_name in names:
            return candidate
    return None


def _looks_like_external_source(source: str) -> bool:
    normalized = source.casefold()
    return normalized.startswith(("http://", "https://", "git@"))


def _read_optional(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _resolve_path(value: str, base: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return base / path


def _frontmatter_name(path: Path) -> str | None:
    return _frontmatter_fields(path).get("name")


def _frontmatter_fields(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fields: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate foundation-owned Skill boundary audit.")
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args(argv)

    errors = validate_skill_audit(project_root=args.project, audit_path=args.audit)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"foundation Skill audit ok: {args.project}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
