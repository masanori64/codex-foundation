from __future__ import annotations

import importlib.util
from pathlib import Path

FOUNDATION = Path("C:/Users/maasa/.codex/foundation")
RESEARCH_X = Path("C:/Users/maasa/research_x")
SCRIPT = FOUNDATION / "skill_audit.py"


def _load_skill_audit():
    spec = importlib.util.spec_from_file_location("skill_audit", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_minimal_project(tmp_path: Path) -> Path:
    project = tmp_path / "research_x"
    for path in (
        ".codex/skill_manifest.lock",
        "control/vendor_sources.lock.md",
        "control/adoption_registry.toml",
    ):
        source = RESEARCH_X / path
        target = project / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    for source in sorted((RESEARCH_X / ".agents" / "skills").glob("*/SKILL.md")):
        target = project / source.relative_to(RESEARCH_X)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return project


def test_foundation_skill_audit_accepts_research_x_as_external_project() -> None:
    skill_audit = _load_skill_audit()

    errors = skill_audit.validate_skill_audit(project_root=RESEARCH_X)

    assert errors == []


def test_research_x_no_longer_owns_skill_audit_surfaces() -> None:
    assert not (RESEARCH_X / "control" / "skill_quality_audit.toml").exists()
    assert not (RESEARCH_X / "scripts" / "validate_skill_quality_audit.py").exists()
    assert not (RESEARCH_X / "tests" / "skills" / "test_skill_quality_audit.py").exists()


def test_foundation_registry_owns_skill_audit_tool() -> None:
    registry = (FOUNDATION / "codex-foundation-registry.toml").read_text(encoding="utf-8")

    assert 'name = "codex-skill-audit"' in registry
    assert "projects remain audit targets, not audit owners" in registry
    assert "no Skill invocation" in registry


def test_unmanifested_project_skill_is_rejected(tmp_path: Path) -> None:
    skill_audit = _load_skill_audit()
    project = _copy_minimal_project(tmp_path)
    extra_skill = project / ".agents" / "skills" / "unmanifested-skill"
    extra_skill.mkdir(parents=True)
    (extra_skill / "SKILL.md").write_text(
        "---\nname: unmanifested-skill\n---\n\n# Unmanifested\n",
        encoding="utf-8",
    )

    errors = skill_audit.validate_skill_audit(project_root=project)

    assert any(
        "SKILL.md exists but manifest has no repo_skill entry" in error for error in errors
    )


def test_retired_project_skill_cannot_reenter_active_tree(tmp_path: Path) -> None:
    skill_audit = _load_skill_audit()
    project = _copy_minimal_project(tmp_path)
    active_retired = project / ".agents" / "skills" / "research-x-goal-runner"
    active_retired.mkdir(parents=True)
    (active_retired / "SKILL.md").write_text(
        "---\nname: research-x-goal-runner\n---\n\n# Retired Copy\n",
        encoding="utf-8",
    )

    errors = skill_audit.validate_skill_audit(project_root=project)

    assert any(
        "retired Skill must not reenter active .agents/skills" in error for error in errors
    )


def test_active_foundation_skill_must_be_registry_enabled(tmp_path: Path) -> None:
    skill_audit = _load_skill_audit()
    skill_root = tmp_path / "skills"
    skill_dir = skill_root / "noisy-source-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: noisy-source-skill\n---\n\n# Noisy Source Skill\n",
        encoding="utf-8",
    )
    registry = tmp_path / "registry.toml"
    registry.write_text(
        """
[[candidates]]
name = "noisy-source-skill"
adoption_shape = "staging"
source_state = "source_locked_reference"
enabled = false
""".strip(),
        encoding="utf-8",
    )
    errors: list[str] = []

    skill_audit._validate_active_foundation_skills(  # noqa: SLF001
        {"retired_foundation_skills": []},
        {
            "codex_personal_skill_root": skill_root,
            "codex_foundation_registry": registry,
        },
        errors,
    )

    assert "noisy-source-skill: active foundation Skill candidate must be enabled" in errors
    assert "noisy-source-skill: active foundation Skill adoption_shape must be adopt" in errors
    assert (
        "noisy-source-skill: active foundation Skill source_state must be installed/local"
        in errors
    )
    assert "noisy-source-skill: description must name a concrete trigger and behavior" in errors
    assert "noisy-source-skill: SKILL.md must include ## Use When" in errors
    assert "noisy-source-skill: SKILL.md must include ## Do Not Use When" in errors


