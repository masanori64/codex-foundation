# Codex Foundation HOTL Pipeline

This package owns the reusable Codex programming-work pipeline. Project repositories are targets, not owners, of the generic pipeline engine.

The pipeline is local-first in Phase 0/1:

- read a project `.codex-project/profile.yml`;
- read a project `.codex-project/bridge.yml`;
- enforce HOTL gates before external or irreversible actions;
- generate dashboard state, HTML, Mermaid, deploy manifest, and rollback manifest as control artifacts;
- never treat generated control artifacts as research evidence, citations, or answer support.

`research_x` may contain a profile, bridge, thin wrappers, and generated artifacts. It must not own the generic dashboard engine, GitHub state collector, rollback planner, or subagent definitions.

## Phase 0/1 Boundary

Implemented:

- profile and bridge validation;
- local-only gate checks;
- local dashboard and Mermaid generation;
- deploy and rollback manifest planning without execution;
- evidence-boundary checks for generated control artifacts.
- GitHub Actions wrapper generation for artifact-only dashboard upload.
- Preview artifact generation without Pages, live deployment, secrets, or
  repository settings changes.
- Staging safe-static dry-run manifests without environment creation or live
  staging deployment.
- Production planning manifests without production deployment.
- Rollback dry-run manifests for safe static artifacts only, with destructive,
  DB, provider, and secrets rollback classes refused by default.
- Subagent governance manifests with read-only roles, sanitized summaries, and
  raw project log storage disabled.
- Control-artifact audit manifests that reject overlap between generated
  control outputs and configured evidence/citation paths.
- Cross-project dummy validation proving the foundation can render a second
  project from profile/bridge only.
- No-cost smoke guard that separates local/read-only/artifact-only checks from
  billing-sensitive or state-mutating lanes.
- Unauthenticated GitHub REST read collection for repo, PR, workflow run,
  artifact, and rate-limit metadata, without tokens or writes.
- Artifact-only GitHub Actions wrapper audit without workflow dispatch.
- Push-triggered remote artifact-only smoke workflow for public repositories,
  without Pages, deployments, repository settings, secrets, or live deploys.
- E2E completion manifest for the artifact-only no-cost pipeline loop.
- Subagent runtime dry-run without spawning workers, model runners, or raw
  project log storage.

Not implemented in Phase 0/1:

- provider/API/quota calls;
- GitHub API write or authenticated collection;
- GitHub Pages enablement;
- staging or production deploy;
- rollback execution;
- secrets or credentials handling;
- installs, model downloads, MCP/plugin/hook enablement;
- custom subagent runtime configuration.

## Commands

Use the wrapper scripts or run the module with `PYTHONPATH` pointing at `engine`.

```powershell
C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1 validate --project C:\Users\maasa\research_x
C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1 render-dashboard --project C:\Users\maasa\research_x
C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1 render-mermaid --project C:\Users\maasa\research_x
C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1 check-cost --project C:\Users\maasa\research_x
C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1 collect-github-read --project C:\Users\maasa\research_x
C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1 audit-workflow-artifacts --project C:\Users\maasa\research_x
C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1 audit-workflow-smoke --project C:\Users\maasa\research_x
C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1 subagent-dry-run --project C:\Users\maasa\research_x
C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1 generate-github-wrappers --project C:\Users\maasa\research_x
C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1 validate-github-wrappers --project C:\Users\maasa\research_x
```
