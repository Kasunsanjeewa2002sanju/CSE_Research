# ============================================================================
# CSE Research & Live Engine - Unified Backend Launcher (PowerShell)
# ============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $ScriptDir "cse_research")

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} else {
    $pythonExe = "python"
}

& $pythonExe run_backend.py $args