def test_active_foundation_skill_semantic_audit_rejects_ungated_risky_terms(
    tmp_path: Path,
) -> None:
    skill_audit = _load_skill_audit()
    skill_path = tmp_path / "risky-skill" / "SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text(
        """---
name: risky-skill
description: Use when this risky source wants to run external browser plugin actions.
---

# Risky Skill

## Use When

Use for risky source workflows.

## Do Not Use When

This section exists but does not narrow unsafe cases.

Run browser plugin provider hook actions.
""",
        encoding="utf-8",
    )
    errors: list[str] = []

    skill_audit._validate_skill_semantics(  # noqa: SLF001
        "risky-skill",
        skill_path,
        {
            "source": "https://example.test/risky-skill",
            "source_state": "installed_local_skill",
        },
        errors,
    )

    assert any("risky terms need explicit approval/gating language" in error for error in errors)
    assert any("externally sourced active Skill must be source-locked" in error for error in errors)


def test_bad_agent_skill_arxiv_locator_is_rejected_outside_quarantine(
    tmp_path: Path,
) -> None:
    skill_audit = _load_skill_audit()
    registry = tmp_path / "registry.toml"
    vendor_lock = tmp_path / "vendor_sources.lock.md"
    inventory = tmp_path / "source-origin-inventory.md"
    registry.write_text(
        """
[[candidates]]
name = "bad-agent-skills-source"
source = "https://arxiv.org/html/2605.13221"
""".strip(),
        encoding="utf-8",
    )
    vendor_lock.write_text(
        "| Candidate | Source | Locked decision |\n"
        "|---|---|---|\n"
        "| `bad` | arxiv:2605.13221 | Incorrect active locator. |\n",
        encoding="utf-8",
    )
    inventory.write_text(
        "`quarantined_bad_locator`: current arXiv content is unrelated "
        "UAV logistics scheduling\n2605.13221\n",
        encoding="utf-8",
    )
    errors: list[str] = []

    skill_audit._validate_foundation_source_provenance(  # noqa: SLF001
        tmp_path,
        {
            "codex_foundation_registry": registry,
            "codex_foundation_vendor_sources": vendor_lock,
        },
        errors,
    )

    assert any(
        "codex_foundation_registry: bad Agent Skills/security locator" in error
        for error in errors
    )
    assert any(
        "codex_foundation_vendor_sources: bad Agent Skills/security locator" in error
        for error in errors
    )


def test_retired_foundation_skill_cannot_reenter_active_skill_root(tmp_path: Path) -> None:
    skill_audit = _load_skill_audit()
    skill_root = tmp_path / "skills"
    skill_dir = skill_root / "skillopt-sleep"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: skillopt-sleep\n---\n\n# Retired Copy\n",
        encoding="utf-8",
    )
    registry = tmp_path / "registry.toml"
    registry.write_text(
        """
[[candidates]]
name = "skillopt"
surface_alias = "skillopt-sleep"
adoption_shape = "reference_only"
source_state = "imported"
enabled = false
""".strip(),
        encoding="utf-8",
    )
    errors: list[str] = []

    skill_audit._validate_active_foundation_skills(  # noqa: SLF001
        {
            "retired_foundation_skills": [
                {
                    "name": "skillopt-sleep",
                    "decision": "deleted_active_skill_surface_20260626",
                }
            ]
        },
        {
            "codex_personal_skill_root": skill_root,
            "codex_foundation_registry": registry,
        },
        errors,
    )

    assert any("retired foundation Skill must not reenter active" in error for error in errors)


def test_source_locked_staging_candidate_cannot_be_enabled(tmp_path: Path) -> None:
    skill_audit = _load_skill_audit()
    registry = tmp_path / "registry.toml"
    vendor_lock = tmp_path / "vendor_sources.lock.md"
    registry.write_text(
        """
[[candidates]]
name = "evoskill"
source = "https://github.com/sentient-agi/EvoSkill"
source_state = "source_locked_reference"
active_surface = "staging"
enabled = true
""".strip(),
        encoding="utf-8",
    )
    vendor_lock.write_text(
        "| Candidate | Source | Locked decision |\n"
        "|---|---|---|\n"
        "| `evoskill` | https://github.com/sentient-agi/EvoSkill | Staging only. |\n",
        encoding="utf-8",
    )
    errors: list[str] = []

    skill_audit._validate_foundation_registry_source_locks(  # noqa: SLF001
        {
            "codex_foundation_registry": registry,
            "codex_foundation_vendor_sources": vendor_lock,
        },
        errors,
    )

    assert any("external source candidate cannot be enabled" in error for error in errors)
    assert any("source-locked staging candidate must stay disabled" in error for error in errors)
