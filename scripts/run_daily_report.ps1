param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$PythonCommand = "python",
    [string]$OutputDir = "build/site"
)

$ErrorActionPreference = "Stop"

Set-Location $ProjectRoot

$logDir = Join-Path $ProjectRoot "build/logs"
if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$reportDate = Get-Date -Format "yyyy-MM-dd"
$logPath = Join-Path $logDir "$reportDate.log"

"[$(Get-Date -Format s)] Starting daily report generation." | Out-File -FilePath $logPath -Encoding utf8 -Append
$commandOutput = & $PythonCommand "run_dashboard.py" "generate-today" "--output-dir" $OutputDir 2>&1
$commandOutput | ForEach-Object { $_.ToString() } | Out-File -FilePath $logPath -Encoding utf8 -Append
$exitCode = $LASTEXITCODE
"[$(Get-Date -Format s)] Finished with exit code $exitCode." | Out-File -FilePath $logPath -Encoding utf8 -Append

if ($exitCode -ne 0) {
    throw "Daily report generation failed with exit code $exitCode. Check $logPath."
}
