$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot

python -m uvicorn app.main:app --app-dir $PSScriptRoot --host 0.0.0.0 --port 8001
