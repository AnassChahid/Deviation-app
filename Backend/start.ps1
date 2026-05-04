$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot

python -m uvicorn app.main:app --app-dir $PSScriptRoot --reload --reload-dir $PSScriptRoot --port 8001
