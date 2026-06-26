# Codex HOTL Pipeline Active Plan

Status: completed_superseded_by_static_pages_cd

Objective: implement the Codex-foundation-owned HOTL programming pipeline Phase 0/1. The generic engine lives under `C:/Users/maasa/.codex/foundation/pipeline`; `research_x` only receives a project profile, bridge, and generated control artifacts.

Supersession note:
- This Phase 0/1 plan was the initial no-CD/local-control slice.
- The user later clarified that every no-cost action was permitted, including free GitHub Actions and GitHub Pages. The active completion target moved to full free static Pages CD, tracked in `C:/Users/maasa/.codex/foundation/project_plans/codex-static-pages-cd-execution-20260626.md`.
- Do not use this file's old "no GitHub API/CD, production deploy, or rollback execution is used" line as the current completion boundary.
- Current final state is `complete_static_pages_cd_no_cost`, with safe static Pages rollback executed and paid/provider/secret/DB/destructive paths outside the completed free-CD pipeline.

Current source of truth: `C:/Users/maasa/.codex/foundation/project_reviews/research_x_chatgpt_control/codex-dev-flow-pipeline-20260626/codex-foundation-hotl-pipeline-replan.md`.

Done requires:
- `codex-pipeline validate --project C:/Users/maasa/research_x` succeeds.
- `codex-pipeline render-dashboard --project C:/Users/maasa/research_x` writes control artifacts.
- `codex-pipeline render-mermaid --project C:/Users/maasa/research_x` writes Mermaid sources.
- Generated dashboard says `control artifact / not evidence / not citation`.
- No provider/API/quota, secrets, install, MCP/plugin/hook enablement, destructive action, GitHub API/CD, production deploy, or rollback execution is used.
- Existing `research_x` draft dashboard/pipeline files are not promoted as source of truth.

Progress:
- 2026-06-26: Goal activated and implementation started from the GPT Pro boundary replan.
- 2026-06-26: Added `C:/Users/maasa/.codex/foundation/pipeline` Phase 0/1 engine, schemas, policies, CLI wrappers, and tests.
- 2026-06-26: Added `research_x/.codex-project/profile.yml`, `bridge.yml`, and generated `docs/control/codex/dashboard` artifacts.
- 2026-06-26: Removed the earlier untracked research_x draft pipeline/dashboard implementation files from `.pipeline`, `.github/workflows/project-dashboard.yml`, `scripts/collect_github_state.py`, `scripts/render_dashboard.py`, `src/research_x/project_dashboard.py`, and `tests/test_project_dashboard.py`.
- 2026-06-26: Validation passed:
  - `uv run ruff check C:\Users\maasa\.codex\foundation\pipeline\engine C:\Users\maasa\.codex\foundation\pipeline\tests`
  - `uv run pytest C:\Users\maasa\.codex\foundation\pipeline\tests`
  - `PYTHONPATH=C:\Users\maasa\.codex\foundation;C:\Users\maasa\.codex\foundation\pipeline\engine uv run pytest C:\Users\maasa\.codex\foundation\tests C:\Users\maasa\.codex\foundation\pipeline\tests`
  - `uv run ruff check src\research_x tests scripts`
  - `uv run pytest`
  - `codex-pipeline validate/render-dashboard/render-mermaid --project C:\Users\maasa\research_x`

Final state: Phase 0/1 was completed and then superseded by the full Static Pages CD completion plan. The latest pushed project commits are `7ca98b2 Clarify Codex Pages completion boundaries` and `61bf90f Align Pages workflow foundation hash`; `.codex` foundation files are local Codex foundation state and not in a git repository.
