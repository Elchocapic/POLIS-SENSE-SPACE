# TERMINAR DE TRABAJAR: exporta tu memoria y sube todo. Uso: .\scripts\sync-out.ps1 "mensaje"
param([string]$Msg = "sync: avance")
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$env:ENGRAM_PROJECT = "polis-sense-space"
engram sync --project $env:ENGRAM_PROJECT
Write-Host ">> REVISA .engram\ por secretos antes de continuar (5s, Ctrl+C cancela)"; Start-Sleep 5
git add -A
git diff --cached --quiet; if ($LASTEXITCODE -eq 0) { Write-Host "Nada que subir."; exit 0 }
git commit -m $Msg
git pull --rebase; git push
Write-Host "Subido."
