from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

FOUNDATION_ROOT = Path(__file__).resolve().parent
DEFAULT_CODEX_HOME = Path("C:/Users/maasa/.codex")
DEFAULT_CANDIDATE_ROOT = FOUNDATION_ROOT / "skill_factory" / "candidates"
DEFAULT_ACTIVE_ROOT = DEFAULT_CODEX_HOME / "skills"
DEFAULT_PROJECT_ROOT = Path("C:/Users/maasa/research_x")
DEFAULT_SKILL_AUDIT = FOUNDATION_ROOT / "skill_audit.py"
HOOK_MARKER = "codex-skill-factory-managed-pre-commit"

SECTION_ORDER = (
    "Purpose",
    "Use When",
    "Do Not Use When",
    "Inputs",
    "Outputs",
    "Workflow",
    "Safety Gates",
    "Verification",
    "Removal Path",
)
PROVIDER_WORDS = (
    "api",
    "quota",
    "provider",
    "openai",
    "gemini",
    "mistral",
    "voyage",
    "cohere",
    "serper",
    "brave",
    "firecrawl",
    "tavily",
    "exa",
    "perplexity",
)
OVERBROAD_TRIGGERS = (
    "always use",
    "every request",
    "all tasks",
    "必ず使う",
    "常に使う",
    "全部",
    "すべて",
)
TARGETS = ("auto", "codex", "project")
REJECTED_TARGET = "rejected"
CODEX_SCOPE_WORDS = (
    "codex",
    "foundation",
    "handoff",
    "memory",
    "session",
    "retrospective",
    "governance",
    "audit",
    "skill",
    "基盤",
    "全体",
    "横断",
    "記憶",
    "監査",
    "引き継ぎ",
)
PROJECT_SCOPE_WORDS = (
    "project",
    "repo",
    "repository",
    "domain",
    "test",
    "verify",
    "citation",
    "retrieval",
    "provider gate",
    "プロジェクト",
    "検証",
    "引用",
    "検索",
)
REJECT_WORDS = (
    "one-off",
    "one time",
    "今回だけ",
    "一回だけ",
    "メモ",
)
NON_SKILL_SURFACE_WORDS = (
    "mcp",
    "plugin",
    "connector",
    "browser",
    "script",
    "cli",
    "hook",
)


@dataclass(frozen=True)
class SkillSpec:
    name: str
    description: str
    purpose: str
    use_when: list[str]
    do_not_use_when: list[str]
    inputs: list[str]
    outputs: list[str]
    workflow: list[str]
    safety_gates: list[str]
    verification: list[str]
    removal_path: str
    owner: str = "maasa/.codex"
    resources: list[str] | None = None
    provider_or_quota: bool = False


@dataclass(frozen=True)
class PipelineResult:
    status: str
    skill_name: str
    candidate_path: str
    active_path: str | None
    errors: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class PlacementDecision:
    status: str
    target: str
    reason: str
    target_path: str | None
    errors: list[str]
    warnings: list[str]


def spec_from_brief(brief: str, *, name: str | None = None) -> SkillSpec:
    clean = " ".join(brief.strip().split())
    inferred_name = normalize_name(name or _infer_name(clean))
    purpose = _infer_purpose(clean)
    provider_or_quota = any(word in clean.lower() for word in PROVIDER_WORDS)
    return SkillSpec(
        name=inferred_name,
        description=(
            f"Use when Codex repeatedly needs to {purpose}. "
            "Do not use for one-off work or tasks covered by a more specific Skill."
        ),
        purpose=purpose,
        use_when=[
            f"The user asks for the recurring workflow: {clean}",
            "The same workflow has appeared often enough to justify always-visible Skill metadata.",
        ],
        do_not_use_when=[
            "The request is a one-off note, research result, or project fact.",
            "An existing Skill or plugin already owns the trigger more precisely.",
            "The task requires provider/API/quota use, install, connector, MCP, or hook changes.",
        ],
        inputs=[
            "User request",
            "Target files, project, or artifact paths",
            "Existing Skill and registry context when overlap is possible",
        ],
        outputs=[
            "A focused task result for the recurring workflow",
            "Verification notes",
            "A recommendation to retire or merge the Skill if overlap appears",
        ],
        workflow=[
            "Confirm the request matches this Skill's narrow recurring trigger.",
            "Inspect the relevant local files or artifacts before changing them.",
            "Apply the smallest workflow-specific procedure that completes the task.",
            "Run the local verification appropriate for the touched surface.",
            "Report outputs, skipped external actions, and any retirement or merge signal.",
        ],
        safety_gates=[
            "Do not call providers or network APIs.",
            "Do not install dependencies, enable connectors, configure MCP, or add hooks.",
            "Do not overwrite unrelated files or user changes.",
            "Stop if a more specific active Skill owns the request.",
        ],
        verification=[
            (
                "Run the local command or inspection that proves the requested "
                "artifact changed correctly."
            ),
            "Check that the Skill did not trigger for a broader neighboring workflow.",
            "Record missing verification honestly instead of treating intent as proof.",
        ],
        removal_path=(
            "Merge or retire this Skill if its trigger overlaps a stronger owner, "
            "stops recurring, or no longer changes Codex behavior."
        ),
        provider_or_quota=provider_or_quota,
    )


