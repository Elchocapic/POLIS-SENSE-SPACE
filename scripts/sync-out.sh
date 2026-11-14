#!/usr/bin/env bash
# TERMINAR DE TRABAJAR: exporta tu memoria y sube todo. Uso: bash scripts/sync-out.sh "mensaje"
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/config.sh
MSG="${1:-sync: avance}"
engram sync --project "$ENGRAM_PROJECT"
echo ">> REVISA .engram/ por secretos antes de continuar (Ctrl+C para cancelar, 5s)"; sleep 5
git add -A
git diff --cached --quiet && { echo "Nada que subir."; exit 0; }
git commit -m "$MSG"
git pull --rebase && git push
echo "Subido."
