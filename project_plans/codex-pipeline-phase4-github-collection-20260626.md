# Codex HOTL Pipeline Phase 4 - GitHub Collection Gate

## Status

Complete.

## Goal

Add a GitHub collection surface to the Codex foundation pipeline without using
real GitHub credentials, live GitHub API calls, write operations, repository
settings changes, GitHub Pages, production CD, or rollback execution.

This phase is a control-plane capability only. It is not project evidence, not a
citation source, and not answer support.

## Implemented

- Added a foundation-owned GitHub collection model.
- Default project behavior is disabled/local-only.
- Read-only method names are explicit.
- Mutation method names are explicitly forbidden.
- No mutation methods are exposed as available.
- Generated dashboard state now includes `github_collection`.
- Generated research_x control artifacts include:
  - `.codex-project/generated/effective-github-collection.json`
  - `docs/control/codex/dashboard/data/github-collection.json`
- Generated state records:
  - `collection_mode: disabled`
  - `api_calls_executed: false`
  - `token_used: false`
  - `write_operations_available: false`
  - `mutation_methods_available: []`
- Validation checks require the generated GitHub collection artifacts to exist
  and preserve the no-API/no-write boundary.

## Not Implemented

- No GitHub token usage.
- No GitHub API request.
- No GitHub write API.
- No active GitHub Actions workflow.
- No repository settings update.
- No GitHub Pages enablement.
- No production CD.
- No rollback execution.

## Verification

- `C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1 validate --project C:\Users\maasa\research_x`
  passed.
- `uv run pytest C:\Users\maasa\.codex\foundation\pipeline\tests` passed with
  16 tests.
- `uv run ruff check C:\Users\maasa\.codex\foundation\pipeline\engine C:\Users\maasa\.codex\foundation\pipeline\tests`
  passed.
- `uv run ruff check src\research_x tests scripts` passed.
- `uv run pytest` passed with 343 tests.
- Generated artifacts were checked for `collection_mode`,
  `api_calls_executed`, `token_used`, `write_operations_available`, and
  `mutation_methods_available`.

## Next Phase

Phase 5 should add thin GitHub Actions wrapper templates only after keeping the
same boundary: wrappers can call the foundation pipeline, but must not move
generic pipeline logic into research_x, enable CD, use secrets, call providers,
or mutate repository settings.
