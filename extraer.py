# /// script
# requires-python = ">=3.11"
# ///
"""Descarga el Anuario Estadístico de Educación Superior de ANUIES a CSV.

Uso:
    uv run extraer.py                 # los 26 ciclos
    uv run extraer.py 2024-2025 ...   # solo los ciclos indicados

Un CSV por ciclo en data/, con las 6 variables y su desglose por sexo,
a nivel programa (carrera) por escuela. Si un CSV ya existe, se salta.
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

URL = "https://anuario.anuies.mx/index.php"
CICLOS = [f"{a}-{a + 1}" for a in range(2025, 1999, -1)]
VARIABLES = ["MATRÍCULA", "NUEVO INGRESO (NI)", "SOLICITUDES NI",
             "LUGARES OFERTADOS", "EGRESADOS", "TITULADOS"]
PAGINA = 3000
PAUSA = 1.5  # segundos entre peticiones
DATA = Path(__file__).parent / "data"

# Dimensiones que el sitio deja activar; todas encendidas = nivel programa por escuela.
FILTROS = {
    "includeEnts": "1", "entMode": "all",
    "includeMuns": "1", "munMode": "all",
    "includeSos": "1", "includeAnuies": "1",
    "includeSub": "1", "subMode": "all",
    "includeInstitucion": "1", "includeEscuela": "1",
    "includeNivel": "1", "includeModalidad": "1",
    "includePrograma": "1", "includeCampoAmplio": "1",
    "includeStem": "0",
    "desagSexo": "1", "desagEdad": "0", "desagDiscapacidad": "0",
    "desagHLI": "0", "desagProcedencia": "0",
}


def pedir(ciclo: str, pagina: int) -> dict:
    campos = [("action", "consulta"), ("ciclo", ciclo), *FILTROS.items(),
              *(("vars[]", v) for v in VARIABLES),
              ("page", str(pagina)), ("pageSize", str(PAGINA)), ("maxRows", str(PAGINA))]
    req = urllib.request.Request(URL, data=urllib.parse.urlencode(campos).encode(),
                                 headers={"User-Agent": "anuies-extractor (uso académico)"})
    for intento in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.load(r)
            if not d.get("ok"):
                raise RuntimeError(d)
            return d
        except Exception as e:
            if intento == 2:
                raise
            espera = 10 * (intento + 1)
            print(f"  error ({e}); reintento en {espera}s", flush=True)
            time.sleep(espera)


def extraer(ciclo: str) -> None:
    destino = DATA / f"anuies_{ciclo}.csv"
    if destino.exists():
        print(f"{ciclo}: ya existe, se salta")
        return
    parcial = destino.with_suffix(".part")
    pagina, total = 1, 0
    with parcial.open("w", newline="", encoding="utf-8") as f:
        escritor = None
        while True:
            d = pedir(ciclo, pagina)
            if escritor is None:
                columnas = ["CICLO", *d["dims"], *(c["key"] for c in d["cols"])]
                escritor = csv.DictWriter(f, columnas, extrasaction="ignore")
                escritor.writeheader()
            for fila in d["rows"]:
                escritor.writerow({"CICLO": ciclo, **fila})
            total += len(d["rows"])
            print(f"{ciclo}: página {pagina}, {total} filas", flush=True)
            if not d["meta"].get("hasMore"):
                break
            pagina += 1
            time.sleep(PAUSA)
    parcial.replace(destino)  # solo queda el CSV si el ciclo terminó completo


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    for ciclo in sys.argv[1:] or CICLOS:
        extraer(ciclo)
        time.sleep(PAUSA)
