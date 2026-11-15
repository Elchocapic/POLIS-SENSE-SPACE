"""Entrena el pronóstico del asistente: ¿qué puede salirse de lo normal mañana?

Uso:  python data/monitoreo-real/entrenar_pronostico.py
Lee alertas_v2.json y limites_v2.csv, escribe pronostico.json (coeficientes de 4 regresiones logísticas
y su validación). Cada fila es un astronauta y un día; se predice el día siguiente.
Validación: (a) hacia adelante en el tiempo (entrena con el primer 60 % de cada persona, prueba con el
resto) y (b) dejando fuera a una persona entera. Se compara con "mañana será igual que hoy".
"""
import json, pathlib
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

AQUI = pathlib.Path(__file__).resolve().parent
d = pd.DataFrame(json.loads((AQUI / "alertas_v2.json").read_text(encoding="utf-8")))
lim = pd.read_csv(AQUI / "limites_v2.csv").set_index(["astronauta", "variable"])
VARS = ["pulso_reposo", "sueno", "animo", "estres", "fatiga", "carga_cardiaca", "recuperacion_nocturna",
        "sueno_profundo", "inquietud", "horas_sueno", "disposicion", "dolor"]
SUENO = ["sueno", "horas_sueno", "sueno_profundo", "inquietud"]
dias = sorted(d.dia.unique()); pos = {x: i for i, x in enumerate(dias)}
d["i"] = d.dia.map(pos); d["e"] = d.estado.map({"normal": 0, "vigilancia": 1, "alerta": 2})
d["z"] = [(v - m) / max(lim.loc[(p, k), "sigma"], 1e-6) for p, k, v, m in zip(d.astronauta, d.variable, d.valor, d.media)]

filas = []
for p, g in d.groupby("astronauta"):
    z = g.pivot(index="i", columns="variable", values="z").reindex(range(len(dias)))
    e = g.pivot(index="i", columns="variable", values="e").reindex(range(len(dias)))
    v = g.pivot(index="i", columns="variable", values="valor").reindex(range(len(dias)))
    f = pd.DataFrame(index=z.index)
    for k in VARS:
        f["z_" + k] = z[k].clip(-4, 4).fillna(0)          # sin dato = en su media
    f["carga3"] = z["carga_cardiaca"].rolling(3, min_periods=1).max().clip(-4, 4).fillna(0)
    f["carga_ayer"] = z["carga_cardiaca"].shift(1).clip(-4, 4).fillna(0)        # el dolor muscular suele llegar 1 a 3 días después
    f["sueno3"] = z["sueno"].rolling(3, min_periods=1).mean().clip(-4, 4).fillna(0)
    f["dolor_hoy"] = (v["dolor"] <= 2).astype(float)
    f["dolor_ayer"] = f["dolor_hoy"].shift(1).fillna(0)
    f["pulso_fuera"] = (e["pulso_reposo"] > 0).astype(float)
    f["sueno_fuera"] = (e[SUENO] > 0).any(axis=1).astype(float)
    f["fatiga_baja"] = (v["fatiga"] <= 2).astype(float)
    y = pd.DataFrame({"dolor": (v["dolor"] <= 2).where(v["dolor"].notna()),
                      "pulso": (e["pulso_reposo"] > 0).where(e["pulso_reposo"].notna()),
                      "sueno": (e[SUENO] > 0).any(axis=1).where(e["sueno"].notna()),
                      "fatiga": (v["fatiga"] <= 2).where(v["fatiga"].notna())}).shift(-1)   # objetivo: mañana
    # Costumbre de cada persona, calculada solo con su pasado: con qué frecuencia le pasa, y en ese día de la semana
    sem = pd.Series([pd.Timestamp(x).dayofweek for x in dias], index=z.index)
    for obj, hoy in {"dolor": f["dolor_hoy"].where(v["dolor"].notna()), "pulso": f["pulso_fuera"].where(e["pulso_reposo"].notna()),
                     "sueno": f["sueno_fuera"].where(e["sueno"].notna()), "fatiga": f["fatiga_baja"].where(v["fatiga"].notna())}.items():
        f["tasa_" + obj] = hoy.expanding().mean().fillna(0)
        manana = sem.shift(-1).fillna((sem.iloc[-1] + 1) % 7)
        acum = {w: hoy[sem == w].expanding().mean() for w in range(7)}
        f["sem_" + obj] = [acum[int(w)].loc[:i].iloc[-1] if len(acum[int(w)].loc[:i]) and pd.notna(acum[int(w)].loc[:i].iloc[-1]) else 0.0 for i, w in zip(f.index, manana)]
    hay = z.notna().any(axis=1)
    f = f.assign(p=p, i=f.index).join(y.add_prefix("y_"))[hay.values]
    filas.append(f)
