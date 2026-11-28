"""Figuras del documento final de MasPasto2, hechas solo con los datos de esta carpeta.

Uso: python3 -I analisis/figuras_documento_final.py <carpeta_MasPasto2_resultados> <carpeta_de_salida>

Cada figura sale de los CSV de derivados/ (que a su vez salen de los crudos con los scripts de analisis/)
o directamente de un crudo, que se nombra en el comentario de cada bloque.
"""
import sys, os, glob
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

B, OUT = sys.argv[1], sys.argv[2]
D = os.path.join(B, "derivados")
os.makedirs(OUT, exist_ok=True)
VERDE, NARANJA, AZUL, GRIS, NEGRO = "#2E6B3A", "#C0622B", "#3B6FB6", "#7A7A7A", "#222222"
plt.rcParams.update({"text.hinting": "no_hinting", "font.family": "DejaVu Sans", "font.size": 8.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3,
                     "legend.frameon": False, "legend.fontsize": 7.5, "axes.titlesize": 9,
                     "axes.titlelocation": "left", "pdf.fonttype": 42})
CH = ["f1_405nm", "f2_425nm", "fz_450nm", "f3_475nm", "f4_515nm", "f5_550nm", "fy_555nm", "fxl_600nm",
      "f6_640nm", "f7_690nm", "f8_745nm", "nir_855nm"]
WL = [405, 425, 450, 475, 515, 550, 555, 600, 640, 690, 745, 855]
IDX = [("f6_640nm", "F6 (640 nm)", NARANJA, "o"), ("f7_690nm", "F7 (690 nm)", "#8A5FB0", "s"),
       ("f8_745nm", "F8 (745 nm)", VERDE, "^"), ("nir_855nm", "NIR (855 nm)", AZUL, "D")]


def busca(nombre):
    f = glob.glob(os.path.join(B, "**", nombre), recursive=True)
    assert f, nombre
    return f[0]


def guarda(fig, nombre):
    fig.savefig(os.path.join(OUT, nombre), bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print("->", nombre)


# ------------------------------------------------------------------------------------------
# 1. Factores de ganancia medidos frente al valor tipico de la hoja de datos (DS001046, Fig. 10)
#    Datos: lab22_factores_ganancia.csv (1, 2 y 8x), casa6_factores_ganancia.csv (2-256x),
#    noche10_factores_05.csv (0,5x del nadir) y tarde11_factor05_cenit.csv (0,5x del cenit).
# ------------------------------------------------------------------------------------------
TIP = {0.5: 7.9e-3, 1: 15.8e-3, 2: 31.6e-3, 4: 64e-3, 8: 124e-3, 16: 247e-3, 32: 0.5, 64: 1.0, 128: 2.0,
       256: 4.1}                                   # ganancia relativa a 64x, valor tipico
hoja = {g: 100 * ((v / TIP[4]) / (g / 4) - 1) for g, v in TIP.items()}
c6 = pd.read_csv(os.path.join(D, "casa6_factores_ganancia.csv"))
l22 = pd.read_csv(os.path.join(D, "lab22_factores_ganancia.csv"), encoding="utf-8-sig")
n05 = pd.read_csv(os.path.join(D, "noche10_factores_05.csv"))
t05 = pd.read_csv(os.path.join(D, "tarde11_factor05_cenit.csv"))
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.7), sharey=True)
G = [0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256]
pos = {g: i for i, g in enumerate(G)}
for a, sen, nom in ((ax[0], "A", "a) Sensor A (nadir)"), (ax[1], "B", "b) Sensor B (cenit)")):
    a.step([pos[g] for g in G], [hoja[g] for g in G], where="mid", color=NEGRO, lw=1.2, ls="--",
           label="Típico de la hoja de datos")
    for c, lab, col, mk in IDX:
        x, y = [], []
        for g in G:
            v = None
            r6 = c6[(c6.sensor == sen) & (c6.ganancia_x == g)]
            r2 = l22[(l22.sensor == sen) & (l22.ganancia_x == g)]
            if g == 0.5:
                v = n05[n05.ganancia_x == 0.5][c].mean() if sen == "A" else float(t05[t05.ganancia_x == 0.5][c + "_regresion"].iloc[0])
            elif len(r6):
                v = float(r6[c].iloc[0])
            elif len(r2):
                v = float(r2[c].iloc[0])
            if v is not None:
                x.append(pos[g]); y.append(v)
        a.plot(x, y, marker=mk, ms=3.5, lw=0.9, color=col, label=lab)
    if sen == "B":
        e = float(t05[t05.ganancia_x == 0.5]["nir_855nm_ee"].iloc[0])
        a.errorbar([pos[0.5]], [float(t05[t05.ganancia_x == 0.5]["nir_855nm_regresion"].iloc[0])], yerr=[e],
                   color=AZUL, capsize=2, lw=0.8)
    a.axhline(0, color=GRIS, lw=0.6)
    a.set_xticks(range(len(G))); a.set_xticklabels(["0,5", "1", "2", "4", "8", "16", "32", "64", "128", "256"])
    a.set_xlabel("Ganancia nominal (×)"); a.set_title(nom)
