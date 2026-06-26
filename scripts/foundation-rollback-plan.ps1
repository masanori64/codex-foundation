param(
  [string]$TargetRef = "HEAD~1",
  [string]$OutputPath = ".foundation-dist/foundation-rollback-plan.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $Root
try {
  $TargetCommit = (git rev-parse --verify "$TargetRef^{commit}").Trim()
  $CurrentCommit = (git rev-parse HEAD).Trim()
  $Status = (git status --porcelain)
  $OutputFullPath = Join-Path $Root $OutputPath
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputFullPath) | Out-Null

  $Plan = [ordered]@{
    schema_version = 1
    artifact_kind = "codex_foundation_rollback_plan"
    control_artifact = $true
    not_project_evidence = $true
    not_research_evidence = $true
    not_citation = $true
    not_answer_support = $true
    generated_by = "codex-foundation-ci"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    rollback_class = "git_artifact_foundation_source"
    rollback_executed = $false
    current_commit = $CurrentCommit
    target_ref = $TargetRef
    target_commit = $TargetCommit
    worktree_clean = ([string]::IsNullOrWhiteSpace(($Status -join "`n")))
    safe_execution_boundary = "plan_only_until_human_or_goal_explicitly_requests_revert_commit"
    recommended_no_destructive_path = @(
      "inspect target commit and package manifest",
      "create a new branch from current main",
      "restore by a new revert/fix-forward commit instead of rewriting public history",
      "run scripts/verify-foundation.ps1",
      "push and require Codex Foundation CI success"
    )
    refused_rollback_classes = @(
      "destructive_action",
      "git_history_rewrite",
      "secret_restore",
      "provider_api_quota",
      "db_restore",
      "external_cloud_deploy",
      "project_evidence_write"
    )
    side_effects = [ordered]@{
      provider_api_calls = $false
      paid_usage_detected = $false
      secrets_used = $false
      db_migration_executed = $false
      external_cloud_used = $false
      destructive_action = $false
    }
  }

  $Plan | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputFullPath -Encoding UTF8
  Write-Host "foundation rollback plan: $OutputFullPath"
}
finally {
  Pop-Location
}
