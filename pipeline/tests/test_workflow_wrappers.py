from __future__ import annotations

from pathlib import Path

from codex_pipeline.workflow_wrappers import (
    generate_pages_workflows,
    generate_workflow_wrappers,
    validate_pages_workflows,
    validate_workflow_wrappers,
)


def test_generated_workflow_wrappers_are_thin_and_artifact_only(
    tmp_path: Path,
) -> None:
    result = generate_workflow_wrappers(tmp_path)

    assert result["github_api_calls_executed"] is False
    assert result["deploy_executed"] is False

    errors = validate_workflow_wrappers(
        tmp_path,
        capability_status="artifact_only",
        dashboard_artifact_status="artifact_only",
    )

    assert errors == []
    ci_text = (tmp_path / ".github/workflows/codex-ci.yml").read_text(
        encoding="utf-8"
    )
    dashboard_text = (
        tmp_path / ".github/workflows/codex-dashboard.yml"
    ).read_text(encoding="utf-8")
    preview_text = (tmp_path / ".github/workflows/codex-preview.yml").read_text(
        encoding="utf-8"
    )
    assert "pull_request_target" not in ci_text
    assert "pages: write" not in dashboard_text
    assert "actions/upload-artifact@v4" in dashboard_text
    assert "codex-preview-artifact" in preview_text
    assert "GITHUB_STEP_SUMMARY" in preview_text


def test_generated_pages_workflows_are_free_static_cd(tmp_path: Path) -> None:
    result = generate_pages_workflows(tmp_path)

    assert result["github_pages_static_cd"] is True
    assert result["secrets_used"] is False
    assert result["paid_usage_detected"] is False
    assert validate_pages_workflows(tmp_path) == []

    production_text = (
        tmp_path / ".github/workflows/codex-pages-production.yml"
    ).read_text(encoding="utf-8")
    rollback_text = (
        tmp_path / ".github/workflows/codex-pages-rollback.yml"
    ).read_text(encoding="utf-8")
    assert "pages: write" in production_text
    assert "id-token: write" in production_text
    assert "actions/deploy-pages@v4" in production_text
    assert "PREVIEW_PATH" in production_text
    assert "PREVIEW_COMMIT_PATH" in production_text
    assert 'PREVIEW_PATH="previews/${PREVIEW_REF}/latest"' in production_text
    assert "previews/" in production_text
    assert "rollback/latest" in production_text
    assert "target_ref" in rollback_text
    assert "[codex-rollback-drill]" in rollback_text
    assert "github.event.before" in rollback_text
    assert "PREVIEW_PATH" in rollback_text


def test_workflow_wrappers_reject_disabled_capability(tmp_path: Path) -> None:
    generate_workflow_wrappers(tmp_path)

    errors = validate_workflow_wrappers(
        tmp_path,
        capability_status="disabled",
        dashboard_artifact_status="disabled",
    )

    assert any("capability is disabled" in error for error in errors)