T = pd.concat(filas, ignore_index=True)
BASE = [c for c in T.columns if c not in ("p", "i") and not c.startswith(("y_", "tasa_", "sem_"))]
HOY = {"dolor": "dolor_hoy", "pulso": "pulso_fuera", "sueno": "sueno_fuera", "fatiga": "fatiga_baja"}

def auc(y, s):
    return float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else float("nan")

def ajustar(X, y):
    mu, sd = X.mean(axis=0), X.std(axis=0).replace(0, 1)
    m = LogisticRegression(C=0.3, max_iter=2000, class_weight=None).fit((X - mu) / sd, y)
    return m, mu, sd

salida = {"objetivos": {}}
for obj in HOY:
    FEAT = BASE + ["tasa_" + obj, "sem_" + obj]
    D = T[T["y_" + obj].notna()].copy(); y = D["y_" + obj].astype(int)
    # (a) hacia adelante en el tiempo, por persona
    corte = D.groupby("p").i.transform(lambda s: s.quantile(0.6)); tr, te = D.i <= corte, D.i > corte
    m, mu, sd = ajustar(D.loc[tr, FEAT], y[tr]); pt = m.predict_proba((D.loc[te, FEAT] - mu) / sd)[:, 1]
    a_t, a_t_persist = auc(y[te], pt), auc(y[te], D.loc[te, HOY[obj]])
    por_persona = {p: round(auc(y[te & (D.p == p)], pt[(D.p[te] == p).values]), 2) for p in sorted(D.p.unique())}
    # (b) dejando fuera a una persona
    lopo = np.zeros(len(D))
    for p in D.p.unique():
        m2, mu2, sd2 = ajustar(D.loc[D.p != p, FEAT], y[D.p != p]); lopo[(D.p == p).values] = m2.predict_proba((D.loc[D.p == p, FEAT] - mu2) / sd2)[:, 1]
    # acierto con umbral 0,5 en la prueba hacia adelante
    pred = pt >= 0.5; yt = y[te].values
    nuevo = (D.loc[te, HOY[obj]] == 0).values          # casos nuevos: hoy no lo tiene
    a_nuevo = auc(yt[nuevo], pt[nuevo])
    # modelo final con todo
    m, mu, sd = ajustar(D[FEAT], y)
    w = m.coef_[0] / sd.values; b = float(m.intercept_[0] - (m.coef_[0] * mu.values / sd.values).sum())
    pr_todo = m.predict_proba((D[FEAT] - mu) / sd)[:, 1]
    muestra = D.assign(pr=pr_todo).groupby("p").apply(lambda g: g.iloc[[len(g) // 3, len(g) // 2, len(g) - 2]], include_groups=False).reset_index()
    salida.setdefault("pruebas", []).extend({"obj": obj, "p": r.p, "i": int(r.i), "pr": round(float(r.pr), 4)} for r in muestra.itertuples())
    salida["objetivos"][obj] = {
        "b": round(b, 4), "w": {f: round(float(c), 4) for f, c in zip(FEAT, w)},
        "n": int(len(D)), "frecuencia": round(float(y.mean()), 3),
        "frecuencia_por_persona": {p: round(float(y[D.p == p].mean()), 3) for p in sorted(D.p.unique())},
        "auc_tiempo": round(a_t, 3), "auc_tiempo_igual_que_hoy": round(a_t_persist, 3), "auc_otra_persona": round(auc(y, lopo), 3),
        "auc_tiempo_por_persona": por_persona, "auc_casos_nuevos": round(a_nuevo, 3), "casos_nuevos": int(yt[nuevo].sum()),
        "avisos_correctos": round(float((pred & (yt == 1)).sum() / max(pred.sum(), 1)), 3), "avisos": int(pred.sum()),
        "casos_detectados": round(float((pred & (yt == 1)).sum() / max(yt.sum(), 1)), 3), "casos": int(yt.sum()), "n_prueba": int(len(yt)),
    }
(AQUI / "pronostico.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
for k, o in salida["objetivos"].items():
    print(f"{k:7s} n={o['n']} frec={o['frecuencia']:.2f}  AUC tiempo={o['auc_tiempo']:.2f} (igual que hoy {o['auc_tiempo_igual_que_hoy']:.2f})  otra persona={o['auc_otra_persona']:.2f}  avisos {o['avisos']} ({o['avisos_correctos']:.0%} correctos), detecta {o['casos_detectados']:.0%} de {o['casos']}  casos nuevos AUC {o['auc_casos_nuevos']:.2f} (n={o['casos_nuevos']})")
    top = sorted(o["w"].items(), key=lambda x: -abs(x[1]))[:6]; print("        ", top)