ax[0].set_ylabel("Ganancia real / nominal − 1 (%)\nreferida a 4×")
h, l = ax[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=5, fontsize=7.5, bbox_to_anchor=(0.5, -0.09))
fig.tight_layout(w_pad=0.8)
guarda(fig, "fig_ganancias.pdf")

# ------------------------------------------------------------------------------------------
# 2. Compensacion de la luz: (a) nubes del 26 oct. (crudo E4_nubes), (b) lampara del 28-29 oct.
#    (lab28_E4.csv), (c) 5 nov. por corrida (campo_5nov_cocientes_por_archivo.csv).
# ------------------------------------------------------------------------------------------
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.5))
d = pd.read_csv(busca("registro_sensorA-B_operacion_E4_nubes_20261026_173202.csv"))
d = d[d.z_desfase_s.abs() <= 0.3]
t = (d.n_t - d.n_t.iloc[0]) / 60
sn = d.n_nir_855nm / (d.n_ganancia_x * d.n_t_int_ms); sz = d.z_nir_855nm / (d.z_ganancia_x * d.z_t_int_ms)
q = sn / sz
a = ax[0]
a.plot(t, sn / sn.mean(), color=NARANJA, lw=1, label="Nadir (crudo)")
a.plot(t, sz / sz.mean(), color=AZUL, lw=1, ls="--", label="Cenit (crudo)")
a.plot(t, q / q.mean(), color=VERDE, lw=1.2, label="Cociente nadir/cenit")
a.set_xlabel("Tiempo (min)"); a.set_ylabel("NIR / su media"); a.set_title("a) Nubes, 26 oct.")
a.legend(loc="upper right")
print("  26 oct: pares", len(d), "CV nadir %.1f cenit %.1f cociente %.2f" % (100 * sn.std() / sn.mean(), 100 * sz.std() / sz.mean(), 100 * q.std() / q.mean()))
e4 = pd.read_csv(os.path.join(D, "lab28_E4.csv"), encoding="utf-8-sig")
a = ax[1]; x = range(len(e4))
a.plot(x, e4.NDVI_nadir, "o-", color=NARANJA, ms=3.5, lw=1, label="Solo nadir")
a.plot(x, e4.NDVI_corr, "s-", color=VERDE, ms=3.5, lw=1, label="Corregido con el cenit")
a.set_xticks(list(x)); a.set_xticklabels([f"{str(v)[:2].rstrip('V')} V\n{l:.0f} %" for v, l in zip(e4.voltaje, e4["luz_cenit_%"])], fontsize=7)
a.set_xlabel("Voltaje de la lámpara y luz en el cenit"); a.set_ylabel("NDVI"); a.set_title("b) Lámpara, 28–29 oct.")
a.legend(loc="upper left")
c5 = pd.read_csv(os.path.join(D, "campo_5nov_cocientes_por_archivo.csv"), dtype={"hora": str})
c5 = c5[c5.etiqueta.str.match(r"^[GW]f?_(sol|nube)_\d+$") & c5.cv_qNIR.notna()].copy()
nb = c5.etiqueta.str.extract(r"_(sol|nube)_(\d+)")
c5["cond"] = np.where(nb[0] == "sol", "Sol", np.where(nb[1].astype(int) >= 8, "Nublado", np.where(nb[1].astype(int) == 1, "Mixto", "Sombrilla")))
a = ax[2]
for cond, col, mk in (("Sol", "#D9A400", "o"), ("Mixto", GRIS, "^"), ("Nublado", VERDE, "s"), ("Sombrilla", NARANJA, "x")):
    s = c5[c5.cond == cond]
    a.loglog(s.cv_zNIR, s.cv_qNIR, mk, color=col, ms=3.5, label=f"{cond} ({len(s)})", ls="none")
