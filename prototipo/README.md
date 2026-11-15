# Prototipo POLIS SENSE SPACE

App web de una sola página para monitorear la salud del astronauta: mapa corporal, lecturas, alertas
con causa probable, pasos y checklist, tendencias, chequeo diario, test de atención y asistente sin conexión. `tripulacion.html` añade el cuerpo 3D y a Luma, la asistente de voz.

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

## Pestaña Datos reales

Usa `data/monitoreo-real/alertas_v2.json`: 5 personas reales (P01–P05), 151 días y 12 variables, cada una
comparada con el rango normal de esa persona. Con la barra de día se recorre el registro; los botones de
**Casos** saltan a los días más útiles para la demo. Cada alerta trae zona en el mapa, causa probable
(reglas simples sobre coincidencias entre variables), dato del vuelo, checklist y pasos.

Son datos de personas en Tierra (PMData), no de astronautas. Detalles en `data/monitoreo-real/README.md`.

## Página de tripulación (`tripulacion.html`)

Segunda página, con la interfaz guiada por AURORA y paleta de cielo profundo. Tiene dos pestañas:

- **Tripulación**: los cinco astronautas con datos reales (P01–P05) por separado. Al elegir uno se ve un
  cuerpo en 3D que se gira arrastrando; cada zona se colorea según el tipo de problema (dolor muscular,
  pulso, sueño, ánimo, fatiga) y, al pasar el mouse, dice qué tiene. El rayado fino marca dónde es posible
  que haya dolor mañana. Debajo van las lecturas del día, las alertas y el pronóstico. Cada alerta dice por qué salta,
  la causa probable, las otras posibilidades y si los datos las apoyan, un resumen de casos similares en la
  tripulación, el checklist, los pasos y cuándo escalar.
- **Luma**: acompañante de salud con el que se conversa por voz o por texto, con el pronóstico para mañana
  al lado (dolor muscular, pulso, sueño y fatiga, con motivos y qué hacer para adelantarse). La idea es la de
  un asistente cercano tipo "robot enfermero", con nombre y aspecto propios y sin hardware.

Luma tiene tres piezas y cada una tiene respaldo:

| Pieza | Publicada como artefacto de Claude | Archivo abierto en el navegador |
|---|---|---|
| Cerebro | Claude, con los registros del día, alertas, pronóstico, estado de la tripulación y los hechos verificados | Reglas locales: 10 emergencias, 14 casos frecuentes en el espacio, registros y pronóstico |
| Oído | Dictado del artefacto | Reconocimiento de voz del navegador (Chrome o Edge, con internet) o teclado |
| Voz | Voz del artefacto | Síntesis de voz del navegador |

- Las emergencias (no responde, dolor de pecho, atragantamiento, sangrado, convulsión, alergia grave,
  quemadura, emergencia de la nave, golpe en la cabeza, ideas de hacerse daño) se detectan siempre en la
  página, sin esperar al modelo, y muestran primeros auxilios y a quién avisar.
- Las respuestas cambian con el día de misión (el control de día de la página): mareo en el día 2 es
  adaptación; en el día 100 hay que buscar otra causa.
- Luma solo cita cifras de `HECHOS`: los 49 hallazgos de `data/salud-espacial/astronaut_health.json` más
  tres datos añadidos en `actualizar_bd.py` (mareo espacial 60-80 % en los primeros 2-3 días; dolor de
  espalda 52 %, Kerstman et al. 2012, Aviat Space Environ Med 83(1):2-7; atención médica en la ISS).
- No diagnostica ni indica dosis: orienta, da primeros auxilios generales y dice cuándo escalar. Los pasos
  son de ejemplo y no sustituyen los procedimientos médicos de una misión.

El cuerpo es `modelo/cuerpo_humano_A_CC0.glb` (54 046 vértices, 163 huesos, CC0 1.0; procedencia en
`modelo/`). `generar_malla.py` lo convierte a `malla_cuerpo.json` y asigna cada vértice a una parte
(cabeza, cuello, tórax, abdomen, pelvis, muslo, pierna, pie, brazo, antebrazo, mano) sumando los pesos de
los huesos del modelo, con un suavizado entre vecinos para que los bordes sigan las articulaciones. La
página lo dibuja con WebGL sin librerías; el aviso del mouse nombra la parte exacta (por ejemplo, "Muslo
derecho" o "Espalda baja"). Los datos solo distinguen ocho zonas, y esas son las que se colorean. Sin WebGL
se muestra la silueta plana.

Se edita en `plantilla_tripulacion.html`. Los procedimientos se copian de `plantilla.html` al generar y el
modelo de pronóstico viene de `data/monitoreo-real/pronostico.json`.

## Editar

- La página se edita en `plantilla.html` (no en `index.html`, que se genera).
- Los datos se editan en `data/salud-espacial/build_db.py`.
- Los registros reales se regeneran con `data/monitoreo-real/kpi_extra.py`.

Después de cualquier cambio:

```bash
python data/salud-espacial/build_db.py
python prototipo/actualizar_bd.py
```
