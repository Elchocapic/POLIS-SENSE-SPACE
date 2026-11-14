"""Construye astronaut_health.db (SQLite) + exportaciones JSON/CSV/TS.

    python data/salud-espacial/build_db.py                # base + JSON + CSV
    python data/salud-espacial/build_db.py --ts ruta.ts   # ademas, un modulo TypeScript tipado

Escribe astronaut_health.db, astronaut_health.json y csv/<tabla>.csv en esta misma carpeta.

Todos los valores vienen de estudios publicados (tabla `fuentes`).
Los campos marcados como 'supuesto' en parametros_simulacion NO son medidos.
"""
import argparse, csv, json, sqlite3, pathlib

parser = argparse.ArgumentParser(description="Genera la base de datos de efectos del vuelo espacial")
parser.add_argument("--ts", type=pathlib.Path, help="ruta donde escribir un modulo TypeScript tipado (opcional)")
args = parser.parse_args()

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE
TS_OUT = args.ts
DB = OUT / "astronaut_health.db"
if DB.exists():
    DB.unlink()

SCHEMA = """
CREATE TABLE fuentes (
  id TEXT PRIMARY KEY,
  cita TEXT NOT NULL,
  anio INTEGER,
  tipo TEXT,                -- articulo | reporte_nasa | conferencia | nota_prensa
  n_sujetos INTEGER,
  url TEXT NOT NULL,
  evidence_id_app TEXT      -- clave equivalente en apps/web/src/domain/evidence.ts (si existe)
);
CREATE TABLE indicadores (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  sistema TEXT NOT NULL,    -- cardiovascular, termorregulacion, sueno, oseo, muscular, ...
  unidad TEXT,
  como_se_mide TEXT
);
CREATE TABLE efectos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  indicador_id TEXT NOT NULL REFERENCES indicadores(id),
  mision TEXT,              -- ISS larga duracion, Transbordador, ...
  duracion_dias TEXT,
  fase TEXT NOT NULL,       -- vuelo | post_vuelo | pre_vuelo
  valor_pre REAL,
  de_pre REAL,
  valor_vuelo REAL,
  de_vuelo REAL,
  valor_post REAL,
  de_post REAL,
  cambio REAL,              -- cambio numerico resumido (signo = direccion)
  cambio_min REAL,
  cambio_max REAL,
  cambio_unidad TEXT,       -- 'mmHg', '%', '%/mes', 'lpm', '°C', ...
  tendencia TEXT NOT NULL,  -- sube | baja | sin_cambio | variable
  dias_hasta_efecto TEXT,
  n INTEGER,
  fuente_id TEXT NOT NULL REFERENCES fuentes(id),
  hallazgo TEXT NOT NULL
);
CREATE TABLE parametros_simulacion (
  indicador_id TEXT PRIMARY KEY REFERENCES indicadores(id),
  valor_tierra REAL,
  de_entre_sujetos REAL,    -- desviacion estandar ENTRE astronautas reportada en el estudio
  valor_vuelo_objetivo REAL,
  forma TEXT,               -- escalon | gradual | lineal
  tasa_por_mes REAL,        -- para forma 'lineal' (unidad del indicador o %)
  tasa_unidad TEXT,
  dias_hasta_estable REAL,  -- para 'gradual'
  fuente_id TEXT REFERENCES fuentes(id),
  origen TEXT NOT NULL,     -- medido | supuesto
  nota TEXT
);
CREATE TABLE datasets (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  repositorio TEXT NOT NULL,
  acceso TEXT NOT NULL,     -- publico | solicitud | no_archivado
  entorno TEXT,             -- vuelo | analogo_tierra
  misiones TEXT,
  variables TEXT,
  url TEXT,
  nota TEXT
);
CREATE VIEW v_efectos AS
  SELECT e.id, i.sistema, i.nombre AS indicador, e.mision, e.duracion_dias, e.fase,
         e.valor_pre, e.valor_vuelo, e.valor_post, e.cambio, e.cambio_min, e.cambio_max,
         e.cambio_unidad, e.tendencia, e.dias_hasta_efecto, e.n, e.hallazgo,
         f.cita, f.url, f.evidence_id_app
  FROM efectos e JOIN indicadores i ON i.id = e.indicador_id JOIN fuentes f ON f.id = e.fuente_id;
"""

