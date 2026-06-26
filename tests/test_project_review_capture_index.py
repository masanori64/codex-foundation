from __future__ import annotations

from pathlib import Path

CODEX_PROJECT_REVIEWS = Path(
    "C:/Users/maasa/.codex/foundation/project_reviews/research_x_chatgpt_control"
)
X_GPT_DIR = CODEX_PROJECT_REVIEWS / "x-url-analysis-20260622"
CODEX_CONTEXT_OFFLOADS = "C:/Users/maasa/.codex/foundation/context_offloads/research_x"
CODEX_PROJECT_PLANS = "C:/Users/maasa/.codex/foundation/project_plans/research_x"
PRESENTATION_PLAN = CODEX_PROJECT_PLANS + "/2026-06-24-presentation-generation-flow.md"


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def test_x_gpt_folder_has_thin_active_index_and_historical_markdown_notices() -> None:
    index = X_GPT_DIR / "README.md"
    text = index.read_text(encoding="utf-8")
    retired_docs = "docs/" + "pdg"
    retired_tool = "tools/" + "pdg" + "kit_canary"

    assert _line_count(index) <= 60
    assert "historical ChatGPT/GPT Pro control capture" in text
    assert "tools/wbs_viewer/projects/research-x-work-state.json" in text
    assert CODEX_CONTEXT_OFFLOADS + "/pointer-map.json" in text
    assert PRESENTATION_PLAN in text
    assert retired_docs not in text
    assert retired_tool not in text

    for path in X_GPT_DIR.glob("*.md"):
        if path.name == "README.md":
            continue
        head = path.read_text(encoding="utf-8")[:500]
        assert "Historical consultation capture. Active path:" in head, path.name
        assert "Retired diagram-tool notes inside are closed/reference-only" in head, path.name
        assert retired_docs not in head, path.name
        assert "Not evidence" in head, path.name
