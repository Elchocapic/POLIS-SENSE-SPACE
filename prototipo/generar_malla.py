"""Convierte prototipo/modelo/cuerpo_humano_A_CC0.glb en prototipo/malla_cuerpo.json para el cuerpo 3D.

Uso:  python prototipo/generar_malla.py
El GLB es un cuerpo hecho con los recursos de MakeHuman (CC0 1.0), en metros, con 163 huesos y pesos por
vértice; su procedencia está en prototipo/modelo/. Aquí cada vértice se asigna a una parte del cuerpo según
el hueso que más pesa en él, así que los bordes entre zonas siguen la anatomía. Se guardan posiciones (int16),
parte de cada vértice (2 bytes) e índices (uint16) en base64.

La parte se guarda como dos números para que el dibujo no invente zonas en los bordes: `a` recorre
cabeza(0) cuello(1) tórax(2) abdomen(3) pelvis(4) muslo(5) pierna(6) pie(7), y `b` recorre el brazo:
0 no es brazo, 1 brazo, 2 antebrazo, 3 mano. Entre partes vecinas solo cambia uno de los dos, en 1.
"""
import base64, json, pathlib, struct
import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
b = (AQUI / "modelo" / "cuerpo_humano_A_CC0.glb").read_bytes()
largo = struct.unpack("<I", b[12:16])[0]
gltf = json.loads(b[20:20 + largo]); binario = b[20 + largo + 8:]

def accesor(i, tipo, n):
    a = gltf["accessors"][i]; v = gltf["bufferViews"][a["bufferView"]]
    return np.frombuffer(binario, dtype=tipo, count=a["count"] * n, offset=v.get("byteOffset", 0) + a.get("byteOffset", 0)).reshape(-1, n)

prim = gltf["meshes"][0]["primitives"][0]["attributes"]
P = accesor(prim["POSITION"], "<f4", 3).astype(float)
tri = accesor(gltf["meshes"][0]["primitives"][0]["indices"], "<u2", 1).reshape(-1, 3)
huesos = accesor(prim["JOINTS_0"], "u1", 4); pesos = accesor(prim["WEIGHTS_0"], "<f4", 4)

nodos = gltf["nodes"]; padre = {h: i for i, n in enumerate(nodos) for h in n.get("children", [])}
# Parte del cuerpo de cada hueso: la suya o la del primer antepasado que tenga una
PARTE = {"head": (0, 0), "neck": (1, 0), "spine01": (2, 0), "spine02": (2, 0), "clavicle": (2, 0), "breast": (2, 0),
         "spine03": (3, 0), "spine04": (3, 0), "spine05": (4, 0), "pelvis": (4, 0), "root": (4, 0),
         "shoulder": (2, 1), "upperarm": (2, 1), "lowerarm": (2, 2), "wrist": (2, 3),
         "upperleg": (5, 0), "lowerleg": (6, 0), "foot": (7, 0)}
def parte(i):
    while True:
        nombre = nodos[i].get("name", "")
        for clave, ab in PARTE.items():
            if nombre.startswith(clave):
                return ab
        if i not in padre:
            return (4, 0)
        i = padre[i]
articulaciones = gltf["skins"][0]["joints"]
ab_hueso = np.array([parte(n) for n in articulaciones])
# Parte de cada vértice: la que suma más peso entre sus huesos (más estable que mirar un solo hueso)
codigo_hueso = ab_hueso[:, 0] * 8 + ab_hueso[:, 1]
suma = np.zeros((len(P), 64))
for k in range(4):
    np.add.at(suma, (np.arange(len(P)), codigo_hueso[huesos[:, k]]), pesos[:, k])
codigo = suma.argmax(axis=1)
# La cadera y los glúteos cuelgan del hueso del muslo; por encima de la entrepierna se cuentan como pelvis
centro = (np.abs(P[:, 0]) < 0.012) & (P[:, 1] > 0.6) & (P[:, 1] < 1.1)
entrepierna = P[centro & np.isin(codigo, (4 * 8, 5 * 8)), 1].min()
codigo[(codigo == 5 * 8) & (P[:, 1] > entrepierna)] = 4 * 8
# Suaviza los bordes: cada vértice toma la parte más común entre él y sus vecinos
vecinos = [set() for _ in P]
for tr in tri:
    for i in range(3):
        vecinos[tr[i]].update((int(tr[(i + 1) % 3]), int(tr[(i + 2) % 3])))
vecinos = [np.array(sorted(v), dtype=int) for v in vecinos]
for _ in range(6):
    nuevo = codigo.copy()
    for i, v in enumerate(vecinos):
        if len(v) and (codigo[v] != codigo[i]).any():
            c = np.bincount(np.append(codigo[v], codigo[i]), minlength=64)
            nuevo[i] = c.argmax() if c.max() > c[codigo[i]] else codigo[i]
    codigo = nuevo
AB = np.stack([codigo // 8, codigo % 8], axis=1).astype(np.uint8)
print("entrepierna a", round(float(entrepierna), 3), "m")

ESC = 15000                                  # metros -> int16 (la figura mide 1,78 m)
q = np.round(P * ESC).astype(np.int16)
assert len(P) < 65536 and np.abs(P * ESC).max() < 32767
salida = {"licencia": "Cuerpo hecho con recursos de MakeHuman, CC0 1.0. Ver prototipo/modelo/", "escala": ESC, "alto": round(float(P[:, 1].max()), 3),
          "vertices": len(P), "triangulos": len(tri),
          "v": base64.b64encode(q.tobytes()).decode(), "z": base64.b64encode(AB.tobytes()).decode(),
          "f": base64.b64encode(tri.astype(np.uint16).tobytes()).decode()}
(AQUI / "malla_cuerpo.json").write_text(json.dumps(salida), encoding="utf-8")
nombres = ["cabeza", "cuello", "tórax", "abdomen", "pelvis", "muslo", "pierna", "pie"]; brazo = ["", "brazo", "antebrazo", "mano"]
cuenta = {}
for a_, b_ in AB:
    k = brazo[b_] or nombres[a_]; cuenta[k] = cuenta.get(k, 0) + 1
print(len(P), "vértices,", len(tri), "triángulos,", (AQUI / "malla_cuerpo.json").stat().st_size // 1024, "KB"); print(cuenta)