lim = [0.1, 40]; a.plot(lim, lim, color=GRIS, lw=0.7, ls=":"); a.set_xlim(lim); a.set_ylim(lim)
a.set_xlabel("CV del NIR en el cenit (%)"); a.set_ylabel("CV del cociente NIR (%)"); a.set_title("c) Campo, 5 nov., por corrida")
a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=2, fontsize=6.3, handletextpad=0.1, columnspacing=0.8)
limpias = c5[(c5.cond == "Sol") & c5.etiqueta.str.startswith("G")]      # las diez corridas sobre el pasto de los bloques de sol
nubl = c5[(c5.cond == "Nublado")]
print("  5 nov nublado: CV cenit max %.2f; cociente pasto %.2f-%.2f; carton %.2f-%.2f" % (nubl.cv_zNIR.max(), nubl[nubl.etiqueta.str.startswith("G")].cv_qNIR.min(), nubl[nubl.etiqueta.str.startswith("G")].cv_qNIR.max(), nubl[nubl.etiqueta.str.startswith("W")].cv_qNIR.min(), nubl[nubl.etiqueta.str.startswith("W")].cv_qNIR.max()))
print("  5 nov bloques de sol (pasto, %d corridas):" % len(limpias), " CV cenit medio %.1f max %.1f; cociente medio %.2f max %.2f" % (limpias.cv_zNIR.mean(), limpias.cv_zNIR.max(), limpias.cv_qNIR.mean(), limpias.cv_qNIR.max()))
fig.tight_layout(w_pad=0.8)
guarda(fig, "fig_compensacion.pdf")

# ------------------------------------------------------------------------------------------
# 3. E2: fotos de las huellas, indices frente a la fraccion verde y firma espectral.
#    Datos: tarde11_superficies.csv, sitio10_resumen.csv, campo26_validacion.csv y fotos de las sesiones.
# ------------------------------------------------------------------------------------------
s = pd.read_csv(os.path.join(D, "tarde11_superficies.csv"))
r10 = pd.read_csv(os.path.join(D, "sitio10_resumen.csv")).set_index("codigo")
m = s.groupby(["dia", "codigo"]).agg(ndvi=("ndvi_carton", "mean"), ndre2=("ndre2_carton", "mean"),
                                     ndre1=("ndre1_carton", "mean"), verde=("verde_pct", "mean"),
                                     vmin=("verde_pct", "min"), vmax=("verde_pct", "max")).reset_index()
for i, r in m.iterrows():
    if r.dia == "10 nov":
        m.loc[i, ["verde", "vmin", "vmax"]] = [r10.loc[r.codigo, "verde_canopeo_pct"], r10.loc[r.codigo, "verde_min_pct"], r10.loc[r.codigo, "verde_max_pct"]]
m["et"] = m.codigo + np.where(m.codigo.isin(["V1", "T"]), "(" + m.dia.str[:2] + ")", "")
m.to_csv(os.path.join(D, "final_e2_ocho_puntos.csv"), index=False)
from scipy.stats import spearmanr
for x in ("ndvi", "ndre2", "ndre1"):
    print("  Spearman", x, round(float(spearmanr(m.verde, m[x])[0]), 3))
