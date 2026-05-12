param(
    [string]$TaskName = "TechDailyDashboard"
)

$ErrorActionPreference = "Stop"

schtasks.exe /Delete /TN $TaskName /F | Out-Null

Write-Host "Scheduled task '$TaskName' deleted."
