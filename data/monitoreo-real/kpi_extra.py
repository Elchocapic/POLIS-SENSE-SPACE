"""KPI adicionales para alertas.json (monitoreo de salud de astronautas).

Uso:  python kpi_extra.py <carpeta NASA> <carpeta salida>
Entrada: P01..P05 (heart_rate*.json, sleep_score.csv, wellness.csv) y entrega/alertas.json
Salida:  alertas_v2.json / .csv (entradas originales + KPI nuevos), limites_v2.csv, kpi_diarios.csv
Metodo igual al de analisis.R: linea base = primeros 21 registros, limites = media +/- 3 sigma.
"""
import sys, re, glob, json, ast, os
import numpy as np, pandas as pd

BASE, OUT = sys.argv[1], sys.argv[2]
PERS = ["P01", "P02", "P03", "P04", "P05"]
NB, FIN = 21, "2020-03-30"
os.makedirs(OUT, exist_ok=True)

# variable: nombre, unidad, zona, lado desfavorable, piso de sigma, vigilancia por racha, accion
INFO = {
 "carga_cardiaca": ("Tiempo con pulso sobre 120 lpm", "min", "corazon", "alto", 5.0, False,
   "Más tiempo de lo habitual con el pulso sobre 120 lpm. Si fue ejercicio programado, prioriza recuperación e hidratación; si no lo fue, repite la medición en reposo y repórtalo al médico de vuelo."),
 "recuperacion_nocturna": ("Recuperación en el descanso (pulso medio − mínimo sostenido)", "lpm", "corazon", "bajo", 1.0, True,
   "Tu pulso bajó menos de lo habitual durante la noche. Revisa carga de ejercicio, hidratación y calidad del sueño; si se repite 3 noches, repórtalo."),
 "sueno_profundo": ("Sueño profundo", "min", "cabeza", "bajo", 5.0, True,
   "Menos sueño profundo de lo habitual en ti. Respeta el horario de sueño, reduce luz y ruido en la cabina y evita cafeína en la segunda mitad del día."),
 "inquietud": ("Inquietud durante el sueño", "%", "cabeza", "alto", 1.0, True,
   "Sueño más inquieto de lo habitual. Revisa temperatura, ruido y sujeción del saco de dormir; si se repite 3 noches, repórtalo."),
 "horas_sueno": ("Horas de sueño (autorreporte)", "h", "cabeza", "bajo", 0.5, False,
   "Dormiste menos horas de lo habitual en ti. Programa una siesta o adelanta la hora de dormir hoy y evita tareas críticas si te sientes somnoliento."),
 "disposicion": ("Disposición para la actividad (0–10)", "0-10", "musculos", "bajo", 0.5, False,
   "Te sientes menos dispuesto de lo habitual. Reduce la intensidad del ejercicio de hoy y revisa sueño, alimentación e hidratación."),
 "dolor": ("Dolor muscular (5 = sin dolor)", "1-5", "musculos", "bajo", 0.5, False, None),
}
ACC_DOLOR = {"vigilancia": "Dolor muscular reportado. Baja la carga sobre la zona señalada, estira y vigila la evolución; si dura más de 3 días, repórtalo.",
             "alerta": "Dolor muscular intenso. Suspende el ejercicio sobre la zona señalada y consulta al médico de vuelo."}
ACC_RACHA = "Tendencia sostenida fuera de tu promedio (5 o más días seguidos). Sin urgencia: vigila este indicador y coméntalo en el próximo control médico."
# Códigos SNOMED CT de soreness_area, verificados uno por uno (pierna, brazo, pelvis, tronco, cabeza)
ZONAS = {48979004: "pierna_izquierda", 32696007: "pierna_derecha", 368208006: "brazo_izquierdo",
         368209003: "brazo_derecho", 12921003: "pelvis", 22943007: "tronco", 69536005: "cabeza"}

RX = re.compile(rb'"dateTime": "([^"]+)", "value": \{"bpm": (\d+), "confidence": (\d)\}')

