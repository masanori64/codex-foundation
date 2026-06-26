from __future__ import annotations

import json
from pathlib import Path

from codex_pipeline.cli import main


def test_cli_validate_and_render_dashboard(codex_project: Path) -> None:
    project = str(codex_project)
    root = Path(project)

    assert main(["generate-github-wrappers", "--project", project]) == 0
    assert main(["generate-pages-workflows", "--project", project]) == 0
    assert main(["render-dashboard", "--project", project]) == 0
    assert main(["render-mermaid", "--project", project]) == 0
    assert main(["validate", "--project", project]) == 0
    assert main(["check-cost", "--project", project]) == 0
    assert main(["audit-workflow-artifacts", "--project", project]) == 0
    assert main(["audit-workflow-smoke", "--project", project]) == 0
    assert main(["subagent-dry-run", "--project", project]) == 0
    report = root / "subagent-report.json"
    report.write_text(
        json.dumps(
            {
                "agent": "ci_log_auditor",
                "mode": "read_only",
                "status": "passed",
                "summary": "reviewed CI logs",
                "control_artifact": True,
                "not_evidence": True,
                "not_citation": True,
                "raw_log_in_project": False,
                "forbidden_actions_executed": [],
                "provider_api_calls": False,
                "paid_usage_detected": False,
                "secrets_used": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    assert main(["validate-subagent-report", "--project", project, "--report", str(report)]) == 0
    assert main(["validate-github-wrappers", "--project", project]) == 0

    assert (root / "docs/control/codex/dashboard/index.html").exists()
    assert (root / "docs/control/codex/dashboard/data/dashboard-state.json").exists()
    assert (root / "docs/control/codex/dashboard/mermaid/pipeline.mmd").exists()
    assert (root / ".codex-project/generated/effective-profile.yml").exists()
    assert (root / ".codex-project/generated/effective-cost-guard.json").exists()
    assert (root / ".codex-project/generated/effective-workflow-artifact-audit.json").exists()
    assert (root / ".codex-project/generated/effective-workflow-smoke.json").exists()
    assert (root / ".codex-project/generated/effective-e2e-completion-manifest.json").exists()
    assert (root / ".codex-project/generated/effective-subagent-runtime-dry-run.json").exists()
    assert (root / ".github/workflows/codex-ci.yml").exists()
    assert (root / ".github/workflows/codex-dashboard.yml").exists()
    assert (root / ".github/workflows/codex-preview.yml").exists()
    assert (root / ".github/workflows/codex-artifact-smoke.yml").exists()