S10 = os.path.join(B, "2026-11-10_sitio_E2_superficies", "fotos")
S11 = os.path.join(B, "2026-11-11_tarde_par_superficies_E_F", "fotos")
fotos = [("V1(10)", os.path.join(S10, "huella_V1_1.jpg")), ("V2", os.path.join(S10, "huella_V2_1.jpg")),
         ("V3", os.path.join(S10, "huella_V3_1.jpg")), ("T(10)", os.path.join(S10, "huella_T_1.jpg")),
         ("A", os.path.join(S10, "huella_A_1.jpg")), ("V4", os.path.join(S11, "medicion_0024_20261111_134815.jpg")),
         ("T(11)", os.path.join(S11, "medicion_0027_20261111_135207.jpg"))]
fig = plt.figure(figsize=(7.2, 4.4))
for j, (et, f) in enumerate(fotos):
    a = fig.add_axes([0.005 + j * 0.1425, 0.74, 0.135, 0.22])
    im = Image.open(f).convert("RGB"); w, h = im.size; k = min(w, h)
    a.imshow(im.crop(((w - k) // 2, (h - k) // 2, (w + k) // 2, (h + k) // 2)).resize((300, 300)))
    v = m[m.et == et].verde.iloc[0]
    a.set_title(f"{et.replace('(10)', '').replace('(11)', ' (11 nov.)') if et != 'T(10)' else 'T (10 nov.)'}: {v:.0f} %", fontsize=7.5, loc="center"); a.axis("off")
a = fig.add_axes([0.075, 0.1, 0.45, 0.53])
for x, lab, col, mk in (("ndvi", "NDVI (855/640)", VERDE, "o"), ("ndre2", "NDRE$_2$ (745/690)", NARANJA, "s"), ("ndre1", "NDRE$_1$ (855/745)", GRIS, "^")):
    a.errorbar(m.verde, m[x], xerr=[m.verde - m.vmin, m.vmax - m.verde], fmt=mk, color=col, ms=4.5, capsize=1.5, lw=0.7, label=lab)
OFF = {"V1(10)": (-62, 4), "V1(11)": None, "V2": (5, -10), "V3": (6, -3), "T(10)": (7, -10), "T(11)": (-3, 9),
       "V4": (6, 1), "A": (7, -8)}
for _, r in m.iterrows():
    if OFF[r.et] is None:
        continue
    txt = "V1 (10 y 11 nov.)" if r.et == "V1(10)" else r.et.replace("(10)", " (10 nov.)").replace("(11)", " (11 nov.)")
    a.annotate(txt, (r.verde, r.ndvi), textcoords="offset points", xytext=OFF[r.et], fontsize=6.8, color=VERDE)
a.set_xlabel("Fracción verde de la foto de la huella (%)"); a.set_ylabel("Índice (referencia: cartón)")
a.set_xlim(-4, 104); a.set_ylim(0, 0.95); a.legend(loc="upper left", bbox_to_anchor=(0.0, 0.93)); a.set_title("a) Índices frente a la cobertura verde")
v26 = pd.read_csv(os.path.join(D, "campo26_validacion.csv"), encoding="utf-8-sig").set_index("superficie")
a = fig.add_axes([0.62, 0.1, 0.37, 0.53])
for cod, lab, col, mk in (("pasto2", "Pasto denso", VERDE, "o"), ("ralo", "Pasto ralo", NARANJA, "s"), ("cemento", "Adoquín", GRIS, "^")):
    a.plot(WL, [v26.loc[cod, "rho_" + c] for c in CH], marker=mk, ms=3.5, lw=1, color=col, label=lab)
for w_, n_ in ((640, "F6"), (690, "F7"), (745, "F8"), (855, "NIR")):
    a.axvline(w_, color=GRIS, lw=0.5, ls=":"); a.text(w_, 1.0, n_, fontsize=6.5, ha="center", va="bottom", color=GRIS)
a.set_ylim(0, 1.0); a.set_xlabel("Longitud de onda del pico del canal (nm)"); a.set_ylabel("Reflectancia relativa al blanco")
a.legend(loc="upper left"); a.set_title("b) Firma espectral (26 oct.)", pad=10)
guarda(fig, "fig_e2.pdf")

# ------------------------------------------------------------------------------------------
# 4. Optica: (a) campo de vision del nadir (tarde11_fov*.csv), (b) respuesta angular del cenit
#    (noche10_angular.csv), (c) referencia: fondo bajo el PTFE (lab28_ptfe_efectos_pct.csv) y
#    reflectancia de las laminas frente al carton (tarde11_par.csv).
# ------------------------------------------------------------------------------------------
fd = pd.read_csv(os.path.join(D, "tarde11_fov.csv")); fc = pd.read_csv(os.path.join(D, "tarde11_fov_corridas.csv"))
fc = fc[fc.diametro_cm.notna() & fc.completa]
thm = float(fd.th_max_ajuste_deg.iloc[0])
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.6))
a = ax[0]; th = np.linspace(0, 55, 200)
a.plot(th, np.sin(np.radians(th)) ** 2, ":", color=GRIS, lw=1, label="Coseno")
a.plot(th, np.minimum(1, np.sin(np.radians(th)) ** 2 / np.sin(np.radians(thm)) ** 2), "-", color=NARANJA, lw=1.2, label=f"Recortado a {thm:.0f}°")
a.plot(fc.semiangulo_deg, fc.F_med, "o", color=VERDE, ms=4, label="Discos")
for _, r in fd.iterrows():
    a.annotate(f"{r.diametro_cm:.0f} cm", (r.semiangulo_deg, r.F_max), textcoords="offset points", xytext=(5, -7) if r.diametro_cm < 18 else (-6, 5), fontsize=6.3)
a.set_xlabel("Semiángulo del disco desde la ventana (°)"); a.set_ylabel("Fracción de la señal del blanco")
a.set_ylim(0, 1.3); a.legend(loc="upper left", fontsize=6.0, borderpad=0.2, labelspacing=0.2); a.set_title("a) Campo de visión del nadir")
an = pd.read_csv(os.path.join(D, "noche10_angular.csv"))
esp = ["rel_" + c for c in CH[6:]]
an["rel"] = an[esp].median(axis=1)
a = ax[1]; tt = np.linspace(-65, 65, 100)
a.plot(tt, np.cos(np.radians(tt)), color=GRIS, lw=1, ls=":", label="Coseno ideal")
for p_, col, mk in ((1, VERDE, "o"), (2, NARANJA, "s")):
    q_ = an[an.plano == p_].sort_values("angulo")
    xs = [-60, -30, 0, 30, 60]; ys = [float(q_[q_.angulo == v].rel.iloc[0]) if v else 1.0 for v in xs]
    a.plot(xs, ys, marker=mk, ms=3.5, lw=1, color=col, label=f"Plano {p_}")
sim = [(an[(an.angulo.abs() == v)].groupby("plano").rel.mean()).mean() for v in (30, 60)]
a.plot([-60, -30, 0, 30, 60], [sim[1], sim[0], 1, sim[0], sim[1]], "--", color=NEGRO, lw=0.8, label="Promedio de + y −")
a.set_xticks([-60, -30, 0, 30, 60]); a.set_xlabel("Ángulo de la lámpara (°)"); a.set_ylabel("Señal relativa a 0°")
a.set_ylim(0, 1.25); a.legend(loc="lower center", fontsize=6.5); a.set_title("b) Respuesta angular del cenit")
print("  angular: promedio simetrico 30/60 =", [round(v, 3) for v in sim], "coseno 0.866/0.5")
par = pd.read_csv(os.path.join(D, "tarde11_par.csv")).set_index("codigo")
a = ax[2]
for cod, lab, col, mk in (("B2", "Pliego blanco", NARANJA, "s"), ("Gr", "Cartulina gris", GRIS, "o"), ("N", "Cartulina negra", NEGRO, "^")):
    a.errorbar(WL, [par.loc[cod, c] for c in CH], yerr=[par.loc[cod, c + "_sd"] for c in CH], marker=mk, ms=3, lw=0.9, capsize=1.2, color=col, label=lab)
a.axhline(1, color=GRIS, lw=0.6)
a.set_xlabel("Longitud de onda (nm)"); a.set_ylabel("Reflectancia frente al cartón"); a.set_ylim(0, 1.6)
a.legend(loc="center right", fontsize=6.5); a.set_title("c) Láminas de referencia")
fig.tight_layout(w_pad=0.6)
guarda(fig, "fig_optica.pdf")

# ------------------------------------------------------------------------------------------
# 5. Saturacion: (a) barridos del 26 oct. (campo26_barridos_saturacion.csv); (b) cenit con sol a 0,5x
#    (5 nov.: resumenes de saturacion del cenit; 13 nov.: mediodia13_atenuador.csv).
# ------------------------------------------------------------------------------------------
bs = pd.read_csv(os.path.join(D, "campo26_barridos_saturacion.csv"), encoding="utf-8-sig")
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.6), gridspec_kw={"width_ratios": [1.25, 1]})
a = ax[0]
nombres = {}
for b_ in bs.barrido.unique():
    k = b_.lower()
    if "pasto_sol" in k: nombres[b_] = ("Nadir, pasto al sol (15:53)", NARANJA, "o")
    elif "pasto_1700" in k: nombres[b_] = ("Nadir, pasto, sol bajo (16:01)", VERDE, "s")
    elif "pasto_sombra" in k: nombres[b_] = ("Nadir, pasto a la sombra (15:54)", AZUL, "^")
    elif bs[bs.barrido == b_].modulo.iloc[0] != "nadir":
        # el reloj de la Raspberry estaba mal en el primero; las horas reales estan en sesiones.md
        primero = not any(v[0].startswith("Cenit") for v in nombres.values())
        nombres[b_] = ("Cenit, nublado (hacia las 16:55)" if primero else "Cenit, nublado, al anochecer (17:11)",
                       "#8A5FB0" if primero else GRIS, "D" if primero else "v")
