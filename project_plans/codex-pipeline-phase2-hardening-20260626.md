# Codex Pipeline Phase 2 Hardening Plan

Status: complete
Owner: Codex foundation
Project bridge target: C:/Users/maasa/research_x
Started: 2026-06-26

## Goal

Harden Phase 0/1 before any GitHub/CD expansion. This is limited to foundation
integrity, reproducible invocation, disabled capability gates, machine-readable
not-evidence markers, and GitHub Actions security baseline.

## Sources

- GPT Pro consultation:
  C:/Users/maasa/.codex/foundation/project_reviews/research_x_chatgpt_control/codex-hotl-pipeline-next-plan-20260626/gpt-pro-response.md
- Codex foundation pipeline:
  C:/Users/maasa/.codex/foundation/pipeline
- research_x bridge artifacts:
  C:/Users/maasa/research_x/.codex-project
  C:/Users/maasa/research_x/docs/control/codex

## Open Items

- [x] Add FOUNDATION_MANIFEST.json writer and audit ledger.
- [x] Make wrappers reproducible from arbitrary cwd.
- [x] Add capability flags / kill switches, disabled by default.
- [x] Enforce not_research_evidence / not_answer_support markers.
- [x] Expand GitHub security baseline before workflow wrappers.
- [x] Regenerate research_x bridge/control artifacts.
- [x] Validate foundation and research_x.
- [x] Commit/push only research_x generated bridge/control changes.

## Gates

Do not use provider/API/quota, secrets, installs, MCP/plugin/hook changes,
destructive actions, DB migration, GitHub Pages, repository settings,
production CD, or rollback execution.

## Current Next Action

Phase 2 Immediate Fix bundle is complete. Next boundary is Phase 3 project
bridge contract stabilization.

research_x commit:

- c27a414 Harden Codex HOTL bridge artifacts

## Validation

- Foundation tests: `uv run pytest C:/Users/maasa/.codex/foundation/pipeline/tests` -> 13 passed.
- Foundation lint: `uv run ruff check C:/Users/maasa/.codex/foundation/pipeline/engine C:/Users/maasa/.codex/foundation/pipeline/tests` -> passed.
- `codex-pipeline.ps1 validate` passed from `.codex`, `research_x`, and temp cwd.
- `codex-pipeline.ps1 render-dashboard` and `render-mermaid` passed from `.codex`, `research_x`, and temp cwd.
- `research_x` lint: `uv run ruff check src/research_x tests scripts` -> passed.
- `research_x` tests: `uv run pytest` -> 343 passed.