def classify_placement(
    brief: str,
    *,
    project_root: Path = DEFAULT_PROJECT_ROOT,
    target: str = "auto",
) -> PlacementDecision:
    if target not in TARGETS:
        return PlacementDecision(
            "rejected",
            REJECTED_TARGET,
            f"unknown target: {target}",
            None,
            [f"target must be one of: {', '.join(TARGETS)}"],
            [],
        )

    text = " ".join(brief.strip().split())
    lowered = text.lower()
    if not text:
        return PlacementDecision(
            "rejected",
            REJECTED_TARGET,
            "empty Skill brief",
            None,
            ["brief is required"],
            [],
        )
    if any(word in lowered for word in PROVIDER_WORDS):
        return PlacementDecision(
            "rejected",
            REJECTED_TARGET,
            "provider/API/quota work is not auto-created as a Skill",
            None,
            ["provider/API/quota work is blocked from automatic Skill creation"],
            [],
        )
    if any(word in lowered for word in REJECT_WORDS):
        return PlacementDecision(
            "rejected",
            REJECTED_TARGET,
            "one-off or note-like requests should not become always-visible Skills",
            None,
            ["request does not justify Skill maintenance cost"],
            [],
        )
    if any(word in lowered for word in NON_SKILL_SURFACE_WORDS) and target == "auto":
        return PlacementDecision(
            "rejected",
            REJECTED_TARGET,
            "the main surface appears to be script/plugin/MCP/hook rather than a Skill",
            None,
            ["use a script, plugin, MCP, hook, or project docs instead of a Skill"],
            [],
        )

    project_manifest = project_manifest_path(project_root)
    project_skill_root = project_skills_root(project_root)
    project_name = project_root.name.lower()
    has_project_words = (
        any(word in lowered for word in PROJECT_SCOPE_WORDS)
        or project_name in lowered
        or str(project_root).lower() in lowered
    )
    has_codex_words = any(word in lowered for word in CODEX_SCOPE_WORDS)

    if target == "codex" or (target == "auto" and has_codex_words and not has_project_words):
        return PlacementDecision(
            "ok",
            "codex",
            "Codex-wide operation belongs in the foundation Skill layer",
            str(DEFAULT_ACTIVE_ROOT),
            [],
            [],
        )
    if target == "project" or (target == "auto" and has_project_words):
        if not project_manifest.exists():
            return PlacementDecision(
                "rejected",
                REJECTED_TARGET,
                "project-local Skill management is not initialized",
                str(project_skill_root),
                [f"project Skill manifest missing: {project_manifest}"],
                [],
            )
        return PlacementDecision(
            "ok",
            "project",
            "Project-specific workflow belongs in the project-local Skill layer",
            str(project_skill_root),
            [],
            [],
        )

    return PlacementDecision(
        "ok",
        "codex",
        "No project-specific signal found; defaulting to Codex foundation Skill layer",
        str(DEFAULT_ACTIVE_ROOT),
        [],
        ["auto target defaulted to codex"],
    )


def load_spec(path: Path) -> SkillSpec:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return SkillSpec(
        name=normalize_name(str(raw.get("name", ""))),
        description=str(raw.get("description", "")).strip(),
        purpose=str(raw.get("purpose", "")).strip(),
        use_when=_string_list(raw.get("use_when")),
        do_not_use_when=_string_list(raw.get("do_not_use_when")),
        inputs=_string_list(raw.get("inputs")),
        outputs=_string_list(raw.get("outputs")),
        workflow=_string_list(raw.get("workflow")),
        safety_gates=_string_list(raw.get("safety_gates")),
        verification=_string_list(raw.get("verification")),
        removal_path=str(raw.get("removal_path", "")).strip(),
        owner=str(raw.get("owner", "maasa/.codex")).strip() or "maasa/.codex",
        resources=_string_list(raw.get("resources")),
        provider_or_quota=bool(raw.get("provider_or_quota", False)),
    )


def normalize_name(value: str) -> str:
    name = value.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-{2,}", "-", name).strip("-")
    return name[:64].strip("-")