for b_, (lab, col, mk) in nombres.items():
    q_ = bs[bs.barrido == b_]
    a.loglog(q_.ganancia_x, q_.max_pct_media.clip(upper=100), marker=mk, ms=3.5, lw=1, color=col, label=lab)
a.axhline(90, color=NEGRO, lw=0.8, ls="--"); a.text(0.52, 93, "límite de saturación (90 %)", fontsize=6.5, va="bottom")
a.axhline(40, color=GRIS, lw=0.8, ls=":"); a.text(0.52, 41.5, "umbral para subir (40 %)", fontsize=6.5, va="bottom", color=GRIS)
a.set_xticks([0.5, 1, 2, 4, 8, 16, 32, 64, 128]); a.set_xticklabels(["0,5", "1", "2", "4", "8", "16", "32", "64", "128"])
a.set_yticks([1, 2, 5, 10, 20, 50, 100]); a.set_yticklabels(["1", "2", "5", "10", "20", "50", "100"])
a.set_ylim(0.5, 180); a.minorticks_off()
a.set_xlabel("Ganancia (×)"); a.set_ylabel("Canal más alto (% de 65 535)"); a.set_title("a) Barridos de ganancia, 26 oct.")
a.legend(loc="lower right", fontsize=6.3)
md = pd.read_csv(os.path.join(D, "mediodia13_atenuador.csv"))
s5 = {}
for f in glob.glob(os.path.join(B, "2026-11-05_campo_sol_nube", "crudos", "saturacion_sensorB_*[0-9].csv")):
    x = pd.read_csv(f); x = x[x.z_ganancia_x == 0.5]
    s5[os.path.basename(f)[-10:-6]] = 100 * x.z_max_cuentas.mean() / 65535
