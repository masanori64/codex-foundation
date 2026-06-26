$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PipelineRoot = Resolve-Path (Join-Path $ScriptDir "..")
$Script = Join-Path $PipelineRoot "scripts\write-foundation-manifest.py"

if (Get-Command uv -ErrorAction SilentlyContinue) {
  Push-Location $PipelineRoot
  try {
    & uv run python $Script @args
    exit $LASTEXITCODE
  } finally {
    Pop-Location
  }
}

if (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 $Script @args
  exit $LASTEXITCODE
}

& python $Script @args
exit $LASTEXITCODE
