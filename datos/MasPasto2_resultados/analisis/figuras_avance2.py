"""Figuras y verificaciones para el informe de avance (corte 28 oct 2026).
Lee los CSV crudos de las sesiones del 21 al 26 oct (los busca en las carpetas crudos/) y escribe PDF en salidas/figuras_avance."""
import glob, math, os, statistics as st
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # carpeta MasPasto2_resultados
D = os.path.join(BASE, "2026-10-26_campo_uniandes", "crudos")
F = os.path.join(BASE, "salidas", "figuras_avance"); os.makedirs(F, exist_ok=True)
CH = ["f1_405nm", "f2_425nm", "fz_450nm", "f3_475nm", "f4_515nm", "f5_550nm", "fy_555nm",
      "fxl_600nm", "f6_640nm", "f7_690nm", "f8_745nm", "nir_855nm"]
WL = [405, 425, 450, 475, 515, 550, 555, 600, 640, 690, 745, 855]
plt.rcParams.update({"text.hinting": "no_hinting", "font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25})
C1, C2, C3, C4, C5 = "#2F6B4F", "#C0622B", "#4C72B0", "#8C6BB1", "#7A7A7A"


def f(pat):
    r = sorted(glob.glob(os.path.join(BASE, "2026-*", "crudos", "**", pat), recursive=True))   # el archivo puede ser de otra sesión
    assert r, pat
    return r[0]


def norm(df, p, ch):
    return df[f"{p}_{ch}"] / (df[f"{p}_ganancia_x"] * df[f"{p}_t_int_ms"])


def pares(df):
    ok = df["z_desfase_s"].abs() <= 0.3
    ok &= (~df["n_saturado"].astype(bool)) & (~df["z_saturado"].astype(bool))
    return df[ok]


def cociente(df):
    d = pares(df)
    return {c: float((norm(d, "n", c) / norm(d, "z", c)).mean()) for c in CH}, len(d), len(df)


def nd(a, b):
    return (a - b) / (a + b)


# ---------------- 1. Barridos de saturacion ----------------
barr = [("Nadir, pasto al sol (15:53)", "saturacion_sensorA_operacion_sat_pasto_sol_1545_20261026_155332_resumen.csv", C2, "o"),
        ("Nadir, pasto, sol bajo (16:01)", "saturacion_sensorA_operacion_sat_pasto_1700_20261026_160101_resumen.csv", C1, "s"),
        ("Nadir, pasto a la sombra (15:54)", "saturacion_sensorA_operacion_sat_pasto_sombra_20261026_155424_resumen.csv", C3, "^"),
        ("Cenit, nublado (~16:55)", "saturacion_sensorB_cenit_3mm_zen_nublado_20260415_133507_resumen.csv", C4, "D"),
        ("Cenit, nublado, al anochecer (17:11)", "saturacion_sensorB_cenit_3mm_zen_nublado_20261026_171133_resumen.csv", C5, "v")]
fig, ax = plt.subplots(figsize=(6.4, 4.4))
print("== Barridos")
for lab, fn, col, mk in barr:
    r = pd.read_csv(f(fn))
    seg = r[r["max_pct_max"] < 90]
    print(f"{lab}: " + ", ".join(f"{g:g}x {p}%" for g, p in zip(r.ganancia_x, r.max_pct_media)),
          f"| segura {seg.ganancia_x.max():g}x")
    ax.plot(r.ganancia_x, r.max_pct_media, marker=mk, color=col, lw=1.3, ms=4.5, label=lab)
ax.axhline(90, color="k", lw=1, ls="--"); ax.text(40, 103, "límite (90 %)", fontsize=8)
ax.axhline(40, color="k", lw=0.8, ls=":"); ax.text(60, 44, "umbral para subir (40 %)", fontsize=8)
ax.set_xscale("log", base=2); ax.set_yscale("log")
ax.set_xticks([0.5, 1, 2, 4, 8, 16, 32, 64, 128]); ax.set_xticklabels(["0,5", "1", "2", "4", "8", "16", "32", "64", "128"])
ax.set_yticks([1, 2, 5, 10, 20, 50, 100]); ax.set_yticklabels(["1", "2", "5", "10", "20", "50", "100"])
ax.set_ylim(0.5, 130)
ax.set_xlabel("Ganancia (×)"); ax.set_ylabel("Canal más alto (% de 65 535)")
ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False)
fig.tight_layout(); fig.savefig(f"{F}/campo_saturacion.pdf"); plt.close(fig)

# ---------------- 2. Validacion espectral ----------------
print("== Validacion")
sup = {"blanco1": "registro_sensorA-B_validacion_blanco1_*.csv", "blanco2": "registro_sensorA-B_validacion_blanco2_*.csv",
       "pasto1": "registro_sensorA-B_validacion_pasto1_*.csv", "pasto2": "registro_sensorA-B_validacion_pasto2_*.csv",
       "ralo": "registro_sensorA-B_validacion_ralo_*.csv", "cemento": "registro_sensorA-B_validacion_cemento_*.csv"}
Q = {}
for k, p in sup.items():
    q, n_ok, n = cociente(pd.read_csv(f(p)))
    Q[k] = q
    print(f"{k}: {n_ok}/{n} pares válidos")
blanco = {c: math.sqrt(Q["blanco1"][c] * Q["blanco2"][c]) for c in CH}
print("blanco1/blanco2:", {c: round(Q["blanco1"][c] / Q["blanco2"][c], 3) for c in ["f5_550nm", "f6_640nm", "nir_855nm"]})
rho = {k: {c: Q[k][c] / blanco[c] for c in CH} for k in ["pasto2", "pasto1", "ralo", "cemento"]}
tabla = []
for k, r in rho.items():
    t = (k, nd(r["nir_855nm"], r["f6_640nm"]), nd(r["nir_855nm"], r["f8_745nm"]), nd(r["f8_745nm"], r["f7_690nm"]))
    tabla.append(t); print("%s NDVI %.3f NDRE1 %.3f NDRE2 %.3f" % t)
nom = {"pasto2": "Pasto denso (2)", "pasto1": "Pasto denso (1)", "ralo": "Pasto ralo", "cemento": "Adoquín"}
cols = {"pasto2": C1, "pasto1": "#6FA585", "ralo": C2, "cemento": C5}
fig, ax = plt.subplots(figsize=(6.4, 3.5))
for k, r in rho.items():
    ax.plot(WL, [r[c] for c in CH], marker="o", ms=3.5, lw=1.3, color=cols[k], label=nom[k])
for w, n_ in [(640, "F6"), (690, "F7"), (745, "F8"), (855, "NIR")]:
    ax.axvline(w, color="0.75", lw=0.8, ls="--"); ax.text(w + 3, 1.02, n_, fontsize=7.5, color="0.4")
ax.set_xlabel("Longitud de onda del pico del canal (nm)"); ax.set_ylabel("Reflectancia relativa al blanco")
ax.set_ylim(0, 1.08); ax.legend(fontsize=8, frameon=False, loc="upper left")
fig.tight_layout(); fig.savefig(f"{F}/campo_espectros.pdf"); plt.close(fig)

# ---------------- 3. E4 con nubes ----------------
print("== E4")
df = pd.read_csv(f("registro_sensorA-B_operacion_E4_nubes_20261026_173202.csv"))
d = pares(df)
t = (d["n_t"] - d["n_t"].iloc[0]) / 60
sn = norm(d, "n", "nir_855nm"); sz = norm(d, "z", "nir_855nm"); q = sn / sz
cv = lambda v: float(np.std(v, ddof=1) / np.mean(v) * 100)
print(f"pares {len(d)}/{len(df)}; CV nadir {cv(sn):.1f} %, cenit {cv(sz):.1f} %, cociente {cv(q):.1f} %")
for c in ["f7_690nm", "f8_745nm", "f6_640nm"]:
    print(c, "CV cociente %.1f %%" % cv(norm(d, "n", c) / norm(d, "z", c)))
rr = {c: (norm(d, "n", c) / norm(d, "z", c)) / blanco[c] for c in ["nir_855nm", "f6_640nm", "f7_690nm", "f8_745nm"]}
ndvi = nd(rr["nir_855nm"], rr["f6_640nm"]); ndre2 = nd(rr["f8_745nm"], rr["f7_690nm"]); ndre1 = nd(rr["nir_855nm"], rr["f8_745nm"])
k5 = max(1, len(d) // 5)
for n_, v in [("NDVI", ndvi), ("NDRE1", ndre1), ("NDRE2", ndre2)]:
    print(f"{n_}: media {v.mean():.3f}, CV {cv(v):.1f} %, primer quinto {v.iloc[:k5].mean():.3f}, ultimo {v.iloc[-k5:].mean():.3f}")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.0))
