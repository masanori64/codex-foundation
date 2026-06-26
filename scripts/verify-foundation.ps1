param(
  [switch]$Portable
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Checked {
  param(
    [Parameter(Mandatory = $true)]
    [scriptblock]$Command,
    [Parameter(Mandatory = $true)]
    [string]$Name
  )

  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Name failed with exit code $LASTEXITCODE"
  }
}

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $Root
try {
  $EnginePath = Join-Path $Root "pipeline\engine"
  if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
    $env:PYTHONPATH = $EnginePath
  }
  else {
    $env:PYTHONPATH = "$EnginePath;$env:PYTHONPATH"
  }

  $PytestTargets = if ($Portable) {
    @(
      "tests/test_codex_improvement.py",
      "tests/test_foundation_cicd_contract.py",
      "tests/test_overimplementation_guard.py",
      "tests/test_skill_lifecycle_input.py",
      "pipeline\tests"
    )
  }
  else {
    @("tests", "pipeline\tests")
  }

  Invoke-Checked -Name "ruff" -Command { uv run ruff check . }
  Invoke-Checked -Name "pytest" -Command { uv run pytest @PytestTargets }
  Invoke-Checked -Name "pipeline manifest validation" -Command { uv run python -c "from codex_pipeline.foundation import validate_foundation_manifest; errors = validate_foundation_manifest(); print('foundation manifest ok' if not errors else '\n'.join(errors)); raise SystemExit(1 if errors else 0)" }
  Invoke-Checked -Name "repo manifest validation" -Command { uv run python scripts\write-foundation-repo-manifest.py --check }
  Invoke-Checked -Name "foundation ci/cd surface validation" -Command { uv run python -c "from pathlib import Path; root = Path('.'); required = ['.github/workflows/foundation-ci.yml', 'scripts/package-foundation.ps1', 'scripts/foundation-rollback-plan.ps1', 'scripts/write-foundation-repo-manifest.py', 'pipeline/FOUNDATION_MANIFEST.json', 'FOUNDATION_REPO_MANIFEST.json']; missing = [p for p in required if not (root / p).exists()]; print('foundation ci/cd surfaces ok' if not missing else 'missing: ' + ', '.join(missing)); raise SystemExit(1 if missing else 0)" }
}
finally {
  Pop-Location
}
