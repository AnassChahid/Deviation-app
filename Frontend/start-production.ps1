$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not $env:HOST) { $env:HOST = "0.0.0.0" }
if (-not $env:PORT) { $env:PORT = "5000" }

waitress-serve --host=$env:HOST --port=$env:PORT run:app
