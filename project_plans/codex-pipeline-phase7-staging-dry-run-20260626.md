# Codex HOTL Pipeline Phase 7 - Staging Dry-Run Plan

Superseded: this is a historical phase record. The active source of truth is
`codex-static-pages-cd-execution-20260626.md`, where staging is now implemented
as free GitHub Pages static CD (`staging_cd: static_pages_lane_enabled`), not as
`staging_cd: gated_plan`.

## Status

Superseded by static Pages CD completion.

## Goal

Design staging safe static CD as a gated dry-run/control surface. This phase
does not create a staging environment and does not deploy to a live staging URL.

## Implemented

- Added a foundation-owned staging manifest builder.
- Generated staging manifests into:
  - `.codex-project/generated/effective-staging-manifest.json`
  - `docs/control/codex/dashboard/data/staging-manifest.json`
- Added staging manifest checks to the GitHub control-artifact CI template.
- Included staging manifest in dashboard/preview artifact workflows.
- Updated research_x profile and bridge:
  - `staging_cd: gated_plan`

## Boundary

- Staging is dry-run only.
- No environment creation.
- No GitHub Pages.
- No live staging URL.
- No secrets.
- No provider/API/quota calls.
- No repository settings change.
- No staging or production deployment.
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

Phase 8 may add production CD planning, but production execution remains
blocked unless explicit production gates are satisfied.
