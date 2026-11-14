#!/usr/bin/env bash
# EMPEZAR A TRABAJAR: trae cambios y memoria del equipo
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/config.sh
git pull --rebase
[ -d .engram ] && engram sync --import || echo "(aún no hay memoria compartida)"
echo "Al día."
