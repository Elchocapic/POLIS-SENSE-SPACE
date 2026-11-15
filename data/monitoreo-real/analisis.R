# Monitoreo de salud de astronautas - linea base personal y alertas
# Entrada: carpeta NASA con P01..P05 (sleep_score.csv y wellness.csv)
# Salida:  alertas.json, alertas.csv, limites.csv, anova
library(dplyr); library(tidyr); library(jsonlite)

base     <- "C:/Users/Usuario/OneDrive/Desktop/NASA"
personas <- c("P01", "P02", "P03", "P04", "P05")
NB       <- 21   # dias de linea base

# 1. Unir: una fila por persona y dia -------------------------------------
leer <- function(p) {
  s <- read.csv(file.path(base, p, "sleep_score.csv")) |>
    mutate(dia = as.Date(substr(timestamp, 1, 10))) |>
    group_by(dia) |>
    summarise(pulso_reposo = mean(resting_heart_rate), sueno = mean(overall_score))
  w <- read.csv(file.path(base, p, "wellness.csv")) |>
    mutate(dia = as.Date(substr(effective_time_frame, 1, 10)),
           across(c(mood, stress, fatigue), ~ ifelse(.x > 0, .x, NA))) |>  # 0 = sin dato
    group_by(dia) |>
    summarise(animo = mean(mood, na.rm = TRUE), estres = mean(stress, na.rm = TRUE),
              fatiga = mean(fatigue, na.rm = TRUE))
  full_join(s, w, by = "dia") |> arrange(dia) |> mutate(astronauta = p)
}
datos <- bind_rows(lapply(personas, leer))

# 2. ANOVA entre personas + ICC -------------------------------------------
for (v in c("pulso_reposo", "sueno", "animo", "estres", "fatiga")) {
  a   <- anova(lm(datos[[v]] ~ datos$astronauta))
  n   <- tapply(!is.na(datos[[v]]), datos$astronauta, sum)
  n0  <- (sum(n) - sum(n^2) / sum(n)) / (length(n) - 1)
  icc <- (a$`Mean Sq`[1] - a$`Mean Sq`[2]) / (a$`Mean Sq`[1] + (n0 - 1) * a$`Mean Sq`[2])
  cat(sprintf("%-13s F = %7.1f  p = %.2g  ICC = %.2f\n", v, a$`F value`[1], a$`Pr(>F)`[1], icc))
}

# 3. Linea base y limites (media +/- 3 sigma de los primeros NB dias) -----
info <- tribble(
  ~variable,      ~nombre,                   ~zona_cuerpo, ~lado,   ~piso,
  "pulso_reposo", "Pulso en reposo",         "corazon",    "ambos", 1.0,
  "sueno",        "Calidad de sueño",        "cabeza",     "bajo",  0,
  "animo",        "Estado de ánimo",         "cabeza",     "bajo",  0.5,
  "estres",       "Estrés (5 = relajado)",   "cabeza",     "bajo",  0.5,
  "fatiga",       "Fatiga (5 = descansado)", "musculos",   "bajo",  0.5)

largo <- datos |>
  pivot_longer(-c(dia, astronauta), names_to = "variable", values_to = "valor") |>
  filter(!is.na(valor)) |>
  left_join(info, by = "variable") |>
  group_by(astronauta, variable) |>
  arrange(dia, .by_group = TRUE) |>
  mutate(n     = row_number(),
         fase  = ifelse(n <= NB, "linea_base", "monitoreo"),
         media = mean(valor[n <= NB]),
         sigma = pmax(sd(valor[n <= NB]), piso),   # piso: evita limites de ancho cero
         limite_inferior = media - 3 * sigma,
         limite_superior = media + 3 * sigma)

# 4. Estados ---------------------------------------------------------------
racha <- function(x) { r <- integer(length(x)); k <- 0L
  for (i in seq_along(x)) { k <- if (x[i]) k + 1L else 0L; r[i] <- k }; r }

alertas <- largo |>
  mutate(
    fuera_alto = valor > limite_superior & lado == "ambos",
    fuera_bajo = valor < limite_inferior,
    clinico    = variable == "pulso_reposo" & (valor < 40 | valor > 100),
    desfav     = fase == "monitoreo" & ((variable == "pulso_reposo" & valor > media) |
                                        (variable == "sueno" & valor < media)),
    estado = case_when(
      clinico                                         ~ "alerta",
      fase == "monitoreo" & (fuera_alto | fuera_bajo) ~ "alerta",
      racha(desfav) >= 5                              ~ "vigilancia",
      TRUE                                            ~ "normal")) |>
  ungroup() |>
  select(astronauta, dia, variable, nombre, valor, media, limite_inferior,
         limite_superior, fase, estado, zona_cuerpo)
# (los textos de "accion" estan en alertas.json; se unen por variable y estado)

print(table(alertas$variable, alertas$estado))
write.csv(alertas, file.path(base, "alertas_R.csv"), row.names = FALSE)
write_json(alertas, file.path(base, "alertas_R.json"), pretty = TRUE, digits = 2)