def pulso_diario(p):
    f = glob.glob(f"{BASE}/{p}/heart_rate*.json")[0]
    m = RX.findall(open(f, "rb").read())
    d = pd.DataFrame({"t": pd.to_datetime([x[0].decode() for x in m]),
                      "bpm": np.fromiter((int(x[1]) for x in m), float),
                      "c": np.fromiter((int(x[2]) for x in m), int)})
    d = d[d.c > 0].sort_values("t")
    d["seg"] = d.t.diff().shift(-1).dt.total_seconds().clip(upper=30).fillna(5)  # duracion de cada muestra
    d["dia"], h = d.t.dt.strftime("%Y-%m-%d"), d.t.dt.hour
    d["alto"] = d.seg * (d.bpm > 120)
    g = d.groupby("dia")
    r = pd.DataFrame({"horas_reloj": g.seg.sum() / 3600, "carga_cardiaca": g.alto.sum() / 60})
    # Recuperacion: mediana de las medias horarias - minimo sostenido 3 h seguidas.
    # No usa horas fijas de reloj porque el ritmo se desplaza si el tripulante cambia de huso/turno.
    d["hora"] = d.t.dt.floor("h")
    hh = d.assign(w=d.bpm * d.seg).groupby("hora").agg(w=("w", "sum"), seg=("seg", "sum"))
    hh = (hh.w / hh.seg).where(hh.seg >= 1200).resample("h").asfreq()          # hora valida: >= 20 min de datos
    min3 = hh.rolling(3, min_periods=3).mean()
    porDia = pd.DataFrame({"m": hh, "min3": min3[min3.index.hour >= 2]})         # ventana de 3 h dentro del dia
    gd = porDia.groupby(porDia.index.strftime("%Y-%m-%d"))
    r["recuperacion_nocturna"] = (gd.m.median() - gd.min3.min()).where(gd.m.count() >= 18)
    r.loc[r.horas_reloj < 6, "carga_cardiaca"] = np.nan                  # dia con poco uso del reloj
    return r.drop(columns="horas_reloj")

def leer(p):
    s = pd.read_csv(f"{BASE}/{p}/sleep_score.csv")
    s["dia"] = s.timestamp.str[:10]
    s = s.groupby("dia").agg(sueno_profundo=("deep_sleep_in_minutes", "mean"),
                             inquietud=("restlessness", lambda x: 100 * x.mean()))
    w = pd.read_csv(f"{BASE}/{p}/wellness.csv")
    w["dia"] = w.effective_time_frame.str[:10]
    sin_dato = (w[["fatigue", "mood", "stress", "soreness", "sleep_quality"]] == 0).all(axis=1)  # registro vacio
    w = w[~sin_dato]
    for c in ["soreness", "sleep_duration_h", "readiness"]:   # 0 = sin dato
        w[c] = w[c].where(w[c] > 0)
    w["zonas"] = w.soreness_area.apply(ast.literal_eval)
    w = w.groupby("dia").agg(horas_sueno=("sleep_duration_h", "mean"), disposicion=("readiness", "mean"),
                             dolor=("soreness", "mean"), zonas=("zonas", lambda x: sorted({z for l in x for z in l})))
    d = pulso_diario(p).join(s, how="outer").join(w, how="outer").sort_index()
    d = d[d.index <= FIN]
    d.insert(0, "astronauta", p)
    return d.reset_index(names="dia")

datos = pd.concat([leer(p) for p in PERS], ignore_index=True)
datos.drop(columns="zonas").round(2).to_csv(f"{OUT}/kpi_diarios.csv", index=False)

def racha(x):
    r, k = [], 0
    for v in x:
        k = k + 1 if v else 0; r.append(k)
    return np.array(r)

