from __future__ import annotations

from pathlib import Path

from codex_pipeline.validation import _validate_project_boundary


def test_project_boundary_rejects_old_research_x_pipeline_draft(tmp_path: Path) -> None:
    forbidden = tmp_path / ".pipeline" / "pipeline.yml"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("schema_version: 1\n", encoding="utf-8")

    errors = _validate_project_boundary(tmp_path, project_id="dummy_project")

    assert errors
    assert "generic Codex pipeline implementation must not live in project" in errors[0]
