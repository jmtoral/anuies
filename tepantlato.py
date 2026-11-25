# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "matplotlib"]
# ///
"""Caso de uso: evolución de la Universidad Tepantlato en el anuario ANUIES.

Requiere haber corrido antes `uv run extraer.py`. Uso: uv run tepantlato.py
Escribe CSV y gráficas en casos/tepantlato/.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).parent
SALIDA = RAIZ / "casos" / "tepantlato"
NOMBRE = "TEPANTLATO"
NUM = ["M_M", "M_H", "MAT_TOTAL", "NI_M", "NI_H", "NI", "SNI_M", "SNI_H", "SNI",
       "LO_REAL", "E_M", "E_H", "E", "T_M", "T_H", "T"]

partes = []
for csv in sorted((RAIZ / "data").glob("anuies_*.csv")):
    df = pd.read_csv(csv, dtype=str)
    partes.append(df[df["NOMBRE_INSTITUCION"].str.contains(NOMBRE, case=False, na=False)])
filas = pd.concat(partes, ignore_index=True)
for c in NUM:
    filas[c] = pd.to_numeric(filas.get(c), errors="coerce")
assert len(filas), "No hay filas de Tepantlato: ¿corriste extraer.py?"

SALIDA.mkdir(parents=True, exist_ok=True)
filas.to_csv(SALIDA / "tepantlato.csv", index=False)

# Resumen por ciclo
r = filas.groupby("CICLO")[NUM].sum(min_count=1).sort_index()
r["PCT_MUJERES_MAT"] = 100 * r["M_M"] / (r["M_M"] + r["M_H"])
r["TASA_TITULACION"] = 100 * r["T"] / r["E"]
r["PROGRAMAS"] = filas[filas["MAT_TOTAL"] > 0].groupby("CICLO")["CARRERA"].nunique()
r.round(1).to_csv(SALIDA / "resumen_por_ciclo.csv")

# Programas que abren (primer ciclo con matrícula) y cierran (último ciclo con matrícula)
activos = filas[filas["MAT_TOTAL"] > 0]
vida = (activos.groupby(["NIVEL", "CARRERA"])["CICLO"].agg(["min", "max"])
        .rename(columns={"min": "PRIMER_CICLO", "max": "ULTIMO_CICLO"}).sort_values("PRIMER_CICLO"))
vida.to_csv(SALIDA / "programas.csv")

# Matrícula por nivel
por_nivel = filas.pivot_table(index="CICLO", columns="NIVEL", values="MAT_TOTAL", aggfunc="sum")
por_nivel.to_csv(SALIDA / "matricula_por_nivel.csv")

# Gráficas
ax = r[["MAT_TOTAL", "NI", "E", "T"]].rename(columns={
    "MAT_TOTAL": "Matrícula", "NI": "Nuevo ingreso", "E": "Egresados", "T": "Titulados"}).plot(marker="o", figsize=(10, 5))
ax.set(title="Universidad Tepantlato: evolución por ciclo", xlabel="", ylabel="Personas")
ax.tick_params(axis="x", rotation=45)
plt.tight_layout(); plt.savefig(SALIDA / "evolucion.png", dpi=120); plt.close()

ax = por_nivel.plot.area(figsize=(10, 5))
ax.set(title="Universidad Tepantlato: matrícula por nivel", xlabel="", ylabel="Matrícula")
ax.tick_params(axis="x", rotation=45)
plt.tight_layout(); plt.savefig(SALIDA / "matricula_por_nivel.png", dpi=120); plt.close()

ax = r[["PCT_MUJERES_MAT", "TASA_TITULACION"]].rename(columns={
    "PCT_MUJERES_MAT": "% mujeres en matrícula", "TASA_TITULACION": "Titulados / egresados (%)"}).plot(marker="o", figsize=(10, 5))
ax.set(title="Universidad Tepantlato: composición por sexo y titulación", xlabel="", ylabel="%")
ax.tick_params(axis="x", rotation=45)
plt.tight_layout(); plt.savefig(SALIDA / "sexo_titulacion.png", dpi=120); plt.close()

ax = r[["SNI", "LO_REAL", "NI"]].rename(columns={
    "SNI": "Solicitudes", "LO_REAL": "Lugares ofertados", "NI": "Nuevo ingreso"}).plot(marker="o", figsize=(10, 5))
ax.set(title="Universidad Tepantlato: demanda contra admisión", xlabel="", ylabel="Personas")
ax.tick_params(axis="x", rotation=45)
plt.tight_layout(); plt.savefig(SALIDA / "demanda.png", dpi=120); plt.close()

pd.set_option("display.width", 200, "display.max_columns", 30, "display.max_rows", 200)
print(r[["MAT_TOTAL", "NI", "SNI", "LO_REAL", "E", "T", "PCT_MUJERES_MAT", "TASA_TITULACION", "PROGRAMAS"]].round(1))
print(filas.groupby(["ENTIDAD", "MUNICIPIO_CORREGIDO", "NOMBRE_DE_ESCUELA_CAMPUS_FACULTAD"]).size())
print(por_nivel)
print(vida.to_string())
