$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$env:DEBUG = "False"
$env:HOST = "0.0.0.0"

python run.py
