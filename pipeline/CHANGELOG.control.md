# Codex HOTL Pipeline Control Changelog

This changelog records control-plane changes for the local Codex foundation
pipeline. It is not project evidence, citation support, or answer support.

## 0.1.0-local

- Created local-first HOTL pipeline skeleton.
- Added project profile/bridge validation, dashboard state, Mermaid, deploy
  manifest, rollback manifest, and Phase 1 gates.
- Added Phase 2 hardening manifest/audit plan.
- Added Phase 4 GitHub collection state in disabled/local-only mode.
- Added Phase 5 GitHub Actions artifact-only wrapper generation and validation.
- Added Phase 6 preview manifest and artifact-only preview workflow generation.
- Added Phase 7 staging safe-static dry-run manifest generation.
- Added Phase 8 production planning manifest generation without execution.
- Added Phase 9 rollback dry-run and static-artifact drill manifest details.
- Added Phase 10 foundation-owned subagent policy generation without spawning.
- Added Phase 11 control-artifact audit manifests to keep dashboard, Mermaid,
  ChatGPT, WBS, GitHub, and subagent control outputs out of evidence paths.
- Added Phase 12 dummy second-project validation and removed project-id-specific
  engine boundary checks.
- Added Phase 13 no-cost smoke guard for local/read-only/artifact-only work,
  plus blocked billing-sensitive lanes.
- Added Phase 14 unauthenticated GitHub REST read collection for repo, PR,
  workflow run, artifact, and rate-limit metadata, without token or write
  operations.
- Added Phase 15 artifact-only workflow audit without GitHub Actions dispatch.
- Added Phase 16 subagent runtime dry-run without spawning workers or starting
  model runners.
- Added Phase 17 push-triggered artifact-only remote smoke workflow and
  workflow-smoke control artifacts.
- Added Phase 18 E2E completion manifest for the no-cost artifact-only
  pipeline loop.