a1.plot(t, sn / sn.mean(), color=C2, lw=1.2, label="NIR del nadir (crudo)")
a1.plot(t, sz / sz.mean(), color=C3, lw=1.2, label="NIR del cenit (crudo)")
a1.plot(t, q / q.mean(), color=C1, lw=1.8, label="Cociente nadir/cenit")
a1.set_xlabel("Tiempo (min)"); a1.set_ylabel("Señal / su media"); a1.legend(fontsize=7.5, frameon=False)
a1.set_title("(a) Señal normalizada en 855 nm", fontsize=9, loc="left")
a2.plot(t, ndvi, color=C2, lw=1.3, label="NDVI")
a2.plot(t, ndre2, color=C1, lw=1.3, label="NDRE$_2$")
a2.set_ylim(0.45, 0.85); a2.set_xlabel("Tiempo (min)"); a2.set_ylabel("Índice corregido")
a2.legend(fontsize=7.5, frameon=False); a2.set_title("(b) Índices corregidos", fontsize=9, loc="left")
fig.tight_layout(); fig.savefig(f"{F}/campo_E4.pdf"); plt.close(fig)

# ---------------- 4. k con intercambio ----------------
print("== k")
pos = ["163938", "170015", "180021", "190012", "200011"]
R = []
for p_ in pos:
    dd = pd.read_csv(f(f"intercomparacion_sensorA-B_difusor_20261022_{p_}.csv"))
    cols_ = dd.columns
    pre_n = "n" if "n_nir_855nm" in cols_ else None
    R.append({c: float((norm(dd, "z", c) / norm(dd, "n", c)).mean()) for c in CH})
