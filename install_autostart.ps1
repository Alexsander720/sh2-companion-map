# Registers a Windows Scheduled Task for SILENT HILL 2 Live Companion Map (port 8791, LAN).
# Starts silently at logon (pythonw) with a 10-minute watchdog (exits immediately if port 8791 is already active).
$root = $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $py)) {
    $py = Join-Path $root ".venv\Scripts\python.exe"
}
if (-not (Test-Path $py)) {
    throw "Virtual environment not found. Run start.bat once first."
}
$srv = Join-Path $root "server.py"
$act = New-ScheduledTaskAction -Execute $py -Argument "`"$srv`" --port 8791 --lan --no-browser" -WorkingDirectory $root
$t1 = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$t2 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10)
$set = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "SH2CompanionMap" -Action $act -Trigger @($t1, $t2) -Settings $set -Description "SILENT HILL 2 Live Companion Map (:8791 LAN)" -Force | Out-Null
Start-ScheduledTask -TaskName "SH2CompanionMap"
(Get-ScheduledTask -TaskName "SH2CompanionMap").State