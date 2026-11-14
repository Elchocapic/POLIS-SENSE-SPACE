# EMPEZAR A TRABAJAR: trae cambios y memoria del equipo
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$env:ENGRAM_PROJECT = "nasa-space-app"   # igual para todo el equipo
git pull --rebase
if (Test-Path .engram) { engram sync --import } else { Write-Host "(aún no hay memoria compartida)" }
Write-Host "Al día."
