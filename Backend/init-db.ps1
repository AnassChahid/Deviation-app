$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot

python -m app.db.initialize
