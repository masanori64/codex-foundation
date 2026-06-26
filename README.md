# Codex Foundation

This repository is the local Codex foundation control plane. It owns reusable
Codex-wide governance, source intake, self-improvement staging, and the HOTL
implementation pipeline used by project repositories such as `research_x`.

Project repositories remain targets. They should keep only thin profiles,
bridges, workflow wrappers, generated control artifacts, and project-specific
source-of-truth documents.

## Current Surfaces

- `pipeline/`: reusable HOTL implementation pipeline engine, policies,
  schemas, GitHub workflow templates, dashboard rendering, Pages readback, and
  rollback manifests.
- `codex_improvement/`: proposal-only self-improvement signal and triage flow.
- `tests/`: local Codex foundation governance tests.
- `project_plans/`: durable plan records for foundation work.
- `codex-foundation-registry.toml`: machine-readable registry for foundation
  candidates and ownership.
- `vendor_sources.lock.md`: provenance lock for imported foundation sources.

`project_reviews/`, ZIP bundles, attachment mirrors, downloads, caches, and
runtime logs are intentionally ignored. They can contain task-local context and
are not part of the foundation source repo.

## Local Verification

Run from this directory:

```powershell
uv run ruff check .
uv run pytest tests pipeline\tests
```

The pipeline subset can also be checked directly:

```powershell
uv run ruff check pipeline\engine pipeline\tests
uv run pytest pipeline\tests
```

For the `research_x` bridge target:

```powershell
.\pipeline\scripts\codex-pipeline.ps1 validate --project C:\Users\maasa\research_x
.\pipeline\scripts\codex-pipeline.ps1 final-audit --project C:\Users\maasa\research_x
.\pipeline\scripts\codex-pipeline.ps1 validate-github-wrappers --project C:\Users\maasa\research_x
.\pipeline\scripts\codex-pipeline.ps1 validate-pages-workflows --project C:\Users\maasa\research_x
```

## Boundary

This repository must not contain secrets, PATs, deploy keys, provider keys,
private browser exports, raw ChatGPT downloads, or project evidence bundles.
Generated Codex control artifacts are not research evidence, citations, or
answer support.