def build_skill_markdown(spec: SkillSpec) -> str:
    sections = {
        "Purpose": spec.purpose,
        "Use When": _bullets(spec.use_when),
        "Do Not Use When": _bullets(spec.do_not_use_when),
        "Inputs": _bullets(spec.inputs),
        "Outputs": _bullets(spec.outputs),
        "Workflow": _numbered(spec.workflow),
        "Safety Gates": _bullets(spec.safety_gates),
        "Verification": _bullets(spec.verification),
        "Removal Path": spec.removal_path,
    }
    body = "\n\n".join(f"## {heading}\n\n{sections[heading]}" for heading in SECTION_ORDER)
    return (
        f"---\nname: {spec.name}\ndescription: {spec.description}\n---\n\n"
        f"# {title(spec.name)}\n\n{body}\n"
    )


def build_openai_yaml(spec: SkillSpec) -> str:
    display = title(spec.name)
    short = spec.description[:64].rstrip()
    prompt = f"Use ${spec.name} to {spec.purpose[:80].rstrip('.')}."
    return (
        "interface:\n"
        f'  display_name: "{_yaml_quote(display)}"\n'
        f'  short_description: "{_yaml_quote(short)}"\n'
        f'  default_prompt: "{_yaml_quote(prompt)}"\n'
        "policy:\n"
        "  allow_implicit_invocation: true\n"
    )


