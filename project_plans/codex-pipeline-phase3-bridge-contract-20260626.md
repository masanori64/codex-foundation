# Codex Pipeline Phase 3 Bridge Contract Plan

Status: complete
Owner: Codex foundation
Project bridge target: C:/Users/maasa/research_x
Started: 2026-06-26

## Goal

Stabilize the project profile/bridge contract without moving generic pipeline
logic into research_x.

## Completed

- Added `schema/project-bridge.schema.json`.
- Updated profile schema to require machine-readable not-evidence fields.
- Made profile and bridge loaders read foundation schema files.
- Added `effective-profile.yml` generation.
- Added validator checks that known generic pipeline draft files do not exist
  in research_x.
- Regenerated research_x control artifacts.
- Committed/pushed research_x generated bridge/control artifact update.

## Validation

- `codex-pipeline.ps1 validate --project C:/Users/maasa/research_x` -> passed.
- Foundation tests: `uv run pytest C:/Users/maasa/.codex/foundation/pipeline/tests` -> 14 passed.
- Foundation lint: `uv run ruff check C:/Users/maasa/.codex/foundation/pipeline/engine C:/Users/maasa/.codex/foundation/pipeline/tests` -> passed.
- `research_x` lint: `uv run ruff check src/research_x tests scripts` -> passed.
- `research_x` tests: `uv run pytest` -> 343 passed.

## Commit

- research_x: 9ba34db Stabilize Codex project bridge artifacts

## Next Boundary

Phase 4: gated GitHub read-only collection in Codex foundation. Keep default
mode disabled/mock and do not use tokens or GitHub mutation without an explicit
gate.
