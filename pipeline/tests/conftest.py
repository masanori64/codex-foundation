from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE))


@pytest.fixture
def codex_project(tmp_path: Path) -> Path:
    project = tmp_path / "research_x"
    (project / ".codex-project").mkdir(parents=True, exist_ok=True)
    _write_profile(project)
    _write_bridge(project)
    return project


def _write_profile(project: Path) -> None:
    boundary = (
        "raw source != searchable document != search result != source bundle "
        "!= context chunk != citation != answer"
    )
    (project / ".codex-project" / "profile.yml").write_text(
        f"""schema_version: 1
project:
  id: research_x
  name: research_x
  root: {project.as_posix()}
  domain: ai_callable_x_memory_search
commands:
  sync: uv sync
  test: uv run pytest
  lint: uv run ruff check src\\research_x tests scripts
constraints:
  use_uv: true
  no_quota_provider_freeze: true
  forbid_control_artifacts_as_evidence: true
  evidence_boundary: {boundary}
  forbidden_external_actions:
    - provider_api_quota
    - secrets_credentials
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
  provider_api_calls: hard_blocked_paid
  mcp_plugin_hook_enablement: outside_free_static_pages_cd
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
    - pr_reviewer
    - ci_log_auditor
    - release_auditor
""",
        encoding="utf-8",
        newline="\n",
    )


def _write_bridge(project: Path) -> None:
    (project / ".codex-project" / "bridge.yml").write_text(
        """schema_version: 1
project_id: research_x
codex_foundation: C:/Users/maasa/.codex
github:
  mode: public_repo_pages_static_cd
  api_enabled: public_read
  repository: masanori64/research_x
  default_branch: main
outputs:
  dashboard_dir: docs/control/codex/dashboard
  generated_dir: .codex-project/generated
  mermaid_dir: docs/control/codex/dashboard/mermaid
workflow:
  phase: static_pages_cd_final
  cd_execution_enabled: true
  rollback_execution_enabled: safe_static_only
  github_pages_enabled_by_codex: enabled_workflow_static_pages
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
  provider_api_calls: hard_blocked_paid
  mcp_plugin_hook_enablement: outside_free_static_pages_cd
""",
        encoding="utf-8",
        newline="\n",
    )
