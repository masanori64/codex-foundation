from __future__ import annotations

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
    assert ".\\scripts\\package-foundation.ps1" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "permissions:\n  contents: read" in workflow

    assert "uv run ruff check ." in verify
    assert "uv run pytest tests pipeline\\tests" in verify
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
    assert "github_actions_artifact" in repo_manifest
    assert '"project_plans"' in repo_manifest
    assert '"scripts"' in repo_manifest
    assert '"tests"' in repo_manifest


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
