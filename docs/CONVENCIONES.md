# Convenciones del equipo

## Memoria (Engram)
- **Un solo proyecto**: `nasa-space-app` (no cambiarlo; la memoria se separa por nombre de proyecto).
- **Un solo idioma** para memorias compartidas (acordar: español o inglés). La búsqueda no cruza idiomas.
- `scope: project` → decisiones, bugs, convenciones, datos del reto (útil para todos).
- `scope: personal` → notas propias. **Ojo:** el scope NO evita la sincronización. Para notas realmente privadas, usar otro proyecto de Engram y no subirlo.
- Nunca guardar contraseñas, tokens ni claves API en memorias.
- Al cerrar sesión, pedir al agente un `mem_session_summary`.

## Spec Kit
- Constitución y specs son archivos del repo: se cambian por Git como cualquier código.
- **Una spec/feature por persona** para evitar conflictos. Avisar en el chat del equipo antes de editar `constitution.md`.
- Flujo: `/speckit-constitution` (una vez) → `/speckit-specify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement` → `/speckit-converge`.

## Git
- Rama `main` estable; cada quien trabaja en rama `feat/<nombre>-<tema>` y abre PR.
- Commits pequeños y frecuentes. Siempre `git pull --rebase` antes de `push`.
