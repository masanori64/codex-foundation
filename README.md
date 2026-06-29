# Codex Foundation

This repository is the local Codex foundation control plane. It owns reusable
Codex-wide governance, source intake, self-improvement staging, and the HOTL
implementation pipeline used by project repositories such as `research_x`.

Project repositories remain targets. They should keep only thin profiles,
bridges, workflow wrappers, generated control artifacts, and project-specific
source-of-truth documents.

## Current Surfaces

- `.github/workflows/foundation-ci.yml`: independent GitHub CI/CD for the
  foundation repository. Pushes and pull requests verify the full foundation
  repo, validate the pipeline manifest, then publish a no-cost source package as
  a GitHub Actions artifact.
- `FOUNDATION_REPO_MANIFEST.json`: repo-level freshness manifest covering the
  active source, CI, scripts, tests, registry, and pipeline package.
- `scripts/`: local mirrors of the CI/CD path: full verification, foundation
  artifact packaging, and plan-only rollback manifests.
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
.\scripts\verify-foundation.ps1
```

GitHub CI uses the portable repo-owned suite:

```powershell
.\scripts\verify-foundation.ps1 -Portable
```

The default local command also runs desktop integration canaries that depend on
local Codex control-plane state outside this repository, such as route memory,
installed Skills, and the checked-out `research_x` project. The portable suite
is the independent GitHub contract; the default suite is the broader local
operator contract.

The main direct commands are:

```powershell
$env:PYTHONPATH = "$PWD\pipeline\engine;$env:PYTHONPATH"
uv run ruff check codex_improvement pipeline scripts tests offline_canaries.py skill_audit.py skill_factory.py
uv run pytest tests pipeline\tests
uv run python -c "from codex_pipeline.foundation import validate_foundation_manifest; errors = validate_foundation_manifest(); print(errors); raise SystemExit(1 if errors else 0)"
uv run python scripts\write-foundation-repo-manifest.py --check
```

The pipeline subset can still be checked directly:

```powershell
uv run ruff check pipeline\engine pipeline\tests
uv run pytest pipeline\tests
```

## Foundation CI/CD

This repository is not deployed to a paid cloud service. Its CD output is a
verified GitHub Actions artifact package of the foundation source at the checked
commit:

```powershell
.\scripts\package-foundation.ps1
```

The package manifest records the commit, archive hash, and no-cost boundary:
no paid provider/API calls, no secrets, no DB migration, no destructive action,
and no external cloud deployment.

Rollback is Git/artifact based. The default rollback command only writes a
plan-only manifest and refuses destructive rollback classes:

```powershell
.\scripts\foundation-rollback-plan.ps1 -TargetRef HEAD~1
```

Actual recovery should be a new revert or fix-forward commit followed by
`.\scripts\verify-foundation.ps1` and a successful `Codex Foundation CI` run.
Do not rewrite public history or restore secrets, databases, provider state, or
external cloud resources through this foundation path.

For any target project with `.codex-project/profile.yml` and
`.codex-project/bridge.yml`, set `$PROJECT`:

```powershell
$PROJECT = "C:\path\to\target-project"
.\pipeline\scripts\codex-pipeline.ps1 validate --project $PROJECT
.\pipeline\scripts\codex-pipeline.ps1 final-audit --project $PROJECT
.\pipeline\scripts\codex-pipeline.ps1 validate-github-wrappers --project $PROJECT
.\pipeline\scripts\codex-pipeline.ps1 validate-pages-workflows --project $PROJECT
```

## Boundary

This repository must not contain secrets, PATs, deploy keys, provider keys,
private browser exports, raw ChatGPT downloads, or project evidence bundles.
Generated Codex control artifacts are not research evidence, citations, or
answer support.

Real Codex subagent spawning is a Codex app/runtime capability, not a Python
package feature in this repository. The foundation owns the subagent policy,
report schema, and no-cost dry-run validation boundary. A future runtime adapter
must keep worker logs out of project evidence, keep commit/push/deploy decisions
with the parent, and pass the same provider/secrets/destructive-action gates.
