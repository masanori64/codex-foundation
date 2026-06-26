# Codex HOTL Pipeline Phase 9 - Rollback Dry-Run

Superseded: this is a historical phase record. The active source of truth is
`codex-static-pages-cd-execution-20260626.md`, where rollback is now implemented
as executed safe static GitHub Pages rollback (`rollback_execution:
safe_static_pages_enabled`), not as `rollback_execution: dry_run_only`.

## Status

Superseded by executed safe static Pages rollback.

## Goal

Add rollback dry-run and drill for safe static artifacts only.

## Implemented

- Enhanced the foundation rollback planner.
- Rollback manifest now records:
  - `scope: safe_static_artifacts_only`
  - simulated static target selection
  - simulated drill state
  - refused destructive/DB/provider/secrets rollback classes
  - no file mutation and no rollback execution
- Updated workflow control-artifact validation to check rollback boundaries.
- Updated research_x profile and bridge:
  - `rollback_execution: dry_run_only`

## Boundary

- Rollback is dry-run only.
- No file mutation.
- No production mutation.
- No DB migration or DB restore.
- No provider/API/quota calls.
- No secrets.
- No destructive action.
- No repository settings change.
- No real rollback execution.

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

Phase 10 may add Codex foundation-owned subagent governance with project
allowlist and sanitized summaries.
