from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_foundation_ci_runs_full_verification_and_artifact_cd() -> None:
    workflow = (ROOT / ".github/workflows/foundation-ci.yml").read_text(encoding="utf-8")
    verify = (ROOT / "scripts/verify-foundation.ps1").read_text(encoding="utf-8")
    package = (ROOT / "scripts/package-foundation.ps1").read_text(encoding="utf-8")
    repo_manifest = (ROOT / "scripts/write-foundation-repo-manifest.py").read_text(
        encoding="utf-8"
    )

    assert "push:" in workflow
    assert "pull_request:" in workflow
    assert ".\\scripts\\verify-foundation.ps1" in workflow
    assert "-Portable" in workflow
    assert ".\\scripts\\package-foundation.ps1 -OutputDir foundation-dist" in workflow
    assert (
        "foundation-rollback-plan.ps1 -TargetRef HEAD -OutputPath "
        "foundation-dist/foundation-rollback-plan.json"
    ) in workflow
    assert "foundation-dist/*.zip" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "concurrency:" in workflow
    assert "timeout-minutes: 20" in workflow
    assert "timeout-minutes: 15" in workflow
    assert "persist-credentials: false" in workflow
    assert "retention-days: 14" in workflow

    assert "uv run ruff check @RuffTargets" in verify
    for target in (
        "codex_improvement",
        "pipeline",
        "scripts",
        "tests",
        "offline_canaries.py",
        "skill_audit.py",
        "skill_factory.py",
    ):
        assert f'"{target}"' in verify
    assert "test_foundation_cicd_contract.py" in verify
    assert "pipeline\\tests" in verify
    assert '@("tests", "pipeline\\tests")' in verify
    assert "validate_foundation_manifest" in verify
    assert "write-foundation-repo-manifest.py --check" in verify
    assert "pipeline/FOUNDATION_MANIFEST.json" in verify
    assert "FOUNDATION_REPO_MANIFEST.json" in verify

    assert "git archive --format=zip" in package
    assert 'cd_mode = "github_actions_artifact"' in package
    assert "paid_usage_detected = $false" in package
    assert "provider_api_calls = $false" in package
    assert "secrets_used = $false" in package

    assert "foundation_repo_manifest" in repo_manifest
    assert 'MANIFEST_ROOT = "."' in repo_manifest
    assert '"root": MANIFEST_ROOT' in repo_manifest
    assert "foundation repo manifest root must be repository-relative '.'" in repo_manifest
    assert "github_actions_artifact" in repo_manifest
    assert '"project_plans"' in repo_manifest
    assert '"scripts"' in repo_manifest
    assert '"tests"' in repo_manifest


def test_foundation_repo_manifest_root_is_portable() -> None:
    manifest = json.loads((ROOT / "FOUNDATION_REPO_MANIFEST.json").read_text(encoding="utf-8"))

    assert manifest["root"] == "."


def test_root_readme_describes_generic_target_project_and_no_cost_cd() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    forbidden = "C:/Users/" + "maasa/research_x"

    assert forbidden not in readme
    assert forbidden.replace("/", "\\") not in readme
    assert "For any target project with `.codex-project/profile.yml`" in readme
    assert "GitHub Actions artifact package" in readme
    assert "not deployed to a paid cloud service" in readme
    assert ".foundation-dist/" in gitignore


def test_foundation_rollback_plan_is_plan_only_and_refuses_dangerous_classes() -> None:
    rollback = (ROOT / "scripts/foundation-rollback-plan.ps1").read_text(encoding="utf-8")

    assert 'rollback_class = "git_artifact_foundation_source"' in rollback
    assert "rollback_executed = $false" in rollback
    assert "plan_only_until_human_or_goal_explicitly_requests_revert_commit" in rollback
    assert "git_history_rewrite" in rollback
    assert "provider_api_quota" in rollback
    assert "secret_restore" in rollback
    assert "db_restore" in rollback
    assert "external_cloud_deploy" in rollback