def validate_spec(
    spec: SkillSpec,
    *,
    active_root: Path = DEFAULT_ACTIVE_ROOT,
    candidate_root: Path = DEFAULT_CANDIDATE_ROOT,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not spec.name:
        errors.append("name is required")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", spec.name or ""):
        errors.append("name must be lowercase hyphen-case")
    if not spec.description:
        errors.append("description is required")
    if len(spec.description) > 1024:
        errors.append("description must be 1024 characters or less")
    if not spec.purpose:
        errors.append("purpose is required")
    required_lists = (
        "use_when",
        "do_not_use_when",
        "inputs",
        "outputs",
        "workflow",
        "safety_gates",
        "verification",
    )
    for field in required_lists:
        if not getattr(spec, field):
            errors.append(f"{field} must have at least one item")
    if not spec.removal_path:
        errors.append("removal_path is required")
    if spec.provider_or_quota:
        errors.append("provider_or_quota specs are blocked from automatic Skill creation")

    text = " ".join(
        [
            spec.description,
            spec.purpose,
            " ".join(spec.use_when),
            " ".join(spec.workflow),
            " ".join(spec.safety_gates),
        ]
    ).lower()
    if any(trigger in text for trigger in OVERBROAD_TRIGGERS):
        errors.append("trigger is over-broad; define narrower use_when and negative triggers")
    has_provider_gate = any(
        "gate" in item.lower()
        or "do not call" in item.lower()
        or "禁止" in item
        or "使わない" in item
        for item in spec.safety_gates
    )
    if any(word in text for word in PROVIDER_WORDS) and not has_provider_gate:
        errors.append("provider/API wording requires an explicit safety gate")

    active_skill = active_root / spec.name / "SKILL.md"
    if active_skill.exists():
        errors.append(f"active Skill already exists: {active_skill}")
    candidate_skill = candidate_root / spec.name / "SKILL.md"
    if candidate_skill.exists():
        warnings.append(f"candidate will replace previous candidate: {candidate_skill}")

    overlaps = find_trigger_overlaps(spec, active_root)
    if overlaps:
        joined = ", ".join(overlaps[:5])
        errors.append(f"possible trigger overlap with active Skill(s): {joined}")
    return errors, warnings


def find_trigger_overlaps(spec: SkillSpec, active_root: Path) -> list[str]:
    if not active_root.exists():
        return []
    wanted = _keywords(" ".join([spec.description, spec.purpose, *spec.use_when]))
    overlaps: list[str] = []
    for skill_file in sorted(active_root.glob("*/SKILL.md")):
        if skill_file.parent.name == spec.name:
            continue
        text = skill_file.read_text(encoding="utf-8", errors="ignore")
        existing = _keywords(text[:2500])
        shared = wanted & existing
        if len(shared) >= 5:
            overlaps.append(f"{skill_file.parent.name}({len(shared)})")
    return overlaps


def create_candidate(
    spec: SkillSpec,
    *,
    candidate_root: Path = DEFAULT_CANDIDATE_ROOT,
    active_root: Path = DEFAULT_ACTIVE_ROOT,
    force: bool = False,
    auto_promote: bool = False,
) -> PipelineResult:
    errors, warnings = validate_spec(spec, active_root=active_root, candidate_root=candidate_root)
    candidate_dir = candidate_root / spec.name
    if errors:
        return PipelineResult("rejected", spec.name, str(candidate_dir), None, errors, warnings)
    if candidate_dir.exists() and not force:
        return PipelineResult(
            "rejected",
            spec.name,
            str(candidate_dir),
            None,
            [f"candidate already exists; rerun with --force: {candidate_dir}"],
            warnings,
        )
    if candidate_dir.exists():
        shutil.rmtree(candidate_dir)
    (candidate_dir / "agents").mkdir(parents=True)
    (candidate_dir / "SKILL.md").write_text(build_skill_markdown(spec), encoding="utf-8")
    (candidate_dir / "agents" / "openai.yaml").write_text(build_openai_yaml(spec), encoding="utf-8")
    for resource in spec.resources or []:
        (candidate_dir / resource).mkdir()
    write_report(candidate_dir, spec, status="candidate")
    if auto_promote:
        return promote_candidate(spec.name, candidate_root=candidate_root, active_root=active_root)
    return PipelineResult("candidate", spec.name, str(candidate_dir), None, [], warnings)


def create_from_brief(
    brief: str,
    *,
    name: str | None = None,
    candidate_root: Path = DEFAULT_CANDIDATE_ROOT,
    active_root: Path = DEFAULT_ACTIVE_ROOT,
    force: bool = False,
    auto_promote: bool = False,
) -> PipelineResult:
    return create_candidate(
        spec_from_brief(brief, name=name),
        candidate_root=candidate_root,
        active_root=active_root,
        force=force,
        auto_promote=auto_promote,
    )


def create_routed_from_brief(
    brief: str,
    *,
    name: str | None = None,
    project_root: Path = DEFAULT_PROJECT_ROOT,
    target: str = "auto",
    candidate_root: Path = DEFAULT_CANDIDATE_ROOT,
    active_root: Path = DEFAULT_ACTIVE_ROOT,
    force: bool = False,
    auto_promote: bool = False,
) -> PipelineResult:
    spec = spec_from_brief(brief, name=name)
    return create_routed_spec(
        spec,
        classification_text=brief,
        project_root=project_root,
        target=target,
        candidate_root=candidate_root,
        active_root=active_root,
        force=force,
        auto_promote=auto_promote,
    )


def create_routed_spec(
    spec: SkillSpec,
    *,
    classification_text: str,
    project_root: Path = DEFAULT_PROJECT_ROOT,
    target: str = "auto",
    candidate_root: Path = DEFAULT_CANDIDATE_ROOT,
    active_root: Path = DEFAULT_ACTIVE_ROOT,
    force: bool = False,
    auto_promote: bool = False,
) -> PipelineResult:
    decision = classify_placement(
        classification_text,
        project_root=project_root,
        target=target,
    )
    if decision.errors:
        return PipelineResult(
            "rejected",
            spec.name,
            decision.target_path or "",
            None,
            decision.errors,
            decision.warnings,
        )
    if decision.target == "project":
        return create_project_skill(
            spec,
            project_root=project_root,
            candidate_root=project_candidate_root(candidate_root, project_root),
            force=force,
            auto_promote=auto_promote,
        )
    return create_candidate(
        spec,
        candidate_root=candidate_root,
        active_root=active_root,
        force=force,
        auto_promote=auto_promote,
    )


def create_project_skill(
    spec: SkillSpec,
    *,
    project_root: Path,
    candidate_root: Path,
    force: bool = False,
    auto_promote: bool = False,
) -> PipelineResult:
    manifest_path = project_manifest_path(project_root)
    if not manifest_path.exists():
        return PipelineResult(
            "rejected",
            spec.name,
            str(candidate_root / spec.name),
            None,
            [f"project Skill manifest missing: {manifest_path}"],
            [],
        )
    result = create_candidate(
        spec,
        candidate_root=candidate_root,
        active_root=project_skills_root(project_root),
        force=force,
        auto_promote=auto_promote,
    )
    if result.status == "promoted" and not result.errors:
        append_project_manifest_entry(manifest_path, spec, project_root=project_root)
    return result


def promote_candidate(
    skill_name: str,
    *,
    candidate_root: Path = DEFAULT_CANDIDATE_ROOT,
    active_root: Path = DEFAULT_ACTIVE_ROOT,
    force: bool = False,
) -> PipelineResult:
    name = normalize_name(skill_name)
    candidate_dir = candidate_root / name
    active_dir = active_root / name
    if not (candidate_dir / "SKILL.md").exists():
        return PipelineResult(
            "rejected",
            name,
            str(candidate_dir),
            str(active_dir),
            [f"candidate missing: {candidate_dir}"],
            [],
        )
    if active_dir.exists() and not force:
        return PipelineResult(
            "rejected",
            name,
            str(candidate_dir),
            str(active_dir),
            [f"active Skill already exists: {active_dir}"],
            [],
        )
    if active_dir.exists():
        shutil.rmtree(active_dir)
    active_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(candidate_dir, active_dir)
    write_report(
        candidate_dir,
        _spec_from_skill(candidate_dir / "SKILL.md"),
        status="promoted",
        active_dir=active_dir,
    )
    return PipelineResult("promoted", name, str(candidate_dir), str(active_dir), [], [])


def check_pipeline(
    *,
    candidate_root: Path = DEFAULT_CANDIDATE_ROOT,
    active_root: Path = DEFAULT_ACTIVE_ROOT,
) -> PipelineResult:
    errors: list[str] = []
    warnings: list[str] = []
    candidate_count = 0
    active_count = 0

    if candidate_root.exists():
        for candidate in sorted(path for path in candidate_root.iterdir() if path.is_dir()):
            candidate_count += 1
            skill_md = candidate / "SKILL.md"
            if not skill_md.exists():
                errors.append(f"candidate missing SKILL.md: {candidate}")
            else:
                errors.extend(_validate_skill_file_shape(skill_md, require_factory_sections=True))
            if not (candidate / "skill_factory_report.json").exists():
                errors.append(f"candidate missing skill_factory_report.json: {candidate}")
            active_match = active_root / candidate.name
            report_status = _report_status(candidate / "skill_factory_report.json")
            if active_match.exists() and report_status != "promoted":
                warnings.append(
                    "candidate already promoted or duplicated in active root: "
                    f"{candidate.name}"
                )

    if active_root.exists():
        for active in sorted(path for path in active_root.iterdir() if path.is_dir()):
            if (active / "SKILL.md").exists():
                active_count += 1
                errors.extend(
                    _validate_skill_file_shape(
                        active / "SKILL.md",
                        require_factory_sections=False,
                    )
                )

    status = "ok" if not errors else "rejected"
    result = PipelineResult(
        status,
        "skill-factory",
        str(candidate_root),
        str(active_root),
        errors,
        warnings,
    )
    summary = {
        "status": result.status,
        "candidate_count": candidate_count,
        "active_skill_count": active_count,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return result


def doctor_pipeline(
    *,
    project_root: Path = DEFAULT_PROJECT_ROOT,
    candidate_root: Path = DEFAULT_CANDIDATE_ROOT,
    active_root: Path = DEFAULT_ACTIVE_ROOT,
    skill_audit_path: Path = DEFAULT_SKILL_AUDIT,
) -> PipelineResult:
    errors: list[str] = []
    warnings: list[str] = []

    check_result = check_pipeline(candidate_root=candidate_root, active_root=active_root)
    errors.extend(check_result.errors)
    warnings.extend(check_result.warnings)

    audit_errors = run_foundation_skill_audit(
        project_root=project_root,
        skill_audit_path=skill_audit_path,
    )
    errors.extend(audit_errors)

    status = "ok" if not errors else "rejected"
    result = PipelineResult(
        status,
        "skill-factory-doctor",
        str(candidate_root),
        str(active_root),
        errors,
        warnings,
    )
    summary = {
        "status": result.status,
        "project_root": str(project_root),
        "candidate_root": str(candidate_root),
        "active_root": str(active_root),
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return result


def run_foundation_skill_audit(*, project_root: Path, skill_audit_path: Path) -> list[str]:
    if not skill_audit_path.exists():
        return [f"skill_audit.py missing: {skill_audit_path}"]
    spec = importlib.util.spec_from_file_location("foundation_skill_audit", skill_audit_path)
    if not spec or not spec.loader:
        return [f"cannot load skill audit module: {skill_audit_path}"]
    module = importlib.util.module_from_spec(spec)
    sys.modules["foundation_skill_audit"] = module
    spec.loader.exec_module(module)
    validate = getattr(module, "validate_skill_audit", None)
    if not validate:
        return [f"validate_skill_audit missing: {skill_audit_path}"]
    return list(validate(project_root=project_root))


def write_report(
    candidate_dir: Path,
    spec: SkillSpec,
    *,
    status: str,
    active_dir: Path | None = None,
) -> None:
    report = {
        "status": status,
        "skill_name": spec.name,
        "owner": spec.owner,
        "candidate_path": str(candidate_dir),
        "active_path": str(active_dir) if active_dir else None,
        "created_at": datetime.now(UTC).isoformat(),
        "provider_or_quota": spec.provider_or_quota,
        "registry_candidate": build_registry_candidate(
            spec,
            candidate_dir=candidate_dir,
            active_dir=active_dir,
        ),
        "quality_gates": {
            "has_negative_triggers": bool(spec.do_not_use_when),
            "has_safety_gates": bool(spec.safety_gates),
            "has_verification": bool(spec.verification),
            "has_removal_path": bool(spec.removal_path),
        },
    }
    (candidate_dir / "skill_factory_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )


def build_registry_candidate(
    spec: SkillSpec,
    *,
    candidate_dir: Path,
    active_dir: Path | None,
) -> dict[str, object]:
    active_surface = active_dir / "SKILL.md" if active_dir else candidate_dir / "SKILL.md"
    return {
        "name": spec.name,
        "group": "codex_generated_skill",
        "adoption_shape": "adopt" if active_dir else "staging",
        "source": str(candidate_dir / "SKILL.md"),
        "source_state": "local_skill_factory_generated",
        "active_surface": str(active_surface),
        "first_local_step": spec.workflow[0] if spec.workflow else spec.purpose,
        "promotion_gate": (
            "Skill factory gates pass: no provider/quota, no active duplicate, "
            "negative triggers, safety gates, verification, and removal path present."
        ),
        "enabled": bool(active_dir),
        "notes": "Generated by codex-skill-factory; review overlap before long-term retention.",
    }


def project_skills_root(project_root: Path) -> Path:
    return project_root / ".agents" / "skills"


def project_manifest_path(project_root: Path) -> Path:
    return project_root / ".codex" / "skill_manifest.lock"


def project_candidate_root(candidate_root: Path, project_root: Path) -> Path:
    return candidate_root / "projects" / normalize_name(project_root.name)


def append_project_manifest_entry(
    manifest_path: Path,
    spec: SkillSpec,
    *,
    project_root: Path,
) -> None:
    text = manifest_path.read_text(encoding="utf-8")
    if re.search(rf'^name\s*=\s*"{re.escape(spec.name)}"$', text, re.M):
        return
    entry = (
        "\n"
        "[[entries]]\n"
        f'name = "{_toml_quote(spec.name)}"\n'
        'entry_type = "repo_skill"\n'
        f'source = ".agents/skills/{_toml_quote(spec.name)}/SKILL.md"\n'
        'source_ref = "repo"\n'
        f'scope = "project_{_toml_quote(normalize_scope(project_root.name))}"\n'
        'decision = "enabled_repo_local"\n'
        "enabled = true\n"
        "implicit_invocation = true\n"
        'review_status = "repo_owned"\n'
        'risk = "low"\n'
        'allowed_scripts = "repo_policy"\n'
        'commit = ""\n'
        'negative_trigger_tests = "repo_policy"\n'
        'notes = "Generated by codex-skill-factory after project-local routing."\n'
    )
    manifest_path.write_text(text.rstrip() + "\n" + entry, encoding="utf-8")


def _report_status(report_path: Path) -> str | None:
    if not report_path.exists():
        return None
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    status = report.get("status")
    return str(status) if status else None


def _validate_skill_file_shape(
    skill_md: Path,
    *,
    require_factory_sections: bool,
) -> list[str]:
    errors: list[str] = []
    text = skill_md.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---\n"):
        errors.append(f"SKILL.md missing frontmatter: {skill_md}")
    if not re.search(r"^name:\s*.+$", text, re.M):
        errors.append(f"SKILL.md missing frontmatter name: {skill_md}")
    if not re.search(r"^description:\s*.+$", text, re.M):
        errors.append(f"SKILL.md missing frontmatter description: {skill_md}")
    if require_factory_sections:
        for heading in SECTION_ORDER:
            if f"## {heading}" not in text:
                errors.append(f"SKILL.md missing section {heading}: {skill_md}")
    if "TODO" in text:
        errors.append(f"SKILL.md still contains TODO: {skill_md}")
    return errors


def _spec_from_skill(skill_md: Path) -> SkillSpec:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---", text, re.S)
    frontmatter = match.group(1) if match else ""
    name = _frontmatter_value(frontmatter, "name")
    description = _frontmatter_value(frontmatter, "description")
    return SkillSpec(
        name=normalize_name(name),
        description=description,
        purpose="Promoted from a validated candidate.",
        use_when=["See active SKILL.md."],
        do_not_use_when=["See active SKILL.md."],
        inputs=["See active SKILL.md."],
        outputs=["See active SKILL.md."],
        workflow=["See active SKILL.md."],
        safety_gates=["See active SKILL.md."],
        verification=["See active SKILL.md."],
        removal_path=(
            "Remove or replace through the Skill factory if triggers become "
            "stale or duplicated."
        ),
    )


def _frontmatter_value(frontmatter: str, key: str) -> str:
    for line in frontmatter.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _numbered(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, 1))


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]{3,}", text.lower())
    stop = {
        "skill",
        "when",
        "with",
        "this",
        "that",
        "from",
        "into",
        "use",
        "uses",
        "using",
        "should",
        "must",
    }
    return {word for word in words if word not in stop}


def _infer_name(brief: str) -> str:
    ascii_words = re.findall(r"[a-zA-Z0-9]+", brief.lower())
    if ascii_words:
        return "-".join(ascii_words[:5])
    return "codex-recurring-workflow"


def _infer_purpose(brief: str) -> str:
    clean = brief.strip().rstrip(".。")
    if not clean:
        return "handle a recurring Codex workflow"
    if len(clean) <= 120:
        return clean
    return clean[:117].rstrip() + "..."


def _yaml_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _toml_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def normalize_scope(value: str) -> str:
    return normalize_name(value).replace("-", "_")


def title(name: str) -> str:
    return " ".join(part.capitalize() for part in name.split("-"))


def git_hook_path(project_root: Path) -> Path:
    return project_root / ".git" / "hooks" / "pre-commit"


def build_pre_commit_hook(project_root: Path) -> str:
    project = project_root.as_posix()
    factory = Path(__file__).resolve().as_posix()
    return (
        "#!/bin/sh\n"
        f"# {HOOK_MARKER}\n"
        'if [ "$SKILL_FACTORY_HOOK_SKIP" = "1" ]; then\n'
        '  echo "skill factory hook skipped by SKILL_FACTORY_HOOK_SKIP=1"\n'
        "  exit 0\n"
        "fi\n"
        f'uv run python "{factory}" doctor --project "{project}"\n'
    )


def hook_status(project_root: Path) -> PipelineResult:
    hook = git_hook_path(project_root)
    if not hook.exists():
        return PipelineResult(
            "ok",
            "skill-factory-hook",
            str(hook),
            None,
            [],
            ["pre-commit hook is not installed"],
        )
    text = hook.read_text(encoding="utf-8", errors="ignore")
    if HOOK_MARKER not in text:
        return PipelineResult(
            "rejected",
            "skill-factory-hook",
            str(hook),
            None,
            ["pre-commit hook exists but is not managed by codex-skill-factory"],
            [],
        )
    return PipelineResult("ok", "skill-factory-hook", str(hook), str(hook), [], [])


def install_hook(project_root: Path, *, force: bool = False) -> PipelineResult:
    hooks_dir = project_root / ".git" / "hooks"
    hook = hooks_dir / "pre-commit"
    if not hooks_dir.exists():
        return PipelineResult(
            "rejected",
            "skill-factory-hook",
            str(hook),
            None,
            [f"git hooks directory missing: {hooks_dir}"],
            [],
        )
    if hook.exists():
        text = hook.read_text(encoding="utf-8", errors="ignore")
        if HOOK_MARKER not in text and not force:
            return PipelineResult(
                "rejected",
                "skill-factory-hook",
                str(hook),
                None,
                ["unmanaged pre-commit hook exists; rerun with --force to replace"],
                [],
            )
    hook.write_text(build_pre_commit_hook(project_root), encoding="utf-8", newline="\n")
    with suppress(OSError):
        hook.chmod(0o755)
    return PipelineResult("installed", "skill-factory-hook", str(hook), str(hook), [], [])


def uninstall_hook(project_root: Path, *, force: bool = False) -> PipelineResult:
    hook = git_hook_path(project_root)
    if not hook.exists():
        return PipelineResult(
            "ok",
            "skill-factory-hook",
            str(hook),
            None,
            [],
            ["pre-commit hook is already absent"],
        )
    text = hook.read_text(encoding="utf-8", errors="ignore")
    if HOOK_MARKER not in text and not force:
        return PipelineResult(
            "rejected",
            "skill-factory-hook",
            str(hook),
            None,
            ["unmanaged pre-commit hook exists; rerun with --force to remove"],
            [],
        )
    hook.unlink()
    return PipelineResult("uninstalled", "skill-factory-hook", str(hook), None, [], [])


def run_hook(project_root: Path) -> PipelineResult:
    if "SKILL_FACTORY_HOOK_SKIP" in dict_from_environ():
        return PipelineResult(
            "ok",
            "skill-factory-hook",
            str(git_hook_path(project_root)),
            None,
            [],
            ["hook skipped by SKILL_FACTORY_HOOK_SKIP"],
        )
    return doctor_pipeline(project_root=project_root)


def dict_from_environ() -> dict[str, str]:
    import os

    return dict(os.environ)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create, validate, and store Codex Skills from a spec."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser(
        "create",
        help="Create a staged Skill candidate from a JSON spec.",
    )
    create.add_argument("--spec", required=True, type=Path)
    create.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT)
    create.add_argument("--target", choices=TARGETS, default="auto")
    create.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    create.add_argument("--active-root", type=Path, default=DEFAULT_ACTIVE_ROOT)
    create.add_argument("--force", action="store_true")
    create.add_argument(
        "--promote",
        action="store_true",
        help="Promote immediately after all creation gates pass.",
    )

    create_brief = subparsers.add_parser(
        "create-from-brief",
        help="Create a Skill candidate from a natural-language recurring workflow brief.",
    )
    create_brief.add_argument("brief")
    create_brief.add_argument("--name")
    create_brief.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT)
    create_brief.add_argument("--target", choices=TARGETS, default="auto")
    create_brief.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    create_brief.add_argument("--active-root", type=Path, default=DEFAULT_ACTIVE_ROOT)
    create_brief.add_argument("--force", action="store_true")
    create_brief.add_argument(
        "--promote",
        action="store_true",
        help="Promote immediately after all creation gates pass.",
    )

    classify = subparsers.add_parser(
        "classify",
        help="Classify whether a Skill brief belongs in codex, project, or should be rejected.",
    )
    classify.add_argument("brief")
    classify.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT)
    classify.add_argument("--target", choices=TARGETS, default="auto")

    promote = subparsers.add_parser(
        "promote",
        help="Promote a staged candidate into the active Skill root.",
    )
    promote.add_argument("name")
    promote.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    promote.add_argument("--active-root", type=Path, default=DEFAULT_ACTIVE_ROOT)
    promote.add_argument("--force", action="store_true")

    check = subparsers.add_parser(
        "check",
        help="Check Skill factory candidate and active storage health.",
    )
    check.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    check.add_argument("--active-root", type=Path, default=DEFAULT_ACTIVE_ROOT)

    doctor = subparsers.add_parser(
        "doctor",
        help="Run Skill factory health checks plus foundation cross-Skill audit.",
    )
    doctor.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT)
    doctor.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    doctor.add_argument("--active-root", type=Path, default=DEFAULT_ACTIVE_ROOT)
    doctor.add_argument("--skill-audit", type=Path, default=DEFAULT_SKILL_AUDIT)

    hook_install = subparsers.add_parser(
        "install-hook",
        help="Install the managed pre-commit hook for a project.",
    )
    hook_install.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT)
    hook_install.add_argument("--force", action="store_true")

    hook_status_parser = subparsers.add_parser(
        "hook-status",
        help="Show whether the managed pre-commit hook is installed.",
    )
    hook_status_parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT)

    hook_uninstall = subparsers.add_parser(
        "uninstall-hook",
        help="Remove the managed pre-commit hook for a project.",
    )
    hook_uninstall.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT)
    hook_uninstall.add_argument("--force", action="store_true")

    hook_run = subparsers.add_parser(
        "run-hook",
        help="Run the same doctor check used by the pre-commit hook.",
    )
    hook_run.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT)

    args = parser.parse_args(argv)
    if args.command == "create":
        spec = load_spec(args.spec)
        result = create_candidate(
            spec,
            candidate_root=args.candidate_root,
            active_root=args.active_root,
            force=args.force,
            auto_promote=args.promote,
        ) if args.target == "codex" else create_routed_spec(
            spec,
            classification_text=f"{spec.description} {spec.purpose}",
            project_root=args.project,
            target=args.target,
            candidate_root=args.candidate_root,
            active_root=args.active_root,
            force=args.force,
            auto_promote=args.promote,
        )
    elif args.command == "create-from-brief":
        result = create_routed_from_brief(
            args.brief,
            name=args.name,
            project_root=args.project,
            target=args.target,
            candidate_root=args.candidate_root,
            active_root=args.active_root,
            force=args.force,
            auto_promote=args.promote,
        )
    elif args.command == "classify":
        decision = classify_placement(
            args.brief,
            project_root=args.project,
            target=args.target,
        )
        print(json.dumps(decision.__dict__, indent=2, ensure_ascii=False))
        return 0 if not decision.errors else 2
    elif args.command == "promote":
        result = promote_candidate(
            args.name,
            candidate_root=args.candidate_root,
            active_root=args.active_root,
            force=args.force,
        )
    elif args.command == "check":
        result = check_pipeline(candidate_root=args.candidate_root, active_root=args.active_root)
    elif args.command == "doctor":
        result = doctor_pipeline(
            project_root=args.project,
            candidate_root=args.candidate_root,
            active_root=args.active_root,
            skill_audit_path=args.skill_audit,
        )
    elif args.command == "install-hook":
        result = install_hook(args.project, force=args.force)
    elif args.command == "hook-status":
        result = hook_status(args.project)
    elif args.command == "uninstall-hook":
        result = uninstall_hook(args.project, force=args.force)
    else:
        result = run_hook(args.project)
    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))
    return 0 if not result.errors else 2


if __name__ == "__main__":
    sys.exit(main())
