# Monitoreo con datos reales

Registros diarios de 5 personas (P01–P05) durante 151 días, ya convertidos en alertas con línea base
personal. Alimentan la pestaña **Datos reales** del prototipo. Son personas en Tierra con reloj Fitbit
y autorreporte (dataset PMData), no astronautas: sirven para probar la detección con datos que no inventamos.

## Archivos

| Archivo | Para qué |
|---|---|
| `alertas_v2.json` | 7 275 entradas: una por tripulante, día y variable. **Es lo que lee el prototipo** |
| `limites_v2.csv` | Media, sigma y límites de cada tripulante y variable |
| `datos_diarios.csv`, `kpi_diarios.csv` | Valores diarios sin procesar (5 variables originales y 7 nuevas) |
| `evidencia_soma.json` | 14 hallazgos publicados de astronautas reales (Inspiration4), con cita |
| `analisis.R` | Script original: pulso en reposo, sueño, ánimo, estrés y fatiga |
| `kpi_extra.py` | Script que agrega las 7 variables nuevas y corrige los límites de las escalas 1–5 |

## Campos de `alertas_v2.json`

| Campo | Qué es |
|---|---|
| `astronauta`, `dia` | P01…P05 y fecha (1 nov 2019 – 30 mar 2020) |
| `variable`, `nombre`, `unidad` | Qué se mide |
| `valor` | Medición de ese día |
| `media`, `limite_inferior`, `limite_superior` | Rango normal de esa persona |
| `fase` | `linea_base` (primeros 21 registros, sin alertas) o `monitoreo` |
| `estado` | `normal`, `vigilancia` o `alerta` |
| `direccion` | `alto` o `bajo` (vacío si normal) |
| `zona_cuerpo` | `corazon`, `cabeza` o `musculos` |
| `accion` | Texto recomendado (vacío si normal) |
| `zonas_dolor` | Solo en `dolor`: pierna/brazo izquierdo o derecho, pelvis, tronco, cabeza |

## Variables

| Variable | Qué mide | Alerta cuando |
|---|---|---|
| `pulso_reposo` | Pulso en reposo (lpm) | sale del rango, o < 40 o > 100 |
| `sueno` | Puntaje de sueño del reloj | baja del límite |
| `animo`, `estres`, `fatiga` | Autorreporte 1–5 (5 = mejor) | baja del límite |
| `carga_cardiaca` | Minutos del día con pulso sobre 120 lpm | sube sobre el límite |
| `recuperacion_nocturna` | Mediana del pulso por hora menos el mínimo sostenido 3 h (lpm) | baja del límite |
| `sueno_profundo` | Minutos de sueño profundo | baja del límite |
| `inquietud` | Inquietud durante el sueño (%) | sube sobre el límite |
| `horas_sueno` | Horas dormidas, autorreporte | baja del límite |
| `disposicion` | Disposición para la actividad (0–10) | baja del límite |
| `dolor` | Dolor muscular 1–5 (5 = sin dolor, 3 = normal) | 2 = vigilancia, 1 = alerta |

## Método

- Línea base: los primeros 21 registros de cada persona y variable. Límites: media ± 3 sigma.
- Vigilancia: 5 registros seguidos del lado desfavorable de la media (pulso, sueño, recuperación,
  sueño profundo, inquietud).
- Escalas 1–5: el límite inferior nunca baja de 1,5, así marcar 1 siempre es alerta. Sin este piso
  el límite quedaba por debajo de 1 en P04 y P05 y la alerta era imposible (23 alertas nuevas).
- `recuperacion_nocturna` no usa horas fijas de reloj: el ritmo diario de P04 se desplaza unas 12 h en
  enero de 2020.
- Un día cuenta para `carga_cardiaca` con 6 h o más de reloj puesto, y para `recuperacion_nocturna`
  con 18 h o más.
- En el autorreporte, 0 es "sin dato" (P05 tiene 60 registros de disposición en 0).
- Donde un valor negativo no existe, el límite inferior se recorta a 0. En esos casos no puede haber
  alerta, solo vigilancia (p. ej. sueño profundo de P01 y P02).

## Volver a generar

Los datos crudos de PMData (unos 500 MB de pulso cada 5 s) no están en el repositorio. Se descargan de
https://datasets.simula.no/pmdata/ y se dejan en una carpeta con `P01/` … `P05/` y `entrega/alertas.json`
(la salida de `analisis.R`).

```bash
python data/monitoreo-real/kpi_extra.py <carpeta PMData> data/monitoreo-real
python prototipo/actualizar_bd.py
```

## `evidencia_soma.json`

Hallazgos ya publicados sobre la tripulación de Inspiration4 (4 civiles, 3 días en órbita). El prototipo
los muestra como "Dato del vuelo" en las alertas. Todos están tomados del texto de los dos artículos.
`variables_relacionadas` lo asignamos nosotros; los artículos no hacen esa relación.

No hay indicadores calculados con los archivos de SOMA: en el de exosomas, las muestras previas al vuelo
difieren entre sí tanto como la del aterrizaje (143–311 proteínas de 527 frente a 190–292), así que una
regla simple mide ruido.

## Fuentes y licencia

- PMData: Thambawita V. et al., *PMData: a sports logging dataset*, MMSys 2020,
  https://doi.org/10.1145/3339825.3394926. Licencia CC BY-NC 4.0: uso no comercial y con cita.
- Overbey E. G. et al., *The Space Omics and Medical Atlas (SOMA) and international astronaut biobank*,
  Nature 632 (2024), https://doi.org/10.1038/s41586-024-07639-y
- Jones C. W. et al., *Molecular and physiological changes in the SpaceX Inspiration4 civilian crew*,
  Nature 632 (2024), https://doi.org/10.1038/s41586-024-07648-x
