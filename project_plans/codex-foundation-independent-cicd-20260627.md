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
- [x] Confirmed remote `Codex Foundation CI` run for `cacf897` succeeded before
  this independent CI/CD pass.
- [x] Expand CI/CD workflow from pipeline-only checks to full foundation checks
  plus no-cost artifact packaging.
- [x] Add local scripts for foundation verification, artifact packaging, and
  rollback planning.
- [x] Update foundation docs and registry to reflect the independent CI/CD
  state and remove stale Phase 0/1 under-scope wording.
- [x] Add or update tests for package/rollback/subagent boundaries where needed.
- [x] Regenerate/validate `pipeline/FOUNDATION_MANIFEST.json`.
- [x] Add/validate repo-level `FOUNDATION_REPO_MANIFEST.json`.
- [x] Reproduced the `064fe17` CI failure locally: tests passed, but the repo
  manifest was stale for this active plan file after the final plan update.
- [x] Regenerated repo manifest after the plan repair and reran local
  verification successfully.
- [ ] Push the repair commit and confirm GitHub Actions success.

## Current Known State

- Branch: `main`.
- Remote: `origin https://github.com/masanori64/codex-foundation.git`.
- Current HEAD before this repair: `064fe17 Complete independent foundation CI/CD`.
- Existing workflow: `.github/workflows/foundation-ci.yml`.
- Existing repair gap: `FOUNDATION_REPO_MANIFEST.json` includes active
  `project_plans`, but `064fe17` committed a stale record for this file.

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

## Validation Notes

- `064fe17` remote run failed:
  `https://github.com/masanori64/codex-foundation/actions/runs/28264930656`.
- Local reproduction for `064fe17`: ruff passed, 116 tests passed, pipeline
  manifest passed, then repo manifest validation failed on
  `project_plans/codex-foundation-independent-cicd-20260627.md`.
- Repair action completed locally: this plan now records the failure,
  `FOUNDATION_REPO_MANIFEST.json` was regenerated, and
  `.\scripts\verify-foundation.ps1` passed with 116 tests plus both manifest
  validations.
- Remaining remote check: push the repair commit and confirm the new GitHub
  Actions run.