print("  5 nov cenit 0,5x:", {k: round(v, 1) for k, v in s5.items()})
et = ["5 nov.\n8:33", "5 nov.\n9:28", "13 nov.\n12:54", "13 nov.\n12:55", "13 nov.\n12:55"]
val = [s5["0833"], s5["0928"], float(md.max_pct_05x.iloc[0]), float(md.max_pct_05x.iloc[2]), float(md.max_pct_05x.iloc[1])]
col = [AZUL, AZUL, AZUL, AZUL, VERDE]
a = ax[1]
bars = a.bar(range(5), val, color=col, width=0.62)
for i, v in enumerate(val):
    a.text(i, v + 1.5, f"{v:.0f} %".replace(".", ","), ha="center", fontsize=7.5)
a.axhline(90, color=NEGRO, lw=0.8, ls="--")
a.set_xticks(range(5)); a.set_xticklabels(et, fontsize=7); a.set_ylim(0, 128); a.set_yticks([0, 20, 40, 60, 80, 100])
a.text(4.45, 91.5, "límite (90 %)", fontsize=6.5, ha="right", va="bottom")
a.set_ylabel("Canal más alto a 0,5× (% de la escala)"); a.set_title("b) Cenit con sol directo")
a.grid(axis="x", visible=False)
a.legend([bars[0], bars[4]], ["Sin atenuador", "Con atenuador (PTFE de 2 mm)"], loc="upper left", fontsize=6.5)
fig.tight_layout(w_pad=1.0)
guarda(fig, "fig_saturacion.pdf")