lnr = {c: [math.log(r[c]) for r in R] for c in CH}
k = {c: math.exp((np.mean([lnr[c][0], lnr[c][2], lnr[c][4]]) + np.mean([lnr[c][1], lnr[c][3]])) / 2) for c in CH}
p = {c: math.exp((np.mean([lnr[c][0], lnr[c][2], lnr[c][4]]) - np.mean([lnr[c][1], lnr[c][3]])) / 2) for c in CH}
print("k:", {c: round(k[c], 3) for c in CH}); print("p:", {c: round(p[c], 2) for c in CH})
fig, ax = plt.subplots(figsize=(6.4, 3.2))
x = np.arange(len(CH))
orig = [np.mean([R[i][c] for i in (0, 2, 4)]) for c in CH]
inter = [np.mean([R[i][c] for i in (1, 3)]) for c in CH]
ax.plot(x, orig, "o", color=C2, ms=5, label="Posición original (1, 3 y 5)")
ax.plot(x, inter, "s", color=C3, ms=5, label="Posiciones intercambiadas (2 y 4)")
ax.plot(x, [k[c] for c in CH], "-", color=C1, lw=2, label="$k$ (media geométrica)")
ax.set_xticks(x); ax.set_xticklabels([c.split("_")[0].upper() for c in CH], fontsize=8)
ax.set_ylabel("Cociente B/A (sensor cenit / sensor nadir)"); ax.legend(fontsize=7.5, frameon=False)
fig.tight_layout(); fig.savefig(f"{F}/lab_k.pdf"); plt.close(fig)