filas, limites = [], []
for (p, var), (nombre, unidad, zona, lado, piso, usa_racha, accion) in [((p, v), INFO[v]) for p in PERS for v in INFO]:
    g = datos[(datos.astronauta == p) & datos[var].notna()].reset_index(drop=True)
    if g.empty: continue
    v = g[var].to_numpy(); base = v[:NB]
    media, sigma = base.mean(), max(base.std(ddof=1), piso)
    li, ls = media - 3 * sigma, media + 3 * sigma
    if var != "recuperacion_nocturna": li = max(li, 0.0)   # no hay minutos, horas ni % negativos
    if var == "disposicion": ls = min(ls, 10.0)
    if var == "dolor": li, ls = 1.5, 5.0            # escala fija: 3 = normal, 1-2 = con dolor
    mon = np.arange(len(v)) >= NB
    fuera = (v > ls) if lado == "alto" else (v < li)
    desfav = mon & ((v > media) if lado == "alto" else (v < media))
    estado = np.where(mon & fuera, "alerta", np.where(usa_racha & (racha(desfav) >= 5), "vigilancia", "normal"))
    if var == "dolor":
        estado = np.where(mon & (v <= 1), "alerta", np.where(mon & (v <= 2), "vigilancia", "normal"))
    limites.append(dict(astronauta=p, variable=var, media=round(media, 2), sigma=round(sigma, 2),
                        limite_inferior=round(li, 2), limite_superior=round(ls, 2), dias_base=int(min(NB, len(v)))))
    for i, row in g.iterrows():
        e = estado[i]
        acc = "" if e == "normal" else (ACC_DOLOR[e] if var == "dolor" else accion if e == "alerta" else ACC_RACHA)
        f = dict(astronauta=p, dia=row.dia, variable=var, nombre=nombre, unidad=unidad, valor=round(float(v[i]), 2),
                 media=round(media, 2), limite_inferior=round(li, 2), limite_superior=round(ls, 2),
                 fase="monitoreo" if mon[i] else "linea_base", estado=e,
                 direccion="" if e == "normal" else lado, zona_cuerpo=zona, accion=acc)
        if var == "dolor":
            f["zonas_dolor"] = [ZONAS.get(z, str(z)) for z in row.zonas]
        filas.append(f)

orig = json.load(open(f"{BASE}/entrega/alertas.json", encoding="utf-8-sig"))

# Correccion de las escalas 1-5 (animo, estres, fatiga): con media - 3 sigma el limite inferior podia quedar
# por debajo de 1, el minimo de la escala, y la alerta era imposible. Se fija un piso de 1,5: marcar 1
# (el peor valor posible) siempre es alerta en fase de monitoreo.
ACC_ESCALA = {v: next((f["accion"] for f in orig if f["variable"] == v and f["estado"] == "alerta"), "") for v in ("animo", "estres", "fatiga")}
ACC_ESCALA["estres"] = ACC_ESCALA["estres"] or "Más estrés de lo habitual en ti. Haz una pausa, usa una técnica de respiración y revisa la carga de trabajo del día con el equipo. Si continúa, solicita la conferencia privada de apoyo psicológico."
corregidas = 0
for f in orig:
    if f["variable"] in ACC_ESCALA and f["limite_inferior"] < 1.5:
        f["limite_inferior"] = 1.5
        if f["fase"] == "monitoreo" and f["valor"] < 1.5 and f["estado"] != "alerta":
            f.update(estado="alerta", direccion="bajo", accion=ACC_ESCALA[f["variable"]]); corregidas += 1
print("alertas nuevas por la correccion de escalas:", corregidas)
todo = orig + filas
orden = {v: i for i, v in enumerate(["pulso_reposo", "sueno", "animo", "estres", "fatiga"] + list(INFO))}
todo.sort(key=lambda f: (f["astronauta"], f["dia"], orden[f["variable"]]))
json.dump(todo, open(f"{OUT}/alertas_v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
t = pd.DataFrame(todo); t["zonas_dolor"] = t.zonas_dolor.apply(lambda z: "|".join(z) if isinstance(z, list) else "")
t.to_csv(f"{OUT}/alertas_v2.csv", index=False, encoding="utf-8-sig")
lo = pd.read_csv(f"{BASE}/entrega/limites.csv")
esc15 = lo.variable.isin(list(ACC_ESCALA)) & (lo.limite_inferior < 1.5)
lo.loc[esc15, "limite_inferior"] = 1.5
pd.concat([lo, pd.DataFrame(limites)]).to_csv(f"{OUT}/limites_v2.csv", index=False)

n = pd.DataFrame(filas)
print(len(orig), "originales +", len(n), "nuevas =", len(todo))
print(pd.crosstab(n.variable, n.estado))
print(pd.crosstab([n.astronauta, n.variable], n.estado).to_string())
print(pd.DataFrame(limites).to_string())
