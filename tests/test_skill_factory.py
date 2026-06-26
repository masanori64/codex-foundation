from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

FOUNDATION = Path("C:/Users/maasa/.codex/foundation")
SCRIPT = FOUNDATION / "skill_factory.py"
REGISTRY = FOUNDATION / "codex-foundation-registry.toml"


def _load_skill_factory():
    spec = importlib.util.spec_from_file_location("skill_factory", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["skill_factory"] = module
    spec.loader.exec_module(module)
    return module


def _spec(**overrides):
    base = {
        "name": "invoice-cleanup-helper",
        "description": (
            "Use when Codex repeatedly normalizes local invoice CSV files "
            "without provider calls."
        ),
        "purpose": "normalize local invoice CSV cleanup steps",
        "use_when": [
            "User asks to normalize a local invoice CSV with the recurring house format."
        ],
        "do_not_use_when": [
            "The task needs external provider calls, OCR, or one-off accounting advice."
        ],
        "inputs": ["Local CSV path", "Target column contract"],
        "outputs": ["Cleaned CSV", "Validation summary"],
        "workflow": [
            "Inspect the input columns.",
            "Apply the house cleanup order.",
            "Run local validation.",
        ],
        "safety_gates": [
            "Do not call providers or network APIs.",
            "Do not overwrite source files.",
        ],
        "verification": ["Run the local validator on a copy."],
        "removal_path": (
            "Retire this Skill if invoice cleanup stops recurring or overlaps "
            "a stronger data-cleaning Skill."
        ),
    }
    base.update(overrides)
    return base


def _project_with_manifest(tmp_path: Path, name: str = "research_x") -> Path:
    project = tmp_path / name
    manifest = project / ".codex" / "skill_manifest.lock"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        'lockfile_version = 1\nowner = "test_project"\n\n[policy]\n'
        'repo_skills_path = ".agents/skills"\n',
        encoding="utf-8",
    )
    return project


def test_create_candidate_generates_skill_and_interface(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(_spec()), encoding="utf-8")

    result = skill_factory.create_candidate(
        skill_factory.load_spec(spec_path),
        candidate_root=tmp_path / "candidates",
        active_root=tmp_path / "active",
    )

    skill_dir = tmp_path / "candidates" / "invoice-cleanup-helper"
    assert result.status == "candidate"
    assert result.errors == []
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "agents" / "openai.yaml").exists()
    assert (skill_dir / "skill_factory_report.json").exists()
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "## Do Not Use When" in text
    assert "## Removal Path" in text
    report = json.loads((skill_dir / "skill_factory_report.json").read_text(encoding="utf-8"))
    assert report["registry_candidate"]["name"] == "invoice-cleanup-helper"
    assert report["registry_candidate"]["adoption_shape"] == "staging"


