$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Engine = Join-Path $Root "engine"
$OriginalCwd = (Get-Location).ProviderPath
$NormalizedArgs = New-Object System.Collections.Generic.List[string]
for ($i = 0; $i -lt $args.Count; $i++) {
  $arg = [string]$args[$i]
  if (($arg -eq "--project" -or $arg -eq "--foundation-root") -and ($i + 1) -lt $args.Count) {
    $NormalizedArgs.Add($arg)
    $value = [string]$args[$i + 1]
    if ([System.IO.Path]::IsPathRooted($value)) {
      $NormalizedArgs.Add($value)
    } else {
      $NormalizedArgs.Add([System.IO.Path]::GetFullPath((Join-Path $OriginalCwd $value)))
    }
    $i += 1
    continue
  }
  if ($arg.StartsWith("--project=") -or $arg.StartsWith("--foundation-root=")) {
    $parts = $arg.Split("=", 2)
    $value = $parts[1]
    if (-not [System.IO.Path]::IsPathRooted($value)) {
      $value = [System.IO.Path]::GetFullPath((Join-Path $OriginalCwd $value))
    }
    $NormalizedArgs.Add("$($parts[0])=$value")
    continue
  }
  $NormalizedArgs.Add($arg)
}
$old = $env:PYTHONPATH
if ([string]::IsNullOrWhiteSpace($old)) {
  $env:PYTHONPATH = $Engine
} else {
  $env:PYTHONPATH = "$Engine;$old"
}
$pythonArgs = @("run", "python", "-m", "codex_pipeline.cli") + $NormalizedArgs.ToArray()
if (Get-Command uv -ErrorAction SilentlyContinue) {
  Push-Location $Root
  try {
    & uv @pythonArgs
    exit $LASTEXITCODE
  } finally {
    Pop-Location
  }
}

if (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 -m codex_pipeline.cli @args
  exit $LASTEXITCODE
}

& python -m codex_pipeline.cli @args
exit $LASTEXITCODE
