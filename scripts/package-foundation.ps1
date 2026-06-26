param(
  [string]$OutputDir = ".foundation-dist"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $Root
try {
  $Commit = (git rev-parse HEAD).Trim()
  $Short = (git rev-parse --short HEAD).Trim()
  $OutputPath = Join-Path $Root $OutputDir
  New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null

  $Archive = Join-Path $OutputPath "codex-foundation-$Short.zip"
  if (Test-Path -LiteralPath $Archive) {
    Remove-Item -LiteralPath $Archive -Force
  }

  git archive --format=zip --output $Archive HEAD
  $ArchiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Archive).Hash.ToLowerInvariant()
  $Manifest = [ordered]@{
    schema_version = 1
    artifact_kind = "codex_foundation_package"
    control_artifact = $true
    not_project_evidence = $true
    not_research_evidence = $true
    not_citation = $true
    not_answer_support = $true
    generated_by = "codex-foundation-ci"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    repository = "masanori64/codex-foundation"
    commit = $Commit
    archive = [ordered]@{
      path = $Archive
      sha256 = $ArchiveHash
    }
    cd_mode = "github_actions_artifact"
    paid_usage_detected = $false
    provider_api_calls = $false
    secrets_used = $false
    external_cloud_used = $false
    db_migration_executed = $false
    destructive_action = $false
  }

  $ManifestPath = Join-Path $OutputPath "codex-foundation-package-manifest.json"
  $Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8

  Write-Host "foundation package: $Archive"
  Write-Host "foundation package manifest: $ManifestPath"
}
finally {
  Pop-Location
}
