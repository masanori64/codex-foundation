# Codex Foundation Independent CI/CD - 2026-06-27

Status: complete-source-state

This plan is closed as implementation state. The final GitHub Actions pass and
artifact readback for the plan-close commit are recorded in the Codex thread
result rather than written back into this file, so the plan does not create an
endless plan-update/manifest-update loop.

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
- GitHub CI uses a portable repo-owned verification set, while local operator
  verification can additionally run desktop integration canaries that depend on
  state outside this repository;
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
- [x] Reproduced the `c9c12b2` CI failure: portable tests passed, then repo
  manifest validation failed on LF-normalized `pointer-map.json`.
- [x] Normalized `context_offloads/research_x/pointer-map.json` to LF, updated
  the offline canary hash, regenerated repo manifest, and reran portable/local
  verification successfully.
- [x] Reproduced the `0be8724` CI failure: verification passed and package/rollback
  files were generated, but upload-artifact ignored hidden `.foundation-dist`.
- [x] Switched the CI artifact directory to non-hidden `foundation-dist`.
- [x] Pushed repair commit `22b4092` and confirmed GitHub Actions success:
  `https://github.com/masanori64/codex-foundation/actions/runs/28265396448`.
- [x] Plan-close boundary recorded: this file participates in
  `FOUNDATION_REPO_MANIFEST.json`, so the final plan-close commit must be
  verified by CI and recorded in the Codex thread result rather than causing an
  infinite plan-update/manifest-update loop.
- [x] Converted this active plan into closed implementation state; final remote
  readback for that closing commit is intentionally reported outside this file.

## Current Known State

- Branch: `main`.
- Remote: `origin https://github.com/masanori64/codex-foundation.git`.
- Current verified repair commit: `22b4092 Use visible foundation artifact directory`.
- Existing workflow: `.github/workflows/foundation-ci.yml`.
- Existing repair gap: GitHub checkout normalizes files to LF; local mixed
  line endings in `context_offloads/research_x/pointer-map.json` caused the
  repo manifest hash to differ remotely.

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
- `.github/workflows/foundation-ci.yml` now has `verify` and `package` jobs; the
  verify job uses `.\scripts\verify-foundation.ps1 -Portable`.
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
- CI-equivalent portable verification passed locally with 60 tests plus both
  manifest validations.
- `c9c12b2` remote run failed:
  `https://github.com/masanori64/codex-foundation/actions/runs/28265102859`.
- Repair action completed locally: `pointer-map.json` was normalized to LF,
  `offline_canary_registry.json` now points to the LF hash, repo manifest was
  regenerated, and both `.\scripts\verify-foundation.ps1 -Portable` and
  `.\scripts\verify-foundation.ps1` passed.
- `0be8724` remote run failed:
  `https://github.com/masanori64/codex-foundation/actions/runs/28265261884`.
- Repair action completed locally: workflow package/CD output now uses
  non-hidden `foundation-dist` so `actions/upload-artifact` can read it with
  default settings.
- `22b4092` remote run succeeded:
  `https://github.com/masanori64/codex-foundation/actions/runs/28265396448`.
- Final readback rule: GitHub Actions must pass for the final plan-close commit,
  but the result is recorded in the Codex final response instead of mutating this
  plan again.