FUENTES = [
    # id, cita, anio, tipo, n, url, evidence_id_app
    ("norsk2015", "Norsk et al., J Physiol 593(3):573-584 (CARD, ISS)", 2015, "articulo", 8,
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC4324706/", None),
    ("aha2019", "Impact of Prolonged Spaceflight on Orthostatic Tolerance During Ambulation, and Blood Pressure Profiles in Astronauts (American Heart Association, 2019)", 2019, "articulo", 12,
     "https://neurosciencenews.com/fainting-astronauts-exercise-14528/", None),
    ("fraser2011", "Fraser, Greaves, Blaber et al., IAC-11 (CCISS, ISS 55-199 d)", 2011, "conferencia", 7,
     "https://iafastro.directory/iac/archive/browse/IAC-11/A1/2/9471/", None),
    ("hughson2012", "Hughson et al., J Appl Physiol 2012, Cardiovascular regulation during long-duration spaceflights to the ISS", 2012, "articulo", 6,
     "https://www.eurekalert.org/news-releases/850481", None),
    ("shuttle24h", "Holter y presion 24 h en astronautas del Transbordador (resumen en scite, J.B. Charles)", 1996, "articulo", None,
     "https://scite.ai/authors/john-b-charles-W8zrrg", None),
    ("hrv2013", "Holter 24 h y variabilidad de FC en 8 astronautas de la ISS (PMC3628896)", 2013, "articulo", 8,
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC3628896", None),
    ("stahn2017", "Stahn et al., Sci Rep 7:16180, Increased core body temperature in astronauts during long-duration space missions", 2017, "articulo", 11,
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC5701078", None),
    ("barger2014", "Barger et al., Lancet Neurol 13:904-912 (sueno en Transbordador e ISS)", 2014, "articulo", 85,
     "https://www.news-medical.net/news/20140810/Space-missions-affect-sleep-patterns-in-astronauts.aspx", "sleep2014"),
    ("lang2004", "Lang et al., J Bone Miner Res 19(6):1006-1012 (DXA/QCT, ISS 4-6 meses)", 2004, "articulo", 14,
     "https://pubmed.ncbi.nlm.nih.gov/15125798/", None),
    ("sibonga2013", "Sibonga, Curr Osteoporos Rep 11:92-98", 2013, "articulo", None,
     "https://springerlink.bibliotecabuap.elogim.com/content/pdf/10.1007/s11914-013-0136-5.pdf", None),
    ("nasaBoneEvidence2017", "NASA HRP Evidence Report: Risk of Bone Fracture due to Spaceflight-induced Changes to Bone", 2017, "reporte_nasa", None,
     "https://ntrs.nasa.gov/api/citations/20170004597/downloads/20170004597.pdf", "boneLoss"),
    ("trappe2009", "Trappe et al., J Appl Physiol 106(4):1159-1168 (musculo, ISS 6 meses)", 2009, "articulo", 9,
     "https://epublications.marquette.edu/bio_fac/24/", "muscle6months"),
    ("laurens2019", "Laurens et al., Front Physiol 10:321 (revision balance energetico; cita Zwart 2014 y Matsumoto 2011)", 2019, "articulo", None,
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC6449861", None),
    ("smith2005", "Smith, Zwart et al., estado nutricional tras vuelo largo en la ISS", 2005, "articulo", None,
     "https://data.zhenzhi.com/details/1/886246903", None),
    ("trudel2022", "Trudel et al., Nature Medicine 2022, Hemolysis contributes to anemia during long-duration space flight", 2022, "articulo", 14,
     "https://ohri.ca/newsroom/story/view/1428?l=en", None),
    ("crewdose2024", "Normas de dosis de radiacion para tripulantes de la ISS por agencia (PMC10919966)", 2024, "articulo", None,
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC10919966", None),
    ("cucinotta2008", "Cucinotta et al., Radiat Res 170:127-138 (dosimetria de organos, ISS)", 2008, "articulo", 19,
     "https://bioone.org/journals/radiation-research/volume-170/issue-1/RR1330.1/Physical-and-Biological-Organ-Dosimetry-Analysis-for-International-Space-Station/10.1667/RR1330.1.full", None),
    ("twins2019", "Garrett-Bakelman et al., Science 364:eaau8650 (NASA Twins Study)", 2019, "articulo", 1,
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC7580864", None),
    ("i4_2024", "Molecular and physiological changes in the SpaceX Inspiration4 civilian crew, Nature 632:1155-1164", 2024, "articulo", 4,
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC11357997", None),
    ("penn_i4", "Penn Medicine, primer estudio de una tripulacion civil (Inspiration4)", 2024, "nota_prensa", 4,
     "https://www.pennmedicine.org/news/first-study-of-civilian-space-crew-charts-course-for-research-as-commercial-flight-heats-up", None),
    # Ya presentes en evidence.ts del repo del equipo
    ("sans", "NASA clinical update on SANS, 2023; NASA-led review, 2025", 2023, "reporte_nasa", None,
     "https://ntrs.nasa.gov/citations/20220014606", "sans"),
    ("herpes2019", "Mehta, Crucian et al., Frontiers in Microbiology, 2019", 2019, "articulo", None,
     "https://public-pages-files-2025.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2019.00016/text", "herpes2019"),
    ("orthostatic", "NASA NTRS 20080043912, post-spaceflight orthostatic intolerance", 2008, "reporte_nasa", None,
     "https://ntrs.nasa.gov/citations/20080043912", "orthostatic"),
    ("jugular2019", "Marshall-Goebel et al., JAMA Network Open, 2019", 2019, "articulo", 11,
     "https://scholarlycommons.henryford.com/surgery_articles/390", "jugular2019"),
    ("co2Law2014", "Law et al., J Occup Environ Med, 2014", 2014, "articulo", None,
     "https://ohsonline.com/articles/2014/05/12/study-indicates-co2-may-cause-astronauts-headaches.aspx", "co2Law2014"),
    ("fieldTest", "NASA Field Test and Functional Task Test studies", None, "reporte_nasa", None,
     "https://www.nasa.gov/humans-in-space/walk-the-line-nasa-studies-physical-performance-after-spaceflight", "fieldTest"),
    ("exerciseLoading", "NASA NTRS 20110015001, on-orbit exercise loading", 2011, "reporte_nasa", None,
     "https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20110015001.pdf", "exerciseLoading"),
    ("nasaStd3001Radiation", "NASA-STD-3001 Vol. 1; NASA OCHMO Radiation Protection Technical Brief", None, "reporte_nasa", None,
     "https://www.nasa.gov/sites/default/files/atoms/files/radiation_protection_technical_brief_ochmo.pdf", "nasaStd3001Radiation"),
]

INDICADORES = [
    ("fc_nocturna", "Frecuencia cardiaca nocturna", "cardiovascular", "lpm", "Holter 24 h"),
    ("fc_diurna", "Frecuencia cardiaca en actividad diaria", "cardiovascular", "lpm", "Holter 24 h"),
    ("fc_24h", "Frecuencia cardiaca (24 h / reposo)", "cardiovascular", "lpm", "Holter u oscilometria"),
    ("vfc", "Variabilidad de la frecuencia cardiaca (control autonomico)", "cardiovascular", None, "Holter 24 h"),
    ("pas_24h", "Presion arterial sistolica 24 h", "cardiovascular", "mmHg", "Monitor ambulatorio latido a latido"),
    ("pad_24h", "Presion arterial diastolica 24 h", "cardiovascular", "mmHg", "Monitor ambulatorio"),
    ("pam_24h", "Presion arterial media 24 h", "cardiovascular", "mmHg", "Monitor ambulatorio braquial"),
    ("dip_nocturno_pa", "Caida nocturna de la presion arterial", "cardiovascular", "mmHg", "Monitor ambulatorio"),
    ("gasto_cardiaco", "Gasto cardiaco", "cardiovascular", "L/min", "Reinhalacion"),
    ("volumen_sistolico", "Volumen sistolico", "cardiovascular", "mL", "Reinhalacion"),
    ("resistencia_vascular", "Resistencia vascular sistemica", "cardiovascular", None, "Calculada"),
    ("baroreflejo", "Sensibilidad del baroreflejo arterial", "cardiovascular", "ms/mmHg", "Presion de dedo + ECG"),
    ("tolerancia_ortostatica", "Tolerancia ortostatica al regreso", "cardiovascular", None, "Prueba de pie / actividad diaria"),
    ("flujo_yugular", "Flujo en vena yugular interna", "cardiovascular", None, "Ecografia"),
    ("temp_central_reposo", "Temperatura corporal central en reposo", "termorregulacion", "°C", "Sensor de flujo de calor en frente (Double Sensor)"),
    ("temp_central_ejercicio", "Temperatura corporal central en ejercicio", "termorregulacion", "°C", "Sensor de flujo de calor en frente"),
    ("sueno_duracion", "Duracion del sueno", "sueno", "h/noche", "Actigrafia de muneca + diario"),
    ("sueno_noches_7h", "Noches con 7 h de sueno o mas", "sueno", "%", "Actigrafia"),
    ("sueno_medicacion", "Uso de medicacion para dormir", "sueno", "% tripulantes", "Diario"),
    ("dmo_columna", "Densidad mineral osea, columna lumbar", "oseo", "%", "DXA"),
    ("dmo_cadera", "Densidad mineral osea, cadera", "oseo", "%", "DXA"),
    ("dmo_cadera_trabecular", "Hueso trabecular de cadera (vBMD)", "oseo", "%", "QCT"),
    ("dmo_calcaneo", "Densidad mineral osea, calcaneo", "oseo", "%", "DXA"),
    ("musculo_pantorrilla_vol", "Volumen muscular de pantorrilla", "muscular", "%", "MRI"),
    ("musculo_potencia", "Potencia maxima de pantorrilla", "muscular", "%", "Dinamometria"),
    ("masa_corporal", "Masa corporal", "nutricion", "%", "Balanza de masa en vuelo"),
    ("ingesta_energia", "Ingesta energetica respecto a la recomendada", "nutricion", "%", "Registro de dieta"),
    ("ejercicio_carga", "Tiempo de ejercicio con carga", "actividad", "min/dia", "Registros de equipos"),
    ("volumen_plasmatico", "Volumen plasmatico", "sangre", "%", "Calculado"),
    ("hemolisis", "Destruccion de globulos rojos", "sangre", "%", "CO exhalado"),
    ("anemia_aterrizaje", "Anemia al aterrizar", "sangre", "tripulantes", "Hemograma"),
    ("radiacion_tasa", "Dosis efectiva diaria", "radiacion", "mSv/dia", "Dosimetro personal"),
    ("radiacion_mision", "Dosis efectiva por mision de 6 meses", "radiacion", "mSv", "Dosimetria + modelos"),
    ("radiacion_limite", "Limite de carrera NASA", "radiacion", "mSv", "Norma"),
    ("sans", "Sindrome neuro-ocular asociado al vuelo (SANS)", "vision", "% tripulantes", "Examen oftalmologico/OCT"),
    ("herpes_reactivacion", "Reactivacion de herpesvirus", "inmune", "% tripulantes", "Saliva/orina"),
    ("co2_cefalea", "Cefalea asociada a CO2 de cabina", "ambiente", "odds ratio por mmHg", "Sensores de cabina + reportes"),
    ("funcion_sensoriomotora", "Desempeno funcional/sensoriomotor al aterrizar", "sensoriomotor", "%", "Field Test"),
    ("masa_corporal_twins", "Cambios multisistema (Twins Study)", "multisistema", None, "Multiomica + fisiologia"),
]

# (indicador, mision, duracion, fase, pre, de_pre, vuelo, de_vuelo, post, de_post,
#  cambio, cmin, cmax, unidad, tendencia, dias_efecto, n, fuente, hallazgo)
E = []
def ef(ind, mision, dur, fase, fuente, tendencia, hallazgo, pre=None, de_pre=None, vuelo=None, de_vuelo=None,
       post=None, de_post=None, cambio=None, cmin=None, cmax=None, unidad=None, dias=None, n=None):
    E.append((ind, mision, dur, fase, pre, de_pre, vuelo, de_vuelo, post, de_post, cambio, cmin, cmax,
              unidad, tendencia, dias, n, fuente, hallazgo))

ISS = "ISS larga duracion"
ef("fc_nocturna", ISS, "55-199", "vuelo", "fraser2011", "sin_cambio",
   "FC nocturna igual que en Tierra (55,5±7 vs 55,7±8 lpm en vuelo).", pre=55.5, de_pre=7, vuelo=55.7, de_vuelo=8,
   cambio=0.2, unidad="lpm", n=7)
ef("fc_diurna", ISS, "55-199", "pre_vuelo", "fraser2011", "sin_cambio",
   "FC en actividad diaria en Tierra: manana 71,0±13, tarde 71,5±9, noche 72,8±10 lpm (referencia pre-vuelo).",
   pre=71.0, de_pre=13, unidad="lpm", n=7)
ef("fc_24h", ISS, "85-192", "vuelo", "norsk2015", "sin_cambio",
   "FC y catecolaminas sin cambio durante meses en la ISS.", n=8)
ef("fc_24h", ISS, "52-199", "vuelo", "hughson2012", "sin_cambio",
   "FC, presion y baroreflejo sin cambio de pre-vuelo a vuelo.", n=6)
ef("fc_24h", ISS, "52-199", "post_vuelo", "hughson2012", "sube",
   "Tras el vuelo la FC y el gasto cardiaco suben ligeramente.", n=6)
ef("fc_24h", "Transbordador", "corta", "vuelo", "shuttle24h", "baja",
   "En vuelos cortos bajan FC, presion diastolica, su variabilidad y las extrasistoles ventriculares.")
ef("fc_24h", "Inspiration4", "3", "vuelo", "penn_i4", "baja",
   "Cambios cardiovasculares modestos: el corazon late mas lento en microgravedad.", n=4)
ef("vfc", ISS, "corta y larga", "post_vuelo", "hrv2013", "variable",
   "5 dias tras el regreso la regulacion autonomica de la FC sigue alterada; al mes se recupera casi por completo.",
   dias="5-30 post", n=8)
ef("pas_24h", ISS, "~180", "vuelo", "aha2019", "baja",
   "PAS 24 h: 120±10 antes, 106±9 en vuelo, 122±13 al aterrizar.", pre=120, de_pre=10, vuelo=106, de_vuelo=9,
   post=122, de_post=13, cambio=-14, unidad="mmHg", n=12)
ef("pad_24h", ISS, "~180", "vuelo", "aha2019", "sin_cambio",
   "PAD sin cambio durante ni despues del vuelo.", n=12)
ef("pam_24h", ISS, "85-192", "vuelo", "norsk2015", "baja",
   "Presion ambulatoria 24 h baja 8-10 mmHg por caida de 39% en la resistencia vascular sistemica.",
   cambio=-9, cmin=-10, cmax=-8, unidad="mmHg", n=8)
ef("dip_nocturno_pa", ISS, "85-192", "vuelo", "norsk2015", "sin_cambio",
   "La caida nocturna de presion (8±3 mmHg) se mantiene en el espacio.", vuelo=8, de_vuelo=3, unidad="mmHg", n=8)
ef("resistencia_vascular", ISS, "85-192", "vuelo", "norsk2015", "baja",
   "Resistencia vascular sistemica -39%.", cambio=-39, unidad="%", n=8)
ef("volumen_sistolico", ISS, "85-192", "vuelo", "norsk2015", "sube",
   "Volumen sistolico +35±10%.", cambio=35, cmin=25, cmax=45, unidad="%", n=8)
ef("gasto_cardiaco", ISS, "85-192", "vuelo", "norsk2015", "sube",
   "Gasto cardiaco +41±9%.", cambio=41, cmin=32, cmax=50, unidad="%", n=8)
ef("baroreflejo", ISS, "52-199", "post_vuelo", "hughson2012", "baja",
   "Respuesta del baroreflejo cae ~1/3 tras el vuelo, solo sentado.", cambio=-33, unidad="%", n=6)
ef("tolerancia_ortostatica", ISS, "~180", "post_vuelo", "aha2019", "sin_cambio",
   "Con ejercicio en vuelo y fluidos IV al aterrizar, ninguno tuvo hipotension ortostatica en actividades diarias.", n=12)
ef("tolerancia_ortostatica", "Transbordador", "corta", "post_vuelo", "orthostatic", "baja",
   "Hipotension y presincope en 20-30% de astronautas al regresar.", cmin=20, cmax=30, unidad="% tripulantes")
ef("flujo_yugular", ISS, "~50", "vuelo", "jugular2019", "variable",
   "6 de 11 tripulantes con flujo yugular estancado o invertido ~dia 50; uno con trombo.", dias="~50", n=11)
ef("temp_central_reposo", ISS, "larga", "vuelo", "stahn2017", "sube",
   "Aumento de ~1 °C en reposo que se desarrolla gradualmente en 2,5 meses, hasta ~38 °C; ligado a IL-1ra.",
   pre=37.0, vuelo=38.0, cambio=1.0, unidad="°C", dias="~75", n=11)
ef("temp_central_ejercicio", ISS, "larga", "vuelo", "stahn2017", "sube",
   "En ejercicio la temperatura central sube mas y mas rapido que en Tierra; a menudo supera 40 °C.",
   vuelo=40.0, unidad="°C", n=11)
ef("sueno_duracion", "ISS", "larga", "vuelo", "barger2014", "baja",
   "Promedio 6,09 h/noche en la ISS (5,96 en Transbordador) aunque se programan 8,5 h.",
   vuelo=6.09, cambio=-2.41, unidad="h vs programado", n=21)
ef("sueno_duracion", "Entrenamiento", "~90 d antes", "pre_vuelo", "barger2014", "baja",
   "~3 meses antes del vuelo ya dormian menos de 6,5 h/noche.", pre=6.5, unidad="h", n=85)
ef("sueno_noches_7h", "ISS", "larga", "vuelo", "barger2014", "baja",
   "24% de noches con >=7 h en la ISS (12% en Transbordador) vs 50% y 42% tras la mision.",
   vuelo=24, post=50, unidad="%", n=21)
ef("sueno_medicacion", "ISS", "larga", "vuelo", "barger2014", "sube",
   "75% de tripulantes de la ISS y 78% del Transbordador usaron somniferos en algun momento.",
   vuelo=75, unidad="% tripulantes", n=85)
ef("dmo_columna", ISS, "120-180", "vuelo", "lang2004", "baja",
   "aBMD columna -0,9%/mes.", cambio=-0.9, unidad="%/mes", n=14)
ef("dmo_cadera", ISS, "120-180", "vuelo", "lang2004", "baja",
   "aBMD cadera -1,4 a -1,5%/mes.", cambio=-1.45, cmin=-1.5, cmax=-1.4, unidad="%/mes", n=14)
ef("dmo_cadera_trabecular", ISS, "120-180", "vuelo", "lang2004", "baja",
   "vBMD trabecular de cadera -2,2 a -2,7%/mes.", cambio=-2.45, cmin=-2.7, cmax=-2.2, unidad="%/mes", n=14)
ef("dmo_calcaneo", ISS, "120-180", "vuelo", "lang2004", "baja",
   "Calcaneo -0,4%/mes.", cambio=-0.4, unidad="%/mes", n=14)
ef("dmo_cadera", ISS, "~180", "post_vuelo", "nasaBoneEvidence2017", "baja",
   "Perdida promedio de 1-1,5%/mes en sitios de carga; gran variacion entre sitios y tripulantes.",
   cambio=-1.25, cmin=-1.5, cmax=-1.0, unidad="%/mes")
ef("dmo_cadera", ISS, "~180", "post_vuelo", "sibonga2013", "baja",
   "Algunos astronautas pierden >10% en cadera y columna tras 6 meses.", cmax=-10, unidad="%")
ef("musculo_pantorrilla_vol", ISS, "~180", "post_vuelo", "trappe2009", "baja",
   "Volumen de pantorrilla -13±2% (soleo -15%, gastrocnemio -10%).", cambio=-13, cmin=-15, cmax=-11, unidad="%", n=9)
ef("musculo_potencia", ISS, "~180", "post_vuelo", "trappe2009", "baja",
   "Potencia maxima -32% tras el vuelo.", cambio=-32, unidad="%", n=9)
ef("masa_corporal", ISS, "larga", "vuelo", "laurens2019", "baja",
   "En la ISS reciente se pierde 2-5% de la masa inicial (Zwart 2014).", cambio=-3.5, cmin=-5, cmax=-2, unidad="%")
ef("masa_corporal", "619 misiones", "varias", "vuelo", "laurens2019", "baja",
   "Modelo lineal sobre 619 misiones: -2,4% por cada 100 dias (Matsumoto 2011).", cambio=-2.4, unidad="% por 100 dias")
ef("ingesta_energia", ISS, "larga", "vuelo", "smith2005", "baja",
   "Los tripulantes consumen en promedio 80% de la energia recomendada.", vuelo=80, unidad="%")
ef("ejercicio_carga", ISS, "larga", "vuelo", "exerciseLoading", "baja",
   "Carga real promedio 43 min/dia frente a 146,8 min asignados.", vuelo=43, unidad="min/dia")
ef("volumen_plasmatico", ISS, "larga", "vuelo", "trudel2022", "baja",
   "Se pierde ~10% del liquido de los vasos sanguineos al llegar al espacio.", cambio=-10, unidad="%", dias="primeros dias")
ef("hemolisis", ISS, "~180", "vuelo", "trudel2022", "sube",
   "54% mas destruccion de globulos rojos (3 vs 2 millones/s) durante toda la mision.", cambio=54, unidad="%", n=14)
ef("hemolisis", ISS, "~180", "post_vuelo", "trudel2022", "sube",
   "Un ano despues sigue 30% sobre el nivel pre-vuelo; globulos rojos normales a los 3-4 meses.", cambio=30, unidad="%", n=14)
ef("anemia_aterrizaje", ISS, "~180", "post_vuelo", "trudel2022", "sube",
   "5 de 13 astronautas con anemia diagnosticable al aterrizar.", post=5, unidad="de 13", n=13)
ef("radiacion_tasa", "ISS", "-", "vuelo", "crewdose2024", "sube",
   "Dosis efectiva ~0,2 a ~0,5 mSv/dia o mas.", cmin=0.2, cmax=0.5, unidad="mSv/dia")
ef("radiacion_mision", "ISS", "~180", "vuelo", "cucinotta2008", "sube",
   "Dosis efectiva media de 72 mSv por mision de ~6 meses.", vuelo=72, unidad="mSv", n=19)
ef("radiacion_limite", "-", "carrera", "vuelo", "nasaStd3001Radiation", "sin_cambio",
   "Limite de carrera 600 mSv; 250 mSv por evento solar de particulas.", vuelo=600, unidad="mSv")
ef("sans", ISS, "larga", "vuelo", "sans", "sube",
   "~66% de astronautas de larga duracion muestran signos tempranos de SANS.", vuelo=66, unidad="% tripulantes")
ef("herpes_reactivacion", "ISS", "larga", "vuelo", "herpes2019", "sube",
   "61% de astronautas de la ISS eliminan herpesvirus reactivados; pocos con sintomas.", vuelo=61, unidad="% tripulantes")
ef("co2_cefalea", "ISS", "-", "vuelo", "co2Law2014", "sube",
   "Cada 1 mmHg de CO2 duplica la probabilidad de cefalea; <=4 mmHg reduce a la mitad el riesgo semanal.",
   cambio=2, unidad="odds ratio por mmHg")
ef("funcion_sensoriomotora", ISS, "larga", "post_vuelo", "fieldTest", "baja",
   "Un dia tras aterrizar el circuito funcional tarda 48% mas; deficits hasta una semana.",
   cambio=48, unidad="% mas tiempo", dias="1-7 post")
ef("masa_corporal_twins", ISS, "340", "vuelo", "twins2019", "variable",
   "Baja masa corporal, distension carotidea y mayor grosor intima-media, cambios oculares, de expresion genica y cognitivos; la mayoria vuelve a niveles pre-vuelo.",
   n=1)

# indicador, valor_tierra, de, objetivo, forma, tasa, tasa_unidad, dias_estable, fuente, origen, nota
PARAMS = [
    ("fc_nocturna", 55.5, 7, 55.7, "escalon", None, None, None, "fraser2011", "medido", "Sin cambio real; usar la linea base de cada persona."),
    ("fc_diurna", 71.0, 13, 71.0, "escalon", None, None, None, "fraser2011", "medido", "Valor en vuelo asumido igual a Tierra (Hughson 2012: FC sin cambio)."),
    ("pas_24h", 120, 10, 106, "escalon", None, None, 7, "aha2019", "medido", "dias_hasta_estable es supuesto: el desplazamiento de fluidos ocurre en los primeros dias."),
    ("pad_24h", None, None, None, "escalon", None, None, None, "aha2019", "medido", "Sin cambio: mantener la linea base."),
    ("dip_nocturno_pa", 8, 3, 8, "escalon", None, None, None, "norsk2015", "medido", "La bajada nocturna se mantiene."),
    ("temp_central_reposo", 37.0, None, 38.0, "gradual", None, None, 75, "stahn2017", "medido", "Rampa gradual ~2,5 meses; un umbral fijo de fiebre en 38 °C daria falsos positivos."),
    ("sueno_duracion", 6.5, None, 6.09, "escalon", None, None, None, "barger2014", "medido", "Valor de Tierra = periodo de entrenamiento (<6,5 h)."),
    ("dmo_columna", 0, None, None, "lineal", -0.9, "%/mes", None, "lang2004", "medido", None),
    ("dmo_cadera", 0, None, None, "lineal", -1.45, "%/mes", None, "lang2004", "medido", None),
    ("musculo_pantorrilla_vol", 0, None, -13, "lineal", -2.17, "%/mes", None, "trappe2009", "supuesto", "Solo se midio pre/post (6 meses); la tasa lineal 13%/6 es un supuesto."),
    ("masa_corporal", 0, None, None, "lineal", -0.73, "%/mes", None, "laurens2019", "medido", "Derivado de -2,4% por 100 dias (Matsumoto 2011)."),
    ("volumen_plasmatico", 0, None, -10, "escalon", None, None, 3, "trudel2022", "supuesto", "dias_hasta_estable es supuesto ('al llegar al espacio')."),
    ("radiacion_tasa", 0.35, None, None, "escalon", None, None, None, "crewdose2024", "medido", "Rango 0,2-0,5 mSv/dia; 0,35 es el punto medio."),
]

DATASETS = [
    ("osdr_i4", "Inspiration4 (SOMA): omica, clinica e inmune; datos procesados", "NASA OSDR", "publico", "vuelo",
     "Inspiration4 (3 dias, 2021)", "Sangre, orina, saliva, piel, hisopados; ECG/FC/SpO2/sueno con Apple Watch en el estudio",
     "https://www.nasa.gov/osdr-latest-news-soma-publications", "Crudos e identificables requieren solicitud aprobada."),
    ("osdr_radlab", "RadLab: tasas de dosis DOSTEL, CRaTER, MSL-RAD", "NASA OSDR", "publico", "vuelo",
     "ISS, orbita lunar, Marte", "Dosis absorbida (µGy/h)", "https://visualization.osdr.nasa.gov/radlab/", "Ya usado en la app."),
    ("nlsp_ssm_sensorimotor", "Spaceflight Standard Measures: Sensorimotor (SSM_Sensorimotor)", "NLSP / LSDA", "solicitud", "vuelo",
     "Expediciones 58-73", "FC, PA diastolica media, mareo, equilibrio, sentarse-levantarse",
     "https://nlsp.nasa.gov/explore?search=Spaceflight%20Standard%20Measures&dataType=EXPERIMENTS", "Recoleccion en curso."),
    ("nlsp_skylab", "Skylab Crew Health (skych)", "NLSP / LSDA", "solicitud", "vuelo",
     "Skylab 2, 3, 4", "Calcio, masa osea, masa magra, sueno, enfermedades, radiacion, microbiologia",
     "https://nlsp.nasa.gov/explore?search=Skylab%20Crew%20Health&dataType=EXPERIMENTS", "Parte publica y parte con privacidad."),
    ("nlsp_venoarteriolar", "Effect of Microgravity on the Peripheral Subcutaneous Veno-Arteriolar Reflex (96-E290)", "NLSP / LSDA", "solicitud", "vuelo",
     "Expediciones 3-5", "Flujo sanguineo, presion arterial, FC", "https://nlsp.nasa.gov/explore?search=96-E290&dataType=EXPERIMENTS", None),
    ("nlsp_kinematics_t2", "Biomechanical Analysis of Treadmill Exercise on the ISS (Kinematics_T2)", "NLSP / LSDA", "solicitud", "vuelo",
     "Expediciones 27-32", "FC, fuerza de reaccion, carga externa, velocidad", "https://nlsp.nasa.gov/explore?search=Kinematics_T2&dataType=EXPERIMENTS", None),
    ("nlsp_inflight_loading", "Retrospective Analysis of Inflight Exercise Loading and Health Outcomes", "NLSP / LSDA", "solicitud", "vuelo",
     "ISS", "aBMD cadera/columna, fuerza muscular, cinta: distancia, tiempo, carga", "https://nlsp.nasa.gov/explore?search=Inflight_Loading&dataType=EXPERIMENTS", None),
    ("nlsp_wearable_hera", "Wearable Biosensor Monitor to Support Autonomous Crew Health (HERA C3)", "NLSP / LSDA", "solicitud", "analogo_tierra",
     "HERA Campaign 3", "PA, FC, SpO2, frecuencia respiratoria, temperatura de piel, actividad, carga de trabajo",
     "https://nlsp.nasa.gov/explore?search=Wearable_Bio_Monitor&dataType=EXPERIMENTS", "El mas parecido a un monitor de signos vitales, pero en analogo terrestre."),
    ("nlsp_oawss", "On-Astronaut Wireless Sensor System Evaluation (OAWSS)", "NLSP / LSDA", "solicitud", "analogo_tierra",
     "Tierra", "ECG, FC, frecuencia respiratoria, temperatura de piel, respuesta galvanica, sueno, animo",
     "https://nlsp.nasa.gov/explore?search=OAWSS_Evaluation&dataType=EXPERIMENTS", None),
    ("nlsp_lsah", "Longitudinal Study of Astronaut Health (LSAH)", "NLSP / LSDA", "solicitud", "vuelo",
     "Todas", "Salud clinica de largo plazo", "https://nlsp.nasa.gov/explore?search=LSAH&dataType=EXPERIMENTS", "Recoleccion en curso."),
    ("nlsp_24h_bp_hr", "24-Hour Pattern of Blood Pressure and Heart Rate", "NLSP", "no_archivado", "vuelo",
     "Expediciones 8-9", "PA y FC 24 h", "https://nlsp.nasa.gov/explore?search=24-Hour%20Pattern%20of%20Blood%20Pressure&dataType=EXPERIMENTS",
     "Estudio internacional que no archivo datos en LSDA."),
]

con = sqlite3.connect(DB)
con.executescript(SCHEMA)
con.executemany("INSERT INTO fuentes VALUES (?,?,?,?,?,?,?)", FUENTES)
con.executemany("INSERT INTO indicadores VALUES (?,?,?,?,?)", INDICADORES)
con.executemany("""INSERT INTO efectos (indicador_id, mision, duracion_dias, fase, valor_pre, de_pre, valor_vuelo, de_vuelo,
  valor_post, de_post, cambio, cambio_min, cambio_max, cambio_unidad, tendencia, dias_hasta_efecto, n, fuente_id, hallazgo)
  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", E)
con.executemany("INSERT INTO parametros_simulacion VALUES (?,?,?,?,?,?,?,?,?,?,?)", PARAMS)
con.executemany("INSERT INTO datasets VALUES (?,?,?,?,?,?,?,?,?)", DATASETS)
con.commit()

# Exportaciones
con.row_factory = sqlite3.Row
tables = ["fuentes", "indicadores", "efectos", "parametros_simulacion", "datasets", "v_efectos"]
data = {t: [dict(r) for r in con.execute(f"SELECT * FROM {t}")] for t in tables}
(OUT / "astronaut_health.json").write_text(json.dumps({k: v for k, v in data.items() if k != "v_efectos"}, ensure_ascii=False, indent=2), encoding="utf-8")

CSV_DIR = OUT / "csv"
CSV_DIR.mkdir(exist_ok=True)
for t in tables:
    rows = data[t]
    with (CSV_DIR / f"{t}.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

# Modulo TypeScript para apps/web (tipado; no editar a mano)
TS_TYPES = {
    "fuentes": ("Fuente", "FUENTES"),
    "indicadores": ("Indicador", "INDICADORES"),
    "efectos": ("Efecto", "EFECTOS"),
    "parametros_simulacion": ("ParametroSimulacion", "PARAMETROS_SIMULACION"),
    "datasets": ("Dataset", "DATASETS"),
}

def ts_type(table: str) -> str:
    cols = con.execute(f"PRAGMA table_info({table})").fetchall()
    lines = []
    for c in cols:
        name, typ, notnull, pk = c[1], c[2].upper(), c[3], c[5]
        base = "number" if typ in ("INTEGER", "REAL") else "string"
        nullable = not (notnull or pk)
        lines.append(f"  {name}: {base}{' | null' if nullable else ''}")
    return "\n".join(lines)

ts = [
    "// GENERADO por data/salud-espacial/build_db.py: no editar a mano, edita el script y vuelve a ejecutarlo.",
    "// Valores de estudios publicados (ver FUENTES). En PARAMETROS_SIMULACION, origen 'supuesto' = no medido.",
    "",
]
for t, (typ, const) in TS_TYPES.items():
    ts.append(f"export interface {typ} {{\n{ts_type(t)}\n}}\n")
for t, (typ, const) in TS_TYPES.items():
    ts.append(f"export const {const}: readonly {typ}[] = {json.dumps(data[t], ensure_ascii=False, indent=2)}\n")
ts.append('''/**
 * Valor esperado de un indicador `dia` dias despues del lanzamiento, a partir de la linea base personal.
 * - lineal: la tasa_por_mes es un % de la linea base.
 * - escalon / gradual: se suma (valor_vuelo_objetivo - valor_tierra), de golpe o repartido en dias_hasta_estable.
 */
export function valorEsperado(indicadorId: string, lineaBase: number, dia: number): number {
  const p = PARAMETROS_SIMULACION.find((x) => x.indicador_id === indicadorId)
  if (!p) return lineaBase
  if (p.forma === 'lineal') return p.tasa_por_mes == null ? lineaBase : lineaBase * (1 + (p.tasa_por_mes / 100) * (dia / 30.44))
  if (p.valor_tierra == null || p.valor_vuelo_objetivo == null) return lineaBase
  const delta = p.valor_vuelo_objetivo - p.valor_tierra
  const dias = p.dias_hasta_estable ?? 0
  const frac = dias > 0 ? Math.min(Math.max(dia, 0) / dias, 1) : 1
  return lineaBase + delta * frac
}
''')
if TS_OUT:
    TS_OUT.parent.mkdir(parents=True, exist_ok=True)
    TS_OUT.write_text("\n".join(ts), encoding="utf-8")
    print("modulo TypeScript:", TS_OUT)

for t in tables[:-1]:
    print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
con.close()
