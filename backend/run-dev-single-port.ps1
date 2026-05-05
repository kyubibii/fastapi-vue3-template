$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

# Free port 8000 if occupied
$listenerPids = @(
  Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique
)

foreach ($listenerPid in $listenerPids) {
  if ($listenerPid) {
    try {
      Stop-Process -Id $listenerPid -Force -ErrorAction Stop
      Write-Host "Stopped process on :8000 -> PID $listenerPid"
    }
    catch {
      Write-Warning "Failed to stop PID $listenerPid; try running PowerShell as Administrator."
    }
  }
}

# Pin import resolution to this backend to avoid cross-project `app` package collisions
$env:PYTHONPATH = (Get-Location).Path

# Start FastAPI dev server on single port
uv run fastapi dev app/main.py --app app --host 127.0.0.1 --port 8000
