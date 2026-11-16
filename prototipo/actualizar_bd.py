"""Mete la base de datos de salud espacial dentro del prototipo.

    python data/salud-espacial/build_db.py
    python prototipo/actualizar_bd.py

Lee data/salud-espacial/astronaut_health.json, guarda una versión compacta en
prototipo/plantilla.html (donde está /*BD*/) y escribe prototipo/index.html.
También mete los registros reales de data/monitoreo-real/ (donde está /*REAL*/),
que alimentan la pestaña "Datos reales".
El resultado es un solo archivo que funciona sin conexión.
"""
import csv
import json
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
BD_JSON = RAIZ / "data" / "salud-espacial" / "astronaut_health.json"
PLANTILLA = RAIZ / "prototipo" / "plantilla.html"
SALIDA = RAIZ / "prototipo" / "index.html"
REAL_JSON = RAIZ / "data" / "monitoreo-real" / "alertas_v2.json"
SOMA_JSON = RAIZ / "data" / "monitoreo-real" / "evidencia_soma.json"
LIMITES_CSV = RAIZ / "data" / "monitoreo-real" / "limites_v2.csv"
MODELO_JSON = RAIZ / "data" / "monitoreo-real" / "pronostico.json"

EFECTO = ["indicador_id", "mision", "duracion_dias", "fase", "valor_pre", "valor_vuelo", "valor_post",
          "cambio", "cambio_min", "cambio_max", "cambio_unidad", "tendencia", "n", "fuente_id", "hallazgo"]
PARAM = ["indicador_id", "valor_tierra", "valor_vuelo_objetivo", "forma", "tasa_por_mes", "tasa_unidad",
         "dias_hasta_estable", "fuente_id", "origen", "nota"]


def solo(fila, campos):
    return {k: fila[k] for k in campos if fila.get(k) is not None}


d = json.loads(BD_JSON.read_text(encoding="utf-8"))
bd = {
    "fuentes": [solo(f, ["id", "cita", "anio", "url"]) for f in d["fuentes"]],
    "indicadores": [solo(i, ["id", "nombre", "sistema", "unidad"]) for i in d["indicadores"]],
    "efectos": [solo(e, EFECTO) for e in d["efectos"]],
    "parametros": [solo(p, PARAM) for p in d["parametros_simulacion"]],
}
html = PLANTILLA.read_text(encoding="utf-8")
if "/*BD*/" not in html:
    raise SystemExit("La plantilla no tiene el marcador /*BD*/")
codigo = "const BD = " + json.dumps(bd, ensure_ascii=False, separators=(",", ":")) + ";"


def datos_reales():
    """Compacta alertas_v2.json: una serie por tripulante y variable, [día, valor, estado]."""
    filas = json.loads(REAL_JSON.read_text(encoding="utf-8"))
    dias = sorted({f["dia"] for f in filas})
    pos = {d: i for i, d in enumerate(dias)}
    estado = {"normal": 0, "vigilancia": 1, "alerta": 2}
    lado = {"pulso_reposo": "ambos", "carga_cardiaca": "alto", "inquietud": "alto"}
    variables, trip, dolor = {}, {}, {}
    for f in filas:
        k, p = f["variable"], f["astronauta"]
        variables.setdefault(k, {"nombre": f["nombre"], "unidad": f["unidad"], "zona": f["zona_cuerpo"],
                                 "lado": lado.get(k, "bajo")})
        s = trip.setdefault(p, {}).setdefault(k, {"m": f["media"], "li": f["limite_inferior"],
                                                   "ls": f["limite_superior"], "b": 0, "d": []})
        s["b"] += f["fase"] == "linea_base"
        s["d"].append([pos[f["dia"]], f["valor"], estado[f["estado"]]])
        if f.get("zonas_dolor"):
            dolor.setdefault(p, {})[pos[f["dia"]]] = f["zonas_dolor"]
    for p in trip.values():
        for s in p.values():
            s["d"].sort()
    with LIMITES_CSV.open(encoding="utf-8") as f:      # sigma de cada serie: la usa el pronóstico
        for fila in csv.DictReader(f):
            trip[fila["astronauta"]][fila["variable"]]["s"] = float(fila["sigma"])
    soma = [{k: e[k] for k in ("id", "zona_cuerpo", "variables_relacionadas", "hallazgo", "cita", "anio", "url")}
            for e in json.loads(SOMA_JSON.read_text(encoding="utf-8"))]
    return {"dias": dias, "vars": variables, "trip": trip, "dolor": dolor, "soma": soma}, len(filas)


