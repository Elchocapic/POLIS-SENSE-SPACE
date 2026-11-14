# POLIS SENSE SPACE

Repositorio compartido del equipo. Metodología: **Spec Kit** (specs → plan → tareas → código). Memoria del agente compartida con **Engram** vía Git Sync.

> Detalles del reto: _(completar cuando se definan)_ — ver `docs/RETO.md`.

## 1. Primera vez en cada dispositivo
Requisitos: git, un agente (Claude Code, Codex, Cursor...), Engram instalado.

| Sistema | Comando |
|---|---|
| Linux / macOS | `bash scripts/setup.sh` (o `bash scripts/setup.sh codex`) |
| Windows | `.\scripts\setup.ps1` (o `.\scripts\setup.ps1 -Agent codex`) |

Instalar Engram: `brew install gentleman-programming/tap/engram` o binario en https://github.com/Gentleman-Programming/engram/releases

## 2. Rutina diaria
1. **Al empezar:** `scripts/sync-in` (git pull + `engram sync --import`).
2. Trabajar con el agente usando los comandos `/speckit-*`.
3. **Al terminar:** `scripts/sync-out "qué hice"` (exporta memoria, commit, push).

(`.sh` en Linux/macOS, `.ps1` en Windows.)

## 3. Qué se comparte y dónde
| Qué | Dónde | Cómo |
|---|---|---|
| Specs, planes, tareas, constitución | `.specify/`, `specs/` | Git |
| Datos de salud en el espacio (valores publicados) | `data/salud-espacial/` | Git — ver su README |
| Prototipo de la app (usa la base de datos) | `prototipo/` | Git — abrir `prototipo/index.html` |
| Código | resto del repo | Git |
| Memoria del agente | `.engram/chunks/` | `sync-in` / `sync-out` |

Convenciones: `docs/CONVENCIONES.md`.
