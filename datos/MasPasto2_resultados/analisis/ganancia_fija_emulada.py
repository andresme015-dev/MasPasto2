"""Que pasaria con el NDVI si la ganancia fuera fija en el valor del caso de mas luz.

Toma las corridas de campo del 26 oct (nublado, 17:13-17:22) medidas a 64x y emula la lectura
a una ganancia menor g: cuentas_g = floor(cuentas_64 * g / 64). Solo modela la cuantizacion
(1 cuenta), no el ruido adicional, asi que es un caso optimista para la ganancia fija.
NDVI relativo a la cartulina (blanco1), corregido con el cenit (Ec. rho del informe).
"""
import math, sys
import numpy as np, pandas as pd

C = sys.argv[1]   # carpeta 2026-10-26_campo_uniandes/crudos
blanco = pd.read_csv(f"{C}/registro_sensorA-B_validacion_blanco1_20261026_171508.csv")
pastos = {"pasto denso 1": "registro_sensorA-B_validacion_pasto1_20261026_171303.csv",
          "pasto denso 2": "registro_sensorA-B_validacion_pasto2_20261026_171700.csv",
          "pasto ralo": "registro_sensorA-B_validacion_ralo_20261026_172041.csv"}
R, N = "f6_640nm", "nir_855nm"

def emular(d, g):
    e = {}
    for m in "nz":
        for c in (R, N):
            x = d[f"{m}_{c}"].to_numpy(float)
            e[f"{m}_{c}"] = np.floor(x * g / d[f"{m}_ganancia_x"].to_numpy(float)) / g
    return e

def cociente(e):
    with np.errstate(divide="ignore", invalid="ignore"):
        return {c: e[f"n_{c}"] / e[f"z_{c}"] for c in (R, N)}

filas = []
for nombre, f in pastos.items():
    p = pd.read_csv(f"{C}/{f}")
    for g in (64, 8, 2, 1, 0.5):
        eb, ep = emular(blanco, g), emular(p, g)
        qb = cociente(eb)
        ref = {c: np.nanmean(qb[c][np.isfinite(qb[c])]) if np.isfinite(qb[c]).any() else np.nan for c in (R, N)}
        qp = cociente(ep)
        rho_r, rho_n = qp[R] / ref[R], qp[N] / ref[N]
        with np.errstate(divide="ignore", invalid="ignore"):
            ndvi = (rho_n - rho_r) / (rho_n + rho_r)
        ok = np.isfinite(ndvi)
        filas.append({"superficie": nombre, "ganancia_x": g,
                      "f6_nadir_cuentas": round(float(np.mean(p[f"n_{R}"] * g / p["n_ganancia_x"])), 1),
                      "f6_cenit_cuentas": round(float(np.mean(p[f"z_{R}"] * g / p["z_ganancia_x"])), 1),
                      "lecturas_validas": f"{ok.sum()} de {len(ndvi)}",
                      "ndvi_media": round(float(np.mean(ndvi[ok])), 3) if ok.any() else None,
                      "ndvi_desv": round(float(np.std(ndvi[ok], ddof=1)), 3) if ok.sum() > 1 else None})
t = pd.DataFrame(filas)
print(t.to_string(index=False))
t.to_csv(sys.argv[2], index=False)
