$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot

if (-not $env:HOST) { $env:HOST = "0.0.0.0" }
if (-not $env:PORT) { $env:PORT = "8001" }

python -m uvicorn app.main:app --app-dir $PSScriptRoot --host $env:HOST --port $env:PORT
