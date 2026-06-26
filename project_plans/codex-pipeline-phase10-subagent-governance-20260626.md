# Codex HOTL Pipeline Phase 10 - Subagent Governance

## Status

Complete.

## Goal

Add Codex foundation-owned subagent governance without spawning subagents.

## Implemented

- Added a foundation-owned subagent policy builder.
- Generated subagent policy artifacts into:
  - `.codex-project/generated/effective-subagent-policy.json`
  - `docs/control/codex/dashboard/data/subagent-policy.json`
- Dashboard subagent state now references the generated policy.
- Added workflow validation for:
  - read-only lifecycle
  - no default spawning
  - no raw logs in `research_x`
  - forbidden commit/push/deploy/GitHub mutation/provider/secret/evidence actions

## Boundary

- No subagents were spawned.
- Subagents are not allowed to commit, push, deploy, mutate GitHub, access
  secrets, call providers, create evidence, or execute rollback.
- Raw subagent logs stay out of `research_x`.
- Project receives sanitized control summaries only.

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

Phase 11 may add an automated audit that generated control artifacts cannot
become research_x evidence or citation material.
