# Base de datos: salud del astronauta en el espacio

Cómo cambian los indicadores de salud de los astronautas durante el vuelo espacial (presión, frecuencia
cardíaca, temperatura, sueño, hueso, músculo, masa corporal, sangre, radiación, visión, inmunidad…),
según estudios publicados. Cada valor tiene su fuente con enlace.

Los datos crudos de astronautas de la NASA (portal NLSP/LSDA) están protegidos por privacidad y se piden
por solicitud; estos son los valores **publicados** de esos estudios. La tabla `datasets` dice dónde
pedir o descargar los datos crudos.

## Archivos

| Archivo | Para qué |
|---|---|
| `astronaut_health.db` | Base SQLite con todas las tablas |
| `astronaut_health.json` | Las mismas tablas en JSON (para una app web o móvil) |
| `csv/*.csv` | Una tabla por archivo (Excel, Python, Google Sheets) |
| `build_db.py` | Script que genera todo lo anterior. **Los datos se editan aquí** |

## Tablas

| Tabla | Contenido |
|---|---|
| `indicadores` | Qué se mide, unidad e instrumento (39) |
| `efectos` | Cada hallazgo: valor antes / durante / después del vuelo, cambio, tendencia, n, fuente (49) |
| `parametros_simulacion` | Valor en Tierra, valor en vuelo, forma del cambio (escalón, gradual, lineal) y ritmo, para generar datos simulados (13) |
| `fuentes` | Cita y enlace de cada estudio (28) |
| `datasets` | Dónde están los datos crudos y si son públicos, por solicitud o no archivados (11) |
| `v_efectos` | Vista que une efectos + indicador + fuente |

En `parametros_simulacion`, `origen = 'supuesto'` marca valores que no se midieron directamente (ver `nota`).

## Regenerar

```bash
python data/salud-espacial/build_db.py                 # base + JSON + CSV
python data/salud-espacial/build_db.py --ts src/data/spaceflightEffects.ts   # además, un módulo TypeScript tipado
```

Solo usa la biblioteca estándar de Python (3.8+).

## Ejemplos

```sql
-- Todo lo cardiovascular, con su fuente
SELECT indicador, fase, valor_pre, valor_vuelo, valor_post, cambio, cambio_unidad, cita
FROM v_efectos WHERE sistema = 'cardiovascular';

-- Qué datos crudos se pueden descargar sin solicitud
SELECT nombre, repositorio, url FROM datasets WHERE acceso = 'publico';
```

```python
import json
db = json.load(open("data/salud-espacial/astronaut_health.json", encoding="utf-8"))
temp = next(p for p in db["parametros_simulacion"] if p["indicador_id"] == "temp_central_reposo")
# 37.0 °C en Tierra -> 38.0 °C en vuelo, de forma gradual en ~75 días
```
