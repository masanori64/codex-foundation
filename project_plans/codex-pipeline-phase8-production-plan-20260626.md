# Codex HOTL Pipeline Phase 8 - Production Planning

Superseded: this is a historical phase record. The active source of truth is
`codex-static-pages-cd-execution-20260626.md`, where production is now
implemented as free GitHub Pages static CD (`production_cd:
static_pages_enabled`), not as `production_cd: gated_plan`.

## Status

Superseded by static Pages CD completion.

## Goal

Add production CD planning without executing any production deploy.

## Implemented

- Added a foundation-owned production manifest builder.
- Generated production manifests into:
  - `.codex-project/generated/effective-production-manifest.json`
  - `docs/control/codex/dashboard/data/production-manifest.json`
- Added production manifest checks to the GitHub control-artifact CI template.
- Included production manifest in dashboard and preview artifact workflows.
- Updated research_x profile and bridge:
  - `production_cd: gated_plan`

## Boundary

- Production execution is disabled.
- No production deploy.
- No live production URL.
- No GitHub Pages.
- No secrets.
- No provider/API/quota calls.
- No repository settings change.
- No environment creation.
- No rollback execution.

## Verification

- `codex-pipeline validate --project C:\Users\maasa\research_x` passed.
- `codex-pipeline validate-github-wrappers --project C:\Users\maasa\research_x`
  passed.
- Foundation tests passed.
- Foundation ruff passed.
- Forbidden-pattern scan found no `pull_request_target`, Pages write
  permission, deployment write permission, secrets reference, GitHub API
  command, push trigger, or direct `.codex` runner dependency.
- `uv run ruff check src\research_x tests scripts` passed.
- `uv run pytest` passed with 343 tests.

## Next Phase

Phase 9 may add rollback dry-run and drill for safe static artifacts only.
