param(
    [string]$TaskName = "TechDailyDashboard",
    [string]$ScheduleTime = "08:30",
    [string]$PythonCommand = "python",
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

$runScript = Join-Path $ProjectRoot "scripts\run_daily_report.ps1"
if (-not (Test-Path -LiteralPath $runScript)) {
    throw "Run script not found: $runScript"
}

$taskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$runScript`" -ProjectRoot `"$ProjectRoot`" -PythonCommand `"$PythonCommand`""

schtasks.exe /Create /SC DAILY /TN $TaskName /TR $taskCommand /ST $ScheduleTime /F | Out-Null

Write-Host "Scheduled task '$TaskName' registered for $ScheduleTime."
