#!/usr/bin/env bash
# Prepara un dispositivo nuevo (Linux/macOS). Uso: bash scripts/setup.sh [agente]
# agente de Engram: claude-code (por defecto), codex, cursor, gemini-cli, opencode...
set -euo pipefail
AGENT="${1:-claude-code}"
cd "$(dirname "$0")/.."

command -v git >/dev/null || { echo "Falta git"; exit 1; }
if ! command -v uv >/dev/null; then
  echo ">> Instalando uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
if ! command -v specify >/dev/null; then
  echo ">> Instalando Spec Kit (specify)..."; uv tool install specify-cli
fi
if ! command -v engram >/dev/null; then
  echo "!! Falta Engram. Instálalo con:  brew install gentleman-programming/tap/engram"
  echo "   o descarga el binario: https://github.com/Gentleman-Programming/engram/releases"
  echo "   (o 'go install' con Go >= 1.26.11). Luego vuelve a correr este script."; exit 1
fi
echo ">> Conectando Engram con $AGENT..."; engram setup "$AGENT"
echo ">> Importando memoria compartida (si existe)..."
bash scripts/sync-in.sh || true
echo "Listo. Reinicia tu agente y abre esta carpeta."