def test_provider_or_quota_spec_is_rejected(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    spec = skill_factory.SkillSpec(**_spec(provider_or_quota=True))

    result = skill_factory.create_candidate(
        spec,
        candidate_root=tmp_path / "candidates",
        active_root=tmp_path / "active",
    )

    assert result.status == "rejected"
    assert any("provider_or_quota" in error for error in result.errors)


def test_duplicate_active_skill_is_rejected(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    active = tmp_path / "active" / "invoice-cleanup-helper"
    active.mkdir(parents=True)
    (active / "SKILL.md").write_text(
        "---\nname: invoice-cleanup-helper\ndescription: Existing Skill.\n---\n",
        encoding="utf-8",
    )

    result = skill_factory.create_candidate(
        skill_factory.SkillSpec(**_spec()),
        candidate_root=tmp_path / "candidates",
        active_root=tmp_path / "active",
    )

    assert result.status == "rejected"
    assert any("active Skill already exists" in error for error in result.errors)


def test_promote_candidate_copies_to_active_root(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    candidate_root = tmp_path / "candidates"
    active_root = tmp_path / "active"
    create_result = skill_factory.create_candidate(
        skill_factory.SkillSpec(**_spec()),
        candidate_root=candidate_root,
        active_root=active_root,
    )
    assert create_result.status == "candidate"

    promote_result = skill_factory.promote_candidate(
        "invoice-cleanup-helper",
        candidate_root=candidate_root,
        active_root=active_root,
    )

    assert promote_result.status == "promoted"
    assert (active_root / "invoice-cleanup-helper" / "SKILL.md").exists()
    report = json.loads(
        (candidate_root / "invoice-cleanup-helper" / "skill_factory_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["registry_candidate"]["adoption_shape"] == "adopt"
    assert report["registry_candidate"]["enabled"] is True


def test_create_with_auto_promote_stores_active_skill(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    candidate_root = tmp_path / "candidates"
    active_root = tmp_path / "active"

    result = skill_factory.create_candidate(
        skill_factory.SkillSpec(**_spec()),
        candidate_root=candidate_root,
        active_root=active_root,
        auto_promote=True,
    )

    assert result.status == "promoted"
    assert (candidate_root / "invoice-cleanup-helper" / "SKILL.md").exists()
    assert (active_root / "invoice-cleanup-helper" / "SKILL.md").exists()


def test_create_from_brief_generates_and_promotes_skill(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    candidate_root = tmp_path / "candidates"
    active_root = tmp_path / "active"

    result = skill_factory.create_from_brief(
        "clean recurring local meeting notes into the house format",
        name="meeting-note-cleaner",
        candidate_root=candidate_root,
        active_root=active_root,
        auto_promote=True,
    )

    assert result.status == "promoted"
    skill = active_root / "meeting-note-cleaner" / "SKILL.md"
    assert skill.exists()
    text = skill.read_text(encoding="utf-8")
    assert "clean recurring local meeting notes into the house format" in text
    assert "Do not call providers or network APIs." in text


def test_create_from_brief_rejects_provider_quota_work(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()

    result = skill_factory.create_from_brief(
        "call OpenAI API to summarize recurring meeting notes",
        name="provider-backed-meeting-summary",
        candidate_root=tmp_path / "candidates",
        active_root=tmp_path / "active",
    )

    assert result.status == "rejected"
    assert any("provider_or_quota" in error for error in result.errors)


def test_classify_routes_codex_foundation_work_to_codex(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    project = _project_with_manifest(tmp_path)

    decision = skill_factory.classify_placement(
        "improve Codex handoff and session governance",
        project_root=project,
    )

    assert decision.status == "ok"
    assert decision.target == "codex"


def test_classify_routes_project_work_to_project(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    project = _project_with_manifest(tmp_path)

    decision = skill_factory.classify_placement(
        "research_x citation verification workflow",
        project_root=project,
    )

    assert decision.status == "ok"
    assert decision.target == "project"


def test_classify_rejects_one_off_and_provider_work(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    project = _project_with_manifest(tmp_path)

    one_off = skill_factory.classify_placement("今回だけのメモ", project_root=project)
    provider = skill_factory.classify_placement(
        "OpenAI API backed recurring summary workflow",
        project_root=project,
    )

    assert one_off.status == "rejected"
    assert provider.status == "rejected"


def test_create_routed_project_skill_updates_manifest(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    project = _project_with_manifest(tmp_path)

    result = skill_factory.create_routed_from_brief(
        "research_x citation verification workflow",
        name="research-x-citation-check",
        project_root=project,
        target="project",
        candidate_root=tmp_path / "candidates",
        auto_promote=True,
    )

    skill = project / ".agents" / "skills" / "research-x-citation-check" / "SKILL.md"
    manifest = project / ".codex" / "skill_manifest.lock"
    assert result.status == "promoted"
    assert skill.exists()
    manifest_text = manifest.read_text(encoding="utf-8")
    assert 'name = "research-x-citation-check"' in manifest_text
    assert 'scope = "project_research_x"' in manifest_text


def test_project_skill_creation_rejects_uninitialized_project(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()

    result = skill_factory.create_routed_from_brief(
        "new_project citation verification workflow",
        name="new-project-citation-check",
        project_root=tmp_path / "new_project",
        target="project",
        candidate_root=tmp_path / "candidates",
        auto_promote=True,
    )

    assert result.status == "rejected"
    assert any("manifest missing" in error for error in result.errors)


def test_check_pipeline_reports_candidate_storage_health(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    candidate_root = tmp_path / "candidates"
    active_root = tmp_path / "active"
    skill_factory.create_candidate(
        skill_factory.SkillSpec(**_spec()),
        candidate_root=candidate_root,
        active_root=active_root,
    )

    result = skill_factory.check_pipeline(
        candidate_root=candidate_root,
        active_root=active_root,
    )

    assert result.status == "ok"
    assert result.errors == []


def test_doctor_pipeline_combines_factory_and_foundation_audit(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    audit = tmp_path / "skill_audit.py"
    audit.write_text(
        "def validate_skill_audit(*, project_root):\n"
        "    return []\n",
        encoding="utf-8",
    )

    result = skill_factory.doctor_pipeline(
        project_root=tmp_path / "project",
        candidate_root=tmp_path / "candidates",
        active_root=tmp_path / "active",
        skill_audit_path=audit,
    )

    assert result.status == "ok"
    assert result.errors == []


def test_doctor_pipeline_reports_foundation_audit_errors(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    audit = tmp_path / "skill_audit.py"
    audit.write_text(
        "def validate_skill_audit(*, project_root):\n"
        "    return ['audit failure']\n",
        encoding="utf-8",
    )

    result = skill_factory.doctor_pipeline(
        project_root=tmp_path / "project",
        candidate_root=tmp_path / "candidates",
        active_root=tmp_path / "active",
        skill_audit_path=audit,
    )

    assert result.status == "rejected"
    assert "audit failure" in result.errors


def test_hook_install_status_and_uninstall(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    project = tmp_path / "project"
    hooks = project / ".git" / "hooks"
    hooks.mkdir(parents=True)

    install = skill_factory.install_hook(project)
    status = skill_factory.hook_status(project)
    hook_text = (hooks / "pre-commit").read_text(encoding="utf-8")
    uninstall = skill_factory.uninstall_hook(project)

    assert install.status == "installed"
    assert status.status == "ok"
    assert "skill_factory.py\" doctor" in hook_text
    assert uninstall.status == "uninstalled"
    assert not (hooks / "pre-commit").exists()


def test_hook_does_not_overwrite_unmanaged_without_force(tmp_path: Path) -> None:
    skill_factory = _load_skill_factory()
    project = tmp_path / "project"
    hook = project / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True)
    hook.write_text("#!/bin/sh\necho unmanaged\n", encoding="utf-8")

    result = skill_factory.install_hook(project)

    assert result.status == "rejected"
    assert "unmanaged" in hook.read_text(encoding="utf-8")


def test_run_hook_respects_skip_env(tmp_path: Path, monkeypatch) -> None:
    skill_factory = _load_skill_factory()
    monkeypatch.setenv("SKILL_FACTORY_HOOK_SKIP", "1")

    result = skill_factory.run_hook(tmp_path / "project")

    assert result.status == "ok"
    assert result.warnings == ["hook skipped by SKILL_FACTORY_HOOK_SKIP"]


def test_foundation_registry_owns_skill_factory() -> None:
    registry = REGISTRY.read_text(encoding="utf-8")

    assert 'name = "codex-skill-factory"' in registry
    assert "spec -> candidate -> quality gate -> promotion" in registry
    assert "target-layer routing" in registry
    assert "managed pre-commit hook" in registry
