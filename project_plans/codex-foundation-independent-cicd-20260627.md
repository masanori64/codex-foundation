# Codex Foundation Independent CI/CD - 2026-06-27

Status: active

Objective: make `C:/Users/maasa/.codex/foundation` stand as an independent
Git/GitHub-managed Codex foundation control-plane repository, not merely a
helper package used by `research_x`.

Done means:
- push and pull request CI cover the foundation repository itself;
- CI verifies full foundation lint/tests, pipeline subset lint/tests, manifest
  freshness, workflow/template contracts, and package creation;
- CD is represented as a no-cost verified GitHub Actions artifact package for
  the foundation source, not as a paid cloud deploy;
- README, pipeline README, registry, and active plan language match the executed
  state rather than older Phase 0/1 or `research_x`-only wording;
- cross-project behavior is verified by synthetic fixture coverage and not by
  host-local `research_x` paths;
- subagent support has an explicit executable boundary: report contracts and
  dry-run validation are foundation-owned, while real worker spawning remains a
  Codex app/runtime capability outside this package unless a callable runtime is
  intentionally integrated;
- foundation rollback is documented and checkable as Git/artifact rollback, with
  destructive, provider, secrets, DB, and external-cloud rollback classes refused;
- local validation and GitHub Actions readback are recorded before completion.

Non-negotiable boundaries:
- no paid provider/API/quota, model runner, secrets, PAT/deploy key, DB
  migration, destructive action, or paid external cloud deployment;
- do not narrow completion back to `research_x` Static Pages CD;
- do not call a placeholder, fixture-only proof, or unsupported real subagent
  execution complete without naming the executable boundary and check.

## Progress

- [x] Confirmed foundation repo exists independently at
  `https://github.com/masanori64/codex-foundation.git`.
- [x] Confirmed `main` is synced with `origin/main`.
- [x] Confirmed latest remote `Codex Foundation CI` run for `d8d8554` succeeded.
- [x] Expand CI/CD workflow from pipeline-only checks to full foundation checks
  plus no-cost artifact packaging.
- [x] Add local scripts for foundation verification, artifact packaging, and
  rollback planning.
- [x] Update foundation docs and registry to reflect the independent CI/CD
  state and remove stale Phase 0/1 under-scope wording.
- [x] Add or update tests for package/rollback/subagent boundaries where needed.
- [x] Regenerate/validate `pipeline/FOUNDATION_MANIFEST.json`.
- [x] Add/validate repo-level `FOUNDATION_REPO_MANIFEST.json`.
- [x] Run local verification.
- [ ] Commit, push, and confirm GitHub Actions success.

## Current Known State

- Branch: `main`.
- Remote: `origin https://github.com/masanori64/codex-foundation.git`.
- Current HEAD before this work: `d8d8554 Stabilize foundation manifest line endings`.
- Existing workflow: `.github/workflows/foundation-ci.yml`.
- Existing workflow gap: checks only `pipeline/engine` and `pipeline/tests`, and
  has no package artifact, manifest freshness check, root governance tests, or
  explicit foundation rollback/package boundary.

## Implemented This Pass

- `scripts/verify-foundation.ps1` now runs full repo ruff, full foundation tests,
  pipeline manifest validation, repo manifest validation, and CI/CD surface
  validation. It explicitly fails on non-zero external command exit codes.
- `scripts/package-foundation.ps1` creates a no-cost GitHub Actions artifact
  package and package manifest.
- `scripts/foundation-rollback-plan.ps1` creates a plan-only Git/artifact
  rollback manifest and refuses destructive/provider/secrets/DB/external-cloud
  rollback classes.
- `validate-subagent-report` now validates sanitized read-only subagent summary
  reports without spawning workers, starting model runners, committing, pushing,
  deploying, or executing rollback.
- `FOUNDATION_REPO_MANIFEST.json` covers active root source, CI, scripts, tests,
  registry, and pipeline surfaces.
- `.github/workflows/foundation-ci.yml` now has `verify` and `package` jobs.
- `tests/test_foundation_cicd_contract.py` guards the CI/CD, package, rollback,
  no-provider, no-secret, and plan-only boundaries.

## Local Validation

- `.\scripts\verify-foundation.ps1` passed with 116 tests.
- Package script generated `.foundation-dist/codex-foundation-cacf897.zip` and a
  package manifest.
- Rollback plan script generated `.foundation-dist/foundation-rollback-plan.json`.
- Direct pipeline manifest import check passed after documenting the required
  `PYTHONPATH` setup.
