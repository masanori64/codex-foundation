# Codex HOTL Pipeline Phase 6 - Preview Artifact Only

## Status

Complete.

## Goal

Add preview CD as artifact-only output. This phase creates reviewable preview
artifacts but does not publish a live URL or mutate any staging/production
surface.

## Implemented

- Added a foundation-owned preview manifest builder.
- Added preview manifest generation into dashboard state and project generated
  outputs.
- Added `codex-preview.template.yml`.
- Generated `research_x/.github/workflows/codex-preview.yml`.
- Updated `codex-ci.yml` to validate preview manifest boundaries.
- Updated `codex-dashboard.yml` to include the preview manifest in dashboard
  artifacts.
- Updated research_x profile and bridge:
  - `preview_cd: artifact_only`

## Boundary

- Preview output is a GitHub Actions artifact only.
- No GitHub Pages.
- No live preview URL.
- No secrets.
- No provider/API/quota calls.
- No repository settings or environment creation.
- No staging or production deployment.
- No rollback execution.
- No generic pipeline engine code in `research_x`.

## Verification

- `codex-pipeline validate --project C:\Users\maasa\research_x` passed.
- `codex-pipeline validate-github-wrappers --project C:\Users\maasa\research_x`
  passed.
- Foundation tests passed with 18 tests.
- Foundation ruff passed.
- Forbidden-pattern scan found no `pull_request_target`, Pages write
  permission, deployment write permission, secrets reference, GitHub API
  command, push trigger, or direct `.codex` runner dependency.
- `uv run ruff check src\research_x tests scripts` passed.
- `uv run pytest` passed with 343 tests.

## Next Phase

Phase 7 may design staging safe static CD, but actual staging execution remains
gated if it needs repository settings, environments, secrets, Pages, or external
services.
