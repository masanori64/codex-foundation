from __future__ import annotations

from codex_pipeline.mermaid_renderer import effective_pipeline, render_pipeline_mermaid


def test_mermaid_mentions_control_artifact_boundary() -> None:
    pipeline = effective_pipeline({"project": {"id": "research_x"}})

    source = render_pipeline_mermaid(pipeline)

    assert "flowchart LR" in source
    assert "control artifact / not evidence / not citation" in source