# ------------------------------------------------------------------------------------------
# 6. Modelo: R2 por esquema de validacion e importancia de variables. Valores de
#    verificacion_modelo.py (357 muestras CSIRO; media y desviacion de las particiones).
#    Importancia: feature_importances_ del modelo instalado, entrenado con las 357 muestras
#    (raspberry_pi/modelo_pasturametrics.pkl del repositorio: 0,146 NDVI, 0,147 altura, 0,707 NDVI x altura).
# ------------------------------------------------------------------------------------------
esq = ["CV 5 sin barajar", "CV 5 barajada\n×10", "CV agrupada por\nsitio y fecha"]
r2 = {"Random Forest": ([0.57, 0.48, 0.23], [0.05, 0.17, 0.28]),
      "XGBoost": ([0.46, 0.38, 0.06], [0.08, 0.23, 0.38]),
      "Lineal (NDVI×altura)": ([0.32, 0.29, 0.10], [0.09, 0.16, 0.16])}
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.6), gridspec_kw={"width_ratios": [1.6, 1], "wspace": 0.55})
a = ax[0]; x = np.arange(3); wb = 0.26
for i, (k, col) in enumerate(zip(r2, (VERDE, NARANJA, GRIS))):
    a.bar(x + (i - 1) * wb, r2[k][0], wb, yerr=r2[k][1], color=col, capsize=2, error_kw={"lw": 0.7}, label=k)
a.axhline(0, color=NEGRO, lw=0.6); a.set_xticks(x); a.set_xticklabels(esq, fontsize=7)
a.set_ylabel("R² (media ± desv.)"); a.set_ylim(-0.4, 1.1); a.legend(loc="upper right", fontsize=6.5, ncol=1)
a.set_title("a) R² según el esquema de validación")
a = ax[1]; var = ["NDVI×altura", "Altura", "NDVI"]; imp = [0.71, 0.15, 0.15]
b = a.barh(var, imp, color=[VERDE, "#9FBF8A", "#9FBF8A"]); a.invert_yaxis()
for yi, v in enumerate(imp):
    a.text(v + 0.01, yi, f"{v:.2f}".replace(".", ","), va="center", fontsize=7)
a.set_xlim(0, 0.8); a.set_xlabel("Importancia (reducción de impureza)"); a.set_title("b) Importancia en el modelo instalado")
guarda(fig, "modelo.pdf")