if "/*REAL*/" not in html:
    raise SystemExit("La plantilla no tiene el marcador /*REAL*/")
real, n_real = datos_reales()
codigo_real = "const REAL = " + json.dumps(real, ensure_ascii=False, separators=(",", ":")) + ";"
SALIDA.write_text(html.replace("/*BD*/", codigo).replace("/*REAL*/", codigo_real), encoding="utf-8")

# Segunda página: tripulación con datos reales (interfaz guiada por AURORA).
# Los procedimientos y el asistente se copian de plantilla.html para mantenerlos en un solo lugar.
TRIP_PLANTILLA = RAIZ / "prototipo" / "plantilla_tripulacion.html"
TRIP_SALIDA = RAIZ / "prototipo" / "tripulacion.html"


def tramo(texto, desde, hasta):
    a = texto.index(desde)
    return texto[a:texto.index(hasta, a)].rstrip()


SEP = "// ====================================================================="
# La página de tripulación está en inglés: usa la versión en inglés de los procedimientos y del asistente.
proc = (RAIZ / "prototipo" / "procedimientos_en.js").read_text(encoding="utf-8")
EN = json.loads((RAIZ / "prototipo" / "traduccion_en.json").read_text(encoding="utf-8"))
real_en = json.loads(json.dumps(real))
for k, v in real_en["vars"].items():
    v.update(EN["vars"][k])
codigo_real_en = "const REAL = " + json.dumps(real_en, ensure_ascii=False, separators=(",", ":")) + ";"
trip = TRIP_PLANTILLA.read_text(encoding="utf-8")
modelo = json.loads(MODELO_JSON.read_text(encoding="utf-8"))
campos = ("b", "w", "avisos_correctos", "casos_detectados", "auc_tiempo")
codigo_modelo = "const MODELO = " + json.dumps(
    {"objetivos": {k: {c: o[c] for c in campos} for k, o in modelo["objetivos"].items()}, "pruebas": modelo["pruebas"]},
    ensure_ascii=False, separators=(",", ":")) + ";"
# Malla del cuerpo 3D (MakeHuman, CC0), generada una vez con prototipo/generar_malla.py
malla = json.loads((RAIZ / "prototipo" / "malla_cuerpo.json").read_text(encoding="utf-8"))
codigo_malla = "const MALLA = " + json.dumps({k: malla[k] for k in ("escala", "alto", "v", "z", "f")}, separators=(",", ":")) + ";"
# Hechos que Luma puede citar: los hallazgos de la base del equipo más tres datos de medicina espacial (fuentes en prototipo/README.md)
HECHOS_EXTRA = [
    "Mareo espacial: afecta a entre 60 y 80 % de los astronautas en los primeros 2 o 3 días y suele resolverse antes de 72 horas.",
    "Dolor de espalda por adaptación al espacio: incidencia de 52 % (382 de 728 astronautas), leve en 86 % de los casos; la posición fetal (rodillas al pecho) alivió en 91 %.",
    "Atención médica en la ISS: hay un oficial médico de la tripulación, médicos de vuelo en Tierra con conferencia médica privada, un desfibrilador a bordo y evacuación posible en horas.",
]
hechos = [e["hallazgo"] + " (" + e["mision"] + ")" for e in json.loads(BD_JSON.read_text(encoding="utf-8"))["efectos"]] + HECHOS_EXTRA
if len(EN["hechos"]) != len(hechos):
    raise SystemExit("traduccion_en.json debe tener un hecho en inglés por cada hecho de la base")
hechos = EN["hechos"]
codigo_hechos = "const HECHOS = " + json.dumps(hechos, ensure_ascii=False, separators=(",", ":")) + ";"
for marca in ("/*REAL*/", "/*MODELO*/", "/*MALLA*/", "/*HECHOS*/", "/*PROC*/"):
    if marca not in trip:
        raise SystemExit(f"plantilla_tripulacion.html no tiene el marcador {marca}")
TRIP_SALIDA.write_text(trip.replace("/*REAL*/", codigo_real_en).replace("/*MODELO*/", codigo_modelo).replace("/*MALLA*/", codigo_malla).replace("/*HECHOS*/", codigo_hechos).replace("/*PROC*/", proc),
                       encoding="utf-8")
print("prototipo/tripulacion.html actualizado")
print("prototipo/index.html actualizado:", len(bd["efectos"]), "hallazgos,", len(bd["fuentes"]), "fuentes,",
      n_real, "registros reales de", len(real["trip"]), "tripulantes")
