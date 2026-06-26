# Codex Foundation HOTL Pipeline

This package owns the reusable Codex programming-work pipeline. Project repositories are targets, not owners, of the generic pipeline engine.

The pipeline is foundation-owned and project-targeted:

- read a project `.codex-project/profile.yml`;
- read a project `.codex-project/bridge.yml`;
- enforce HOTL gates before external or irreversible actions;
- generate dashboard state, HTML, Mermaid, deploy manifest, and rollback manifest as control artifacts;
- never treat generated control artifacts as research evidence, citations, or answer support.

Target projects may contain a profile, bridge, thin wrappers, and generated artifacts. They must not own the generic dashboard engine, GitHub state collector, rollback planner, or subagent definitions.

## Implemented Foundation Pipeline

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
- E2E completion manifest for the no-cost static Pages CD pipeline loop.
- Subagent runtime dry-run without spawning workers, model runners, or raw
  project log storage.
- Public-CI fixture coverage that runs against a temporary synthetic project
  instead of creating or mutating a host-local target project.

Outside the completed free static Pages CD pipeline and foundation package CD:

- provider/API/quota calls;
- secrets or credentials handling;
- installs, model downloads, MCP/plugin/hook enablement;
- destructive actions, DB migration, or external cloud deployment;
- custom subagent runtime configuration;
- authenticated host-setting inspection except explicit local verification
  commands such as `gh api` outside the generated pipeline.

The foundation repository has its own CI/CD outside target projects. That path
verifies the full foundation repo and publishes a no-cost source package as a
GitHub Actions artifact. Target project Pages CD, such as the `research_x`
dashboard/preview/staging/production lanes, remains a use of this foundation
pipeline rather than the foundation package CD itself.

## Commands

Use the wrapper scripts or run the module with `PYTHONPATH` pointing at `engine`.
Set `$PROJECT` to a target repository that contains `.codex-project/profile.yml`
and `.codex-project/bridge.yml`.

```powershell
$PIPELINE = "C:\Users\maasa\.codex\foundation\pipeline\scripts\codex-pipeline.ps1"
$PROJECT = "C:\path\to\target-project"

& $PIPELINE validate --project $PROJECT
& $PIPELINE render-dashboard --project $PROJECT
& $PIPELINE render-mermaid --project $PROJECT
& $PIPELINE check-cost --project $PROJECT
& $PIPELINE collect-github-read --project $PROJECT
& $PIPELINE audit-workflow-artifacts --project $PROJECT
& $PIPELINE audit-workflow-smoke --project $PROJECT
& $PIPELINE subagent-dry-run --project $PROJECT
& $PIPELINE validate-subagent-report --project $PROJECT --report C:\path\to\subagent-report.json
& $PIPELINE generate-github-wrappers --project $PROJECT
& $PIPELINE validate-github-wrappers --project $PROJECT
& $PIPELINE generate-pages-workflows --project $PROJECT
& $PIPELINE validate-pages-workflows --project $PROJECT
& $PIPELINE final-audit --project $PROJECT
```
