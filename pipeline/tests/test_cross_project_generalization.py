from __future__ import annotations

from pathlib import Path

from codex_pipeline.cli import main


def test_pipeline_validates_dummy_second_project(tmp_path: Path) -> None:
    project = tmp_path / "dummy_project"
    codex_project = project / ".codex-project"
    codex_project.mkdir(parents=True)
    _write_profile(project)
    _write_bridge(project)

    project_arg = str(project)
    assert main(["generate-github-wrappers", "--project", project_arg]) == 0
    assert main(["generate-pages-workflows", "--project", project_arg]) == 0
    assert main(["render-dashboard", "--project", project_arg]) == 0
    assert main(["render-mermaid", "--project", project_arg]) == 0
    assert main(["validate", "--project", project_arg]) == 0
    assert main(["validate-github-wrappers", "--project", project_arg]) == 0
    assert main(["validate-pages-workflows", "--project", project_arg]) == 0

    assert (project / "docs/control/codex/dashboard/index.html").exists()
    assert (project / "docs/control/codex/dashboard/data/dashboard-state.json").exists()
    assert (project / "docs/control/codex/dashboard/data/control-artifact-audit.json").exists()
    assert (project / ".codex-project/generated/effective-dashboard-state.json").exists()
    assert (project / ".codex-project/generated/effective-control-artifact-audit.json").exists()
    assert str(project).casefold() != "c:/users/maasa/research_x".casefold()


def test_foundation_engine_has_no_research_x_hardcoding() -> None:
    engine = Path(__file__).resolve().parents[1] / "engine" / "codex_pipeline"
    offenders = []
    for path in sorted(engine.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "research_x" in text:
            offenders.append(path.name)

    assert offenders == []


def _write_profile(project: Path) -> None:
    boundary = (
        "raw source != searchable document != search result != source bundle "
        "!= context chunk != citation != answer"
    )
    (project / ".codex-project" / "profile.yml").write_text(
        f"""schema_version: 1
project:
  id: dummy_project
  name: dummy_project
  root: {project.as_posix()}
  domain: dummy_control_target
commands:
  sync: noop
  test: noop
  lint: noop
constraints:
  use_uv: true
  no_quota_provider_freeze: true
  forbid_control_artifacts_as_evidence: true
  evidence_boundary: {boundary}
  forbidden_external_actions:
    - provider_api_quota
    - secrets_credentials
    - install_dependency_model_download
    - mcp_plugin_hook_enablement
    - destructive_action
    - irreversible_db_migration
capabilities:
  github_api_read: public_read_enabled
  github_api_write: pages_static_cd_only
  github_actions_wrappers: enabled
  dashboard_artifact_cd: enabled
  preview_cd: static_pages_lane_enabled
  staging_cd: static_pages_lane_enabled
  production_cd: static_pages_enabled
  rollback_execution: safe_static_pages_enabled
  github_pages: enabled_public_static
  repository_settings_change: free_pages_source_setup_only
  provider_api_calls: disabled
  mcp_plugin_hook_enablement: disabled
control_artifacts:
  output_root: docs/control/codex
  generated_root: .codex-project/generated
  not_evidence: true
  not_research_evidence: true
  not_citation: true
  not_answer_support: true
subagents:
  owner: C:/Users/maasa/.codex
  raw_log_in_project: false
  allowed_roles:
    - impact_mapper
""",
        encoding="utf-8",
        newline="\n",
    )


def _write_bridge(project: Path) -> None:
    (project / ".codex-project" / "bridge.yml").write_text(
        """schema_version: 1
project_id: dummy_project
codex_foundation: C:/Users/maasa/.codex
github:
  mode: public_repo_pages_static_cd
  api_enabled: public_read
  repository: local/dummy_project
  default_branch: main
outputs:
  dashboard_dir: docs/control/codex/dashboard
  generated_dir: .codex-project/generated
  mermaid_dir: docs/control/codex/dashboard/mermaid
workflow:
  phase: static_pages_cd_final
  cd_execution_enabled: true
  rollback_execution_enabled: safe_static_only
  github_pages_enabled_by_codex: pending_free_setup_or_verification
capabilities:
  github_api_read: public_read_enabled
  github_api_write: pages_static_cd_only
  github_actions_wrappers: enabled
  dashboard_artifact_cd: enabled
  preview_cd: static_pages_lane_enabled
  staging_cd: static_pages_lane_enabled
  production_cd: static_pages_enabled
  rollback_execution: safe_static_pages_enabled
  github_pages: enabled_public_static
  repository_settings_change: free_pages_source_setup_only
  provider_api_calls: disabled
  mcp_plugin_hook_enablement: disabled
""",
        encoding="utf-8",
        newline="\n",
    )
