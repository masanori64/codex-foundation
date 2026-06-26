# Codex HOTL Pipeline Phase 5 - GitHub Actions Thin Wrappers

## Status

Complete.

## Goal

Generate thin GitHub Actions wrappers from the Codex foundation while keeping
the generic pipeline engine out of `research_x`.

This phase adds artifact-only automation. It does not add GitHub API
collection, GitHub Pages, repository settings changes, preview/staging/
production deploy, secrets, provider calls, or rollback execution.

## Implemented

- Added foundation-owned GitHub workflow wrapper generation.
- Added foundation-owned wrapper validation.
- Added two dedicated workflow templates:
  - `codex-ci.template.yml`
  - `codex-dashboard.template.yml`
- Removed the stale combined dashboard wrapper template.
- Generated research_x workflow wrappers:
  - `.github/workflows/codex-ci.yml`
  - `.github/workflows/codex-dashboard.yml`
- Updated research_x profile and bridge capabilities:
  - `github_actions_wrappers: artifact_only`
  - `dashboard_artifact_cd: artifact_only`
- Regenerated dashboard/effective control artifacts with the new capability
  state.

## Boundary

- Workflows use `pull_request` and `workflow_dispatch`.
- Workflows do not use `pull_request_target`.
- Workflow permissions are `contents: read`.
- Dashboard output is uploaded as a workflow artifact only.
- No Pages deployment is configured.
- No secrets are referenced.
- No GitHub API write path exists.
- No Codex foundation engine code was copied into `research_x`.

## Verification

- `codex-pipeline validate --project C:\Users\maasa\research_x` passed.
- `codex-pipeline validate-github-wrappers --project C:\Users\maasa\research_x`
  passed.
- Foundation tests passed with 18 tests.
- Foundation ruff passed.
- `uv run ruff check src\research_x tests scripts` passed.
- `uv run pytest` passed with 343 tests.
- Local forbidden-pattern scan found no `pull_request_target`, Pages write
  permission, deployment write permission, secrets reference, GitHub API
  command, push trigger, or direct `.codex` runner dependency.

## Next Phase

Phase 6 can add preview artifact-only CD. It must stay artifact-only and must
not require Pages, external services, repository settings, secrets, providers,
or live deployment.
