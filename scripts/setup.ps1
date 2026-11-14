# Prepara un dispositivo nuevo (Windows PowerShell). Uso: .\scripts\setup.ps1 [-Agent claude-code]
param([string]$Agent = "claude-code")
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Falta git" }
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Host ">> Instalando uv..."
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
if (-not (Get-Command specify -ErrorAction SilentlyContinue)) {
  Write-Host ">> Instalando Spec Kit..."; uv tool install specify-cli
}
if (-not (Get-Command engram -ErrorAction SilentlyContinue)) {
  Write-Host "!! Falta Engram. Descarga engram_<version>_windows_amd64.zip de:"
  Write-Host "   https://github.com/Gentleman-Programming/engram/releases"
  Write-Host "   o usa: go install github.com/Gentleman-Programming/engram/v3/cmd/engram@latest"
  Write-Host "   Ponlo en el PATH y vuelve a correr este script."; exit 1
}
Write-Host ">> Conectando Engram con $Agent..."; engram setup $Agent
.\scripts\sync-in.ps1
Write-Host "Listo. Reinicia tu agente y abre esta carpeta."
