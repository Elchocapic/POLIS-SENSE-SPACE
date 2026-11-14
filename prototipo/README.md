# Prototipo POLIS SENSE SPACE

App web de una sola página para monitorear la salud del astronauta: mapa corporal, lecturas, alertas
con causa probable, pasos y checklist, tendencias, chequeo diario, test de atención y asistente sin conexión.

Abre `index.html` en el navegador (doble clic). No necesita servidor ni internet.

## Cómo usa la base de datos

`index.html` lleva dentro la base de `data/salud-espacial/`:

- **Día de misión** (14, 60, 120, 180): los datos simulados siguen la adaptación medida en la ISS
  (presión sistólica −14 mmHg, temperatura en reposo +1 °C en ~75 días, ~0,4 h menos de sueño).
  La línea base de cada tripulante se calcula en vuelo, así la adaptación no se confunde con enfermedad.
- **Dato del vuelo** en cada alerta: el hallazgo publicado que la explica, con enlace al estudio.
- **Cambios lentos**: hueso, músculo y masa corporal estimados para el día de misión.
- **Radiación**: tasa diaria y límite de carrera de la base.
- **Pestaña Datos del vuelo**: los 49 hallazgos, filtrables por sistema, con su fuente.

## Editar

- La página se edita en `plantilla.html` (no en `index.html`, que se genera).
- Los datos se editan en `data/salud-espacial/build_db.py`.

Después de cualquier cambio:

```bash
python data/salud-espacial/build_db.py
python prototipo/actualizar_bd.py
```
