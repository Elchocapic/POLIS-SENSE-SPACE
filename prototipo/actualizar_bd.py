"""Mete la base de datos de salud espacial dentro del prototipo.

    python data/salud-espacial/build_db.py
    python prototipo/actualizar_bd.py

Lee data/salud-espacial/astronaut_health.json, guarda una versión compacta en
prototipo/plantilla.html (donde está /*BD*/) y escribe prototipo/index.html.
El resultado es un solo archivo que funciona sin conexión.
"""
import json
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
BD_JSON = RAIZ / "data" / "salud-espacial" / "astronaut_health.json"
PLANTILLA = RAIZ / "prototipo" / "plantilla.html"
SALIDA = RAIZ / "prototipo" / "index.html"

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
SALIDA.write_text(html.replace("/*BD*/", codigo), encoding="utf-8")
print("prototipo/index.html actualizado:", len(bd["efectos"]), "hallazgos,", len(bd["fuentes"]), "fuentes")
