"""Genera las tablas (LaTeX) y figuras del Apéndice C (informe de validación del sensor) a partir de las
tablas derivadas y los crudos del paquete de resultados. Ningún número de las tablas se escribe a mano."""
import glob, math, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"   # carpeta MasPasto2_resultados
D = R + "derivados/"
OUT = R + "salidas/apendiceB/tablas/"
FIG = R + "salidas/apendiceB/figuras/"
os.makedirs(FIG, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
CH = ["f1_405nm", "f2_425nm", "fz_450nm", "f3_475nm", "f4_515nm", "f5_550nm", "fy_555nm", "fxl_600nm", "f6_640nm",
      "f7_690nm", "f8_745nm", "nir_855nm"]
NOM = {c: c.split("_")[0].upper().replace("FXL", "FXL") for c in CH}
NOM["nir_855nm"] = "NIR"
PICO = {c: c.split("_")[1].replace("nm", "") for c in CH}
plt.rcParams.update({"text.hinting": "no_hinting", "font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def rd(n):
    return pd.read_csv(D + n, encoding="utf-8-sig")


def f(x, d=2, signo=False):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "---"
    s = f"{abs(x):.{d}f}".replace(".", "{,}")
    if x < 0 and float(f"{abs(x):.{d}f}") != 0:
        return f"$-{s}$"
    if signo and x > 0 and float(f"{x:.{d}f}") != 0:
        return f"$+{s}$"
    return f"${s}$" if "{,}" in s else s


def tabla(nombre, cab, filas, fmt, caption, label, tam="\\footnotesize", nota=None):
    t = [f"\\begin{{table}}[H]\n\\centering{tam}\n\\caption{{{caption}}}\n\\label{{{label}}}",
         f"\\begin{{tabular}}{{@{{}}{fmt}@{{}}}}\n\\toprule", " & ".join(cab) + "\\\\\n\\midrule"]
    for r in filas:
        t.append(r if isinstance(r, str) else " & ".join(r) + "\\\\")
    t.append("\\bottomrule\n\\end{tabular}")
    if nota:
        t.append(f"\\\\[2pt]{{\\scriptsize {nota}}}")
    t.append("\\end{table}\n")
    open(OUT + nombre + ".tex", "w").write("\n".join(t))


canal_cab = [f"{NOM[c]}" for c in CH]

# ---------------------------------------------------------------- E1
e1 = rd("lab28_E1.csv").set_index("variable")
filas = [["Nadir"] + [f(e1.loc[c, "CV_nadir_%"]) for c in CH], ["Cenit"] + [f(e1.loc[c, "CV_cenit_%"]) for c in CH],
         ["Cociente"] + [f(e1.loc[c, "CV_cociente_%"]) for c in CH]]
tabla("tC_E1", [""] + canal_cab, filas, "l" + "c" * 12,
      "E1: coeficiente de variación (\\%) de cada canal en 50 lecturas sobre pasto, con la lámpara a 12~V.", "tab:C_E1",
      nota="Un CV de 0 indica que las 50 lecturas dieron la misma cuenta (canales con pocas cuentas, donde la resolución domina).")
ind = [["NDVI", f(e1.loc["NDVI", "media"], 4), f(e1.loc["NDVI", "desv"], 4), f(e1.loc["NDVI", "CV_cociente_%"], 3)],
       ["NDRE$_2$", f(e1.loc["NDRE2", "media"], 4), f(e1.loc["NDRE2", "desv"], 4), f(e1.loc["NDRE2", "CV_cociente_%"], 3)],
       ["NDRE$_1$", f(e1.loc["NDRE1", "media"], 4), f(e1.loc["NDRE1", "desv"], 4), f(e1.loc["NDRE1", "CV_cociente_%"], 3)]]
tabla("tC_E1ind", ["Índice", "Media", "Desviación estándar", "CV (\\%)"], ind, "lccc",
      "E1: índices corregidos en las mismas 50 lecturas.", "tab:C_E1ind", tam="\\small")

# serie temporal de E1 desde el crudo
IDX = {os.path.basename(p): p for p in glob.glob(R + "**/*.csv", recursive=True)}


def L(n):
    return pd.read_csv(IDX[n + ".csv"])


def qq(n):
    d = L(n).dropna(subset=["z_nir_855nm"])
    return {c: (d["n_" + c] / d["z_" + c]).mean() for c in CH}


d = L("registro_sensorA-B_lab_E1_pasto_20261028_010404").dropna(subset=["z_nir_855nm"]).reset_index(drop=True)
Wb = qq("registro_sensorA-B_lab_E1_blanco1_20261028_010058")
r = {c: (d["n_" + c] / d["z_" + c]) / Wb[c] for c in CH}
ndvi = (r["nir_855nm"] - r["f6_640nm"]) / (r["nir_855nm"] + r["f6_640nm"])
ndre2 = (r["f8_745nm"] - r["f7_690nm"]) / (r["f8_745nm"] + r["f7_690nm"])
assert len(d) == 50, len(d)
fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.4))
for a, y, lab in [(ax[0], 100 * (d.n_nir_855nm / d.n_nir_855nm.mean() - 1), "NIR del nadir"),
                  (ax[0], 100 * (d.z_nir_855nm / d.z_nir_855nm.mean() - 1), "NIR del cenit")]:
    a.plot(np.arange(1, 51), y, lw=1, label=lab)
ax[0].plot(np.arange(1, 51), 100 * (r["nir_855nm"] / r["nir_855nm"].mean() - 1), lw=1.4, color="k", label="Cociente")
ax[0].set_ylabel("Desvío de la media (%)"); ax[0].set_title("(a) Canal NIR", loc="left", fontsize=9)
ax[0].legend(frameon=False, fontsize=6.5, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0)); ax[0].set_ylim(-0.15, 0.2)
ax[1].plot(np.arange(1, 51), ndvi, "o", ms=2.5, color="#2E6B3A"); ax[1].set_title("(b) NDVI", loc="left", fontsize=9)
ax[1].set_ylim(ndvi.mean() - 0.005, ndvi.mean() + 0.005)
ax[2].plot(np.arange(1, 51), ndre2, "o", ms=2.5, color="#7A4FA0"); ax[2].set_title("(c) NDRE$_2$", loc="left", fontsize=9)
ax[2].set_ylim(ndre2.mean() - 0.005, ndre2.mean() + 0.005)
for a in ax:
    a.set_xlabel("Lectura"); a.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(FIG + "apC_E1.pdf"); plt.close(fig)
print("E1 NDVI", round(ndvi.mean(), 4), round(ndvi.std(), 5))

# ---------------------------------------------------------------- E2
s10 = pd.read_csv(D + "sitio10_mediciones.csv")
t11 = pd.read_csv(D + "tarde11_interfaz.csv")
sup = pd.read_csv(D + "tarde11_superficies.csv")
NOMS = {"V1": "Pasto alto verde", "V2": "Pasto verde bajo", "V3": "Pasto con parches secos", "T": "Tierra",
        "A": "Grava", "V4": "Pasto seco"}
filas = []
orden = [("10 nov", "V1"), ("10 nov", "V2"), ("10 nov", "V3"), ("10 nov", "T"), ("10 nov", "A"), ("11 nov", "V4"),
         ("11 nov", "T"), ("11 nov", "V1")]
for dia, cod in orden:
    ss = sup[(sup.dia == dia) & (sup.codigo == cod)].sort_values("id")
    for k, (_, x) in enumerate(ss.iterrows(), 1):
        if dia == "10 nov":
            m = s10[s10.fila == x.id].iloc[0]; hora = (pd.to_datetime(m.hora_celular) - pd.Timedelta(hours=5)).strftime("%H:%M")
            cvv, luz = m.cv_cociente_nir_pct, m.luz_relativa_blanco
        else:
            m = t11[t11.id == x.id].iloc[0]; hora = m.hora[:5]; cvv, luz = m.cv_nir_pct, m.luz_rel
        filas.append([dia.replace(" nov", " nov."), hora, (NOMS[cod] if k == 1 else ""), str(k), f(x.ndvi_carton, 3),
                      f(x.ndre2_carton, 3), f(x.ndre1_carton, 3), f(cvv, 1), f(luz, 2)])
    filas.append("\\addlinespace[2pt]")
filas = filas[:-1]
assert sum(1 for r in filas if not isinstance(r, str)) == 24
tabla("tC_E2tomas", ["Día", "Hora", "Superficie", "Toma", "NDVI", "NDRE$_2$", "NDRE$_1$", "CV coc. (\\%)", "Luz"], filas,
      "llllccccc", "E2: las 24 tomas válidas sobre superficies del suelo. Índices frente al cartón; CV del cociente NIR "
      "dentro de la toma y luz del cenit frente a la del momento de la referencia.", "tab:C_E2tomas")

can = pd.read_csv(D + "sitio10_canopeo_fotos.csv")
filas = []
for cod in ["V1", "V2", "V3", "T", "A"]:
    cc = can[can.codigo == cod]
    filas.append([NOMS[cod]] + [f(v, 1) for v in cc.verde_pct] + [f(cc.verde_pct.mean(), 1), f(cc.cinta_pct.mean(), 1)])
tabla("tC_E2fotos", ["Superficie", "Foto 1", "Foto 2", "Foto 3", "Media", "Cinta excluida"], filas, "lccccc",
      "E2: fracción verde (\\%) de las fotos de las huellas del 10 de noviembre, tomadas con el celular (reglas de "
      "Canopeo~\\cite{Patrignani2015}); la última columna es la fracción de la foto ocupada por la cinta métrica, "
      "que se excluye.", "tab:C_E2fotos", tam="\\small")

e8 = pd.read_csv(D + "final_e2_ocho_puntos.csv")
rk = e8[["verde", "ndvi", "ndre2", "ndre1"]].rank()
sp = {k: rk["verde"].corr(rk[k]) for k in ["ndvi", "ndre2", "ndre1"]}
print("Spearman", {k: round(v, 3) for k, v in sp.items()})

c26 = rd("campo26_validacion.csv")
N26 = {"pasto2": "Pasto denso, punto 2", "pasto1": "Pasto denso, punto 1", "ralo": "Pasto ralo", "cemento": "Adoquín"}
filas = [[N26[x.superficie], str(x.pares), f(x.rho_f6_640nm, 3), f(x.rho_f7_690nm, 3), f(x.rho_f8_745nm, 3),
          f(x.rho_nir_855nm, 3), f(x.NDVI, 3), f(x.NDRE2, 3), f(x.NDRE1, 3)] for _, x in c26.iterrows()]
tabla("tC_E2oct", ["Superficie", "Pares", "$\\rho$ F6", "$\\rho$ F7", "$\\rho$ F8", "$\\rho$ NIR", "NDVI", "NDRE$_2$",
                   "NDRE$_1$"], filas, "lcccccccc",
      "Prueba preliminar de E2 (26 de octubre, nublado): reflectancia relativa a la cartulina blanca e índices.",
      "tab:C_E2oct")

par = pd.read_csv(D + "tarde11_par.csv")
NP = {"Gr": "Cartulina gris", "N": "Cartulina negra", "B2": "Pliego blanco nuevo"}
filas = []
for _, x in par[par.codigo != "C"].iterrows():
    filas.append([NP[x.codigo]] + [f(x[c], 3) for c in ["f2_425nm", "f6_640nm", "f7_690nm", "f8_745nm", "nir_855nm"]]
                 + [f(x.ndvi, 3), f(x.ndre2, 3)])
tabla("tC_par", ["Lámina (3 tomas)", "F2 425", "F6 640", "F7 690", "F8 745", "NIR 855", "NDVI", "NDRE$_2$"], filas,
      "lccccccc", "Láminas de referencia frente al cartón blanco (11 de noviembre), corregidas por la deriva de la luz "
      "durante el par.", "tab:C_par")

# ---------------------------------------------------------------- E3
e3 = rd("noche10_E3.csv").set_index("canal")
filas = []
for c in ["f6_640nm", "f7_690nm", "f8_745nm", "nir_855nm"]:
    x = e3.loc[c]
    filas.append([f"{NOM[c]} ({PICO[c]}~nm)", f(x.pendiente_conjunta_pct_por_C, 3, True), f(x.error_estandar, 3),
                  f(x.pendiente_sin_bolsa_antes, 2, True), f(x.pendiente_con_bolsa, 3, True),
                  f(x.pendiente_sin_bolsa_despues, 3, True), f(x.escalon_al_poner_pct, 2, True),
                  f(x.escalon_al_quitar_pct, 2, True)])
tabla("tC_E3", ["Canal", "Pendiente conjunta", "Error est.", "Antes", "Con bolsa", "Después", "Al poner", "Al quitar"],
      filas, "lccccccc", "E3: pendiente de la señal con la temperatura (\\%/°C) y escalones mecánicos (\\%). La pendiente "
      "conjunta ajusta los tres tramos sin movimiento a la vez, con un nivel propio por tramo; las tres columnas "
      "siguientes ajustan cada tramo por separado.", "tab:C_E3",
      nota="El tramo ``antes'' dura unos 3 minutos y abarca menos de 0,5~°C, por eso su pendiente es mucho menos precisa.")

# figura de E3 desde los crudos (misma lógica que analisis/noche10_analisis.py)
E3F = sorted(glob.glob(R + "2026-11-10_noche_angular_E3_05x/crudos/registro_sensorA_E3_ciclo_*.csv"))
E3F = [p for p in E3F if "resumen" not in p]
partes = []
for i, p in enumerate(E3F, 1):
    x = pd.read_csv(p); x["corrida"] = i; partes.append(x)
e = pd.concat(partes, ignore_index=True)
e["min"] = (e.n_t - e.n_t.iloc[0]) / 60
e["T"] = e.n_temp_c
for c in ["f6_640nm", "f8_745nm", "nir_855nm", "vis_c1"]:
    e[c] = e["n_" + c] / e["n_" + c].iloc[:200].mean()
r3 = e[e.corrida == 3].reset_index(drop=True)
t_quita = r3.loc[730, "min"]
r2 = e[e.corrida == 2]
sm = r2.vis_c1.rolling(5, center=True).mean()
t_pone = r2.loc[sm.diff().idxmin(), "min"]
print(f"E3 figura: {len(e)} lecturas, {e['min'].max():.1f} min, T {e['T'].min():.2f}-{e['T'].max():.2f}, bolsa {t_pone:.1f}-{t_quita:.1f}")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 2.9), gridspec_kw={"width_ratios": [1.35, 1]})
cols = {"f6_640nm": ("#C0622B", "F6"), "f8_745nm": ("#7A4FA0", "F8"), "nir_855nm": ("#2E6B3A", "NIR")}
for c, (col, lab) in cols.items():
    a1.plot(e["min"], 100 * (e[c].rolling(15, center=True).mean() - 1), color=col, lw=1, label=lab)
a1.axvspan(t_pone, t_quita, color="#F2A39A", alpha=0.25, label="bolsa puesta")
a1.set_xlabel("Minutos"); a1.set_ylabel("Cambio de la señal (%)"); a1.set_ylim(-1.6, 0.6); a1.grid(alpha=0.3)
b1 = a1.twinx(); b1.plot(e["min"], e["T"], color="#3F6FB5", lw=1.2, ls="--"); b1.set_ylabel("Temperatura (°C)", color="#3F6FB5")
b1.spines["right"].set_visible(True)
a1.legend(frameon=False, fontsize=7, loc="lower left", ncol=2)
a1.set_title("(a) Señal (media móvil de 15) y temperatura", loc="left", fontsize=9)
TR = {"antes": (0.05, t_pone - 0.1), "con": (t_pone + 0.4, t_quita - 0.2), "despues": (t_quita + 0.7, e["min"].max())}
for k, (a, b) in TR.items():
    s = e[(e["min"] >= a) & (e["min"] <= b)]
    y = 100 * (s["nir_855nm"] / s["nir_855nm"].mean() - 1)
    a2.plot(s["T"], y, ".", ms=1.5, alpha=0.4, label={"antes": "antes", "con": "con bolsa", "despues": "después"}[k])
pend = e3.loc["nir_855nm", "pendiente_conjunta_pct_por_C"]
tt = np.array([25.2, 28.6]); a2.plot(tt, pend * (tt - tt.mean()), "k-", lw=1.4, label=f"pendiente conjunta")
a2.set_xlabel("Temperatura (°C)"); a2.set_ylabel("NIR, desvío de la media del tramo (%)"); a2.grid(alpha=0.3)
a2.set_ylim(-0.4, 0.4); a2.legend(frameon=False, fontsize=7, markerscale=4)
a2.set_title("(b) NIR frente a la temperatura", loc="left", fontsize=9)
fig.tight_layout(); fig.savefig(FIG + "apC_E3.pdf"); plt.close(fig)

# ---------------------------------------------------------------- E4
e4 = rd("lab28_E4.csv")
filas = [[x.voltaje.replace("_vuelta", " (vuelta)").replace("V", "~V"), f(x["luz_cenit_%"], 1), f(x["cenit_NIR/F6"], 2),
          f(x.NDVI_nadir, 4), f(x.NDVI_corr, 4), f(x.NDRE2_nadir, 4), f(x.NDRE2_corr, 4), f(x.NDRE1_nadir, 4),
          f(x.NDRE1_corr, 4)] for _, x in e4.iterrows()]
tabla("tC_E4a", ["Voltaje", "Luz (\\%)", "NIR/F6 cenit", "NDVI solo nadir", "NDVI corr.", "NDRE$_2$ nadir",
                 "NDRE$_2$ corr.", "NDRE$_1$ nadir", "NDRE$_1$ corr."], filas, "lcccccccc",
      "E4 con lámpara: luz del cenit frente a la de 12~V, color de la luz (NIR/F6 en el cenit) e índices sin corregir "
      "(solo nadir) y corregidos con el cenit.", "tab:C_E4a")
c4 = rd("campo26_E4.csv").iloc[0]
filas = [["CV del cociente (\\%)"] + [f(c4[f"CV_cociente_{c}_%"], 1) for c in CH]]
tabla("tC_E4b", [""] + canal_cab, filas, "l" + "c" * 12,
      f"E4 con nubes (26 de octubre, {int(c4.pares)} pares): CV del cociente nadir/cenit por canal. El NIR crudo varió "
      f"con un CV de {f(c4['CV_NIR_nadir_%'],1)}~\\% en el nadir y {f(c4['CV_NIR_cenit_%'],1)}~\\% en el cenit.", "tab:C_E4b")
b5 = rd("campo_5nov_indices_por_bloque.csv")
filas = []
for blq in ["s1", "s2", "s3", "s4", "s5"]:
    a = b5[(b5.bloque == blq) & (b5.modo == "adaptativa, W nube1")].iloc[0]
    fx = b5[(b5.bloque == blq) & (b5.modo == "fija, Wf nube1")].iloc[0]
    hh = str(a.G).zfill(6)
    filas.append([blq.upper().replace("S", "Sol "), f"{hh[:2]}:{hh[2:4]}", "sol directo", f(a.NDVI, 4), f(a.NDRE2, 4), f(fx.NDVI, 4)])
for blq in ["n1", "n2", "n3", "n4", "n5", "n6", "n8", "n9", "n10"]:
    a = b5[(b5.bloque == blq) & (b5.modo == "adaptativa")].iloc[0]
    fx = b5[(b5.bloque == blq) & (b5.modo.str.startswith("fija"))]
    hh = str(a.G).zfill(6)
    filas.append([blq.replace("n", "Nube "), f"{hh[:2]}:{hh[2:4]}", a.cond, f(a.NDVI, 4), f(a.NDRE2, 4),
                  f(fx.NDVI.iloc[0], 4) if len(fx) else "---"])
tabla("tC_E4c", ["Bloque", "Hora", "Cielo", "NDVI adaptativa", "NDRE$_2$ adaptativa", "NDVI fija 0,5\\x{}"], filas,
      "lllccc", "Sol frente a nube en el mismo pasto (5 de noviembre). Los bloques de sol usan la referencia del bloque "
      "Nube~1; el bloque Nube~7 (sombrilla con cielo mixto) no tiene referencia propia y no se incluye.", "tab:C_E4c",
      nota="Sombrilla: tapa el pasto pero no el cenit, así que rompe la condición de validez (Sec.~\\ref{sec:val_luz}).")
sol = b5[b5.modo == "adaptativa, W nube1"].NDVI; nub = b5[(b5.bloque.isin(["n8", "n9", "n10"])) & (b5.modo == "adaptativa")].NDVI
print("sol", round(sol.mean(), 4), round(sol.std(), 4), "nube", round(nub.mean(), 4), round(nub.std(), 4))
fig, ax = plt.subplots(figsize=(7.0, 2.6))
COL = {"sol directo": "#E0A100", "mixto": "#8A9BB0", "sombrilla": "#B23A2E", "nublado natural": "#3F6FB5"}
for i, row in enumerate(filas):
    ax.plot(i, float(row[3].strip("$").replace("{,}", ".").replace("-", "-")), "o", color=COL[row[2]], ms=6)
ax.set_xticks(range(len(filas))); ax.set_xticklabels([r[0] for r in filas], rotation=45, fontsize=7.5)
for k, v in COL.items():
    ax.plot([], [], "o", color=v, label=k)
ax.legend(frameon=False, fontsize=7.5, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12)); ax.set_ylabel("NDVI (ganancia adaptativa)")
ax.set_ylim(0.70, 0.755); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(FIG + "apC_bloques5nov.pdf"); plt.close(fig)

# ---------------------------------------------------------------- caracterización
es = rd("lab22_estabilidad.csv").set_index("canal")
filas = [[lab] + [f(es.loc[c, col], 2) for c in CH] for lab, col in
         [("CV sensor A (\\%)", "CV_A_%"), ("CV sensor B (\\%)", "CV_B_%"), ("CV de B/A (\\%)", "CV_B/A_%"),
          ("Deriva de B/A (\\%)", "deriva_B/A_%")]]
tabla("tC_estab", [""] + canal_cab, filas, "l" + "c" * 12, "Estabilidad del montaje (22 de octubre): 150 pares en 7,1~min "
      "con la lámpara en DC. La deriva compara el último quinto de la corrida con el primero.", "tab:C_estab")

osc = []
for p, fecha in [("2026-10-21_lab_estabilidad_ganancias/crudos/oscuridad_sensorA-B_20261021_163102_resumen.csv", "21 oct."),
                 ("2026-11-06_casa_ganancias_2a256/crudos/oscuridad_sensorA-B_noche6nov_20261106_195455_resumen.csv", "6 nov."),
                 ("2026-11-10_noche_angular_E3_05x/crudos/oscuridad_sensorA-B_oscuridad_10nov_20261110_223410_resumen.csv", "10 nov.")]:
    x = pd.read_csv(R + p); x["fecha"] = fecha; osc.append(x)
osc = pd.concat(osc)
osc["max"] = osc[CH].max(axis=1); osc["nir"] = osc["nir_855nm"]
filas = []
for g in sorted(osc.ganancia_x.unique()):
    a = osc[(osc.ganancia_x == g) & (osc.sensor == "A")]; b = osc[(osc.ganancia_x == g) & (osc.sensor == "B")]
    gs = ("0,5" if g == 0.5 else str(int(g))) + "\\x{}"
    filas.append([gs, ", ".join(a.fecha), f(a["max"].max(), 1), f(a.nir.max(), 1), f(b["max"].max(), 1), f(b.nir.max(), 1)])
tabla("tC_osc", ["Ganancia", "Sesiones", "A: canal más alto", "A: NIR", "B: canal más alto", "B: NIR"], filas, "llcccc",
      "Oscuridad: cuentas medias con los sensores tapados (máximo entre sesiones), frente a señales de miles de cuentas en "
      "las mediciones.", "tab:C_osc", tam="\\small")

g6 = rd("casa6_factores_ganancia.csv")
filas = []
for sen in ["A", "B"]:
    for _, x in g6[g6.sensor == sen].iterrows():
        filas.append([sen if x.ganancia_x == g6[g6.sensor == sen].ganancia_x.min() else "",
                      f"{int(x.ganancia_x)}\\x{{}}"] + [f(x[c], 2, True) for c in ["f6_640nm", "f7_690nm", "f8_745nm", "nir_855nm"]]
                     + [f(x.mediana_11, 2, True), f(x.dif_NIR_F6, 2, True), f(x.dif_F8_F7, 2, True)])
    filas.append("\\addlinespace[2pt]")
tabla("tC_gan", ["Sensor", "Ganancia", "F6", "F7", "F8", "NIR", "Mediana F2--NIR", "NIR$-$F6", "F8$-$F7"], filas[:-1],
      "llccccccc", "Factores de ganancia (6 de noviembre): desviación de la ganancia real frente a la nominal, en \\%, "
      "referida a 4\\x{}. Las dos últimas columnas son las diferencias que afectan al NDVI y al NDRE$_2$.", "tab:C_gan")
f05 = rd("noche10_factores_05.csv")
f05c = rd("tarde11_factor05_cenit.csv")

k = rd("lab22_factor_k.csv").set_index("canal")
filas = [[lab] + [f(k.loc[c, col], d) for c in CH] for lab, col, d in
         [("$k$ (B/A)", "k_B/A", 3), ("Efecto de posición", "p_sitio", 3), ("Dispersión (\\%)", "dispersion_%", 1)]]
tabla("tC_k", [""] + canal_cab, filas, "l" + "c" * 12, "Intercomparación (22 de octubre): factor $k$ entre los sensores, "
      "efecto de la posición bajo la lámpara y dispersión entre los cuatro estimados de $k$.", "tab:C_k")

tp = rd("lab22_transmitancia_pieza.csv").set_index("canal")
m13 = rd("mediodia13_atenuador.csv"); m13c = m13[m13.corrida.str.startswith("con")].iloc[0]
a11 = rd("tarde11_atenuador.csv"); a11 = a11[a11.ganancia_x == 0.5].iloc[0]
cs = ["fy_555nm", "f6_640nm", "f7_690nm", "f8_745nm", "nir_855nm"]
filas = [["Lámina de 2~mm a 3~mm del sensor (lámpara, 22 oct.)"] + [f(tp.loc[c, "T_d"], 3) for c in cs],
         ["Atenuador de 3~mm, cielo de la tarde (11 nov., corrida 1)"] + [f(a11["T_" + c], 3) for c in cs],
         ["Atenuador de 3~mm, cielo de la tarde (11 nov., corrida 2)"] + [f(a11["T2_" + c], 3) for c in cs],
         ["Atenuador de 3~mm, sol directo (13 nov.)"] + [f(m13c["T_" + c], 3) for c in cs]]
tabla("tC_T", ["Difusor", "FY 555", "F6 640", "F7 690", "F8 745", "NIR 855"], filas, "lccccc",
      "Transmitancia de las piezas de PTFE (cociente de la señal con y sin la pieza).", "tab:C_T", tam="\\small")

an = rd("noche10_angular.csv")
filas = []
for _, x in an.sort_values(["plano", "angulo"]).iterrows():
    filas.append([str(int(x.plano)), f"{int(x.angulo):+d}°".replace("+", "$+$").replace("-", "$-$"), f(x.coseno, 3),
                  f(x.rel_f6_640nm, 3), f(x.rel_nir_855nm, 3), f(x.err_coseno_pct_nir_855nm, 1, True),
                  f(100 * (x.cociente_NIR_F6 - 1), 1, True), f(100 * (x.cociente_F8_F7 - 1), 1, True)])
tabla("tC_ang", ["Plano", "Ángulo", "Coseno", "F6 rel.", "NIR rel.", "NIR frente al coseno (\\%)", "NIR/F6 (\\%)",
                 "F8/F7 (\\%)"], filas, "llcccccc", "Respuesta angular del cenit (10 de noviembre): señal relativa a 0° "
      "interpolada en el tiempo, desviación frente al coseno y cambio de la forma espectral.", "tab:C_ang",
      nota="Cada lado incluye la desalineación de 10 a 17° del montaje; el promedio de $+$ y $-$ la cancela en primer orden.")

fu = rd("noche10_fuga_F6.csv").set_index("canal")
filas = [[lab] + [f(fu.loc[c, col], 2, True) for c in ["f4_515nm", "fxl_600nm", "f6_640nm", "f7_690nm", "f8_745nm", "nir_855nm"]]
         for lab, col in [("Con aluminio frente a sin (\\%)", "con_vs_media_sin_pct"), ("Segunda toma sin frente a la primera (\\%)", "sin2_vs_sin_pct")]]
tabla("tC_fuga", ["", "F4", "FXL", "F6", "F7", "F8", "NIR"], filas, "lcccccc",
      "Prueba de fuga lateral del cenit (lámpara a 60°).", "tab:C_fuga", tam="\\small")

fv = rd("tarde11_fov.csv")
filas = [[f(x.diametro_cm, 0), f(x.semiangulo_deg, 1), str(int(x.corridas)), f(x.F_med, 3),
          (f(x.F_min, 3) + "--" + f(x.F_max, 3)) if x.corridas > 1 else "---", f(x.F_f6, 3), f(x.F_nir, 3), f(x.F_modelo, 3)]
         for _, x in fv.iterrows()]
tabla("tC_fov", ["Disco (cm)", "Semiángulo (°)", "Corridas", "Fracción media", "Rango", "F6", "NIR", "Modelo (35°)"], filas,
      "cccccccc", "Campo de visión del nadir (11 de noviembre): fracción de la señal del blanco completo que aporta cada "
      "disco, a 12~cm de la ventana, y la del modelo de coseno recortado en 35°.", "tab:C_fov", tam="\\small")

pt = rd("lab28_ptfe_efectos_pct.csv")
cs = ["f2_425nm", "f4_515nm", "f6_640nm", "f7_690nm", "f8_745nm", "nir_855nm"]
filas = [[x.comparacion.replace("15x30", "15\\x{}30").replace("15x15", "15\\x{}15")] + [f(x[c], 1, True) for c in cs] for _, x in pt.iterrows()]
tabla("tC_ptfe", ["Comparación", "F2", "F4", "F6", "F7", "F8", "NIR"], filas, "lcccccc",
      "Láminas de PTFE como referencia (28 y 29 de octubre): cambio de la lectura (\\%), promedio de dos intentos.",
      "tab:C_ptfe")
ll = rd("lab28_llenado.csv")
filas = [[f(x.ventana_cm, 0), f(x.irradiancia_rel, 3)] + [f(x["medida_" + c], 3) for c in ["f6_640nm", "nir_855nm"]]
         + [f(x["corregida_" + c], 3) for c in ["f6_640nm", "nir_855nm"]] for _, x in ll.iterrows()]
tabla("tC_llen", ["Distancia (cm)", "Irradiancia rel.", "F6 medida", "NIR medida", "F6 corregida", "NIR corregida"], filas,
      "cccccc", "Llenado del campo de visión: lectura de la lámina de 15\\x{}30~cm al alejarla, relativa a 15~cm, sin y con "
      "la corrección por la irradiancia de la lámpara.", "tab:C_llen", tam="\\small")
au = rd("tarde11_autosombra.csv").set_index("canal")
cs = ["f2_425nm", "f4_515nm", "f6_640nm", "f7_690nm", "f8_745nm", "nir_855nm"]
filas = [[lab] + [f(au.loc[c, col], d) for c in cs] for lab, col, d in
         [("Efecto de 15 frente a 10~cm (\\%)", "efecto_15_vs_10_pct", 1), ("Error estándar (\\%)", "ee_pct", 1),
          ("Tomas vecinas, par 1 (\\%)", "vecinos_1_pct", 1), ("Tomas vecinas, par 2 (\\%)", "vecinos_2_pct", 1),
          ("Deriva a 10~cm en 4~min (\\%)", "deriva_10cm_pct", 1)]]
tabla("tC_auto", ["", "F2", "F4", "F6", "F7", "F8", "NIR"], filas, "lcccccc",
      "Autosombra de la referencia (11 de noviembre): cartón a 15 y 10~cm del nadir, alternado tres veces.", "tab:C_auto",
      tam="\\small")

sb = rd("campo26_barridos_saturacion.csv")
NB = {"sat_pasto_sol_1545": "Nadir, pasto al sol (15:53)", "sat_pasto_1700": "Nadir, pasto con sol bajo (16:01)",
      "sat_pasto_sombra": "Nadir, pasto a la sombra", "zen_nublado_20260415": "Cenit, nublado (16:55)",
      "zen_nublado_20261026": "Cenit, nublado (17:11)"}
filas = []
for key, lab in NB.items():
    x = sb[sb.barrido.str.contains(key)]
    x = x[x.barrido == x.barrido.iloc[-1]] if key.startswith("sat_pasto_s") else x
    seg = x[x.max_pct_max < 90].ganancia_x.max()
    pasos = ", ".join(f"{('0,5' if g == 0.5 else int(g))}\\x{{}}: {f(m, 0)}" for g, m in zip(x.ganancia_x, x.max_pct_max))
    filas.append([lab, pasos, (("0,5" if seg == 0.5 else str(int(seg))) + "\\x{}")])
open(OUT + "tC_sat.tex", "w").write(
    "\\begin{table}[H]\n\\centering\\footnotesize\n\\caption{Barridos de saturación en campo (26 de octubre): canal más alto "
    "(\\% de la escala) en cada ganancia y ganancia más alta por debajo del 90~\\%.}\n\\label{tab:C_sat}\n"
    "\\begin{tabularx}{\\textwidth}{@{}L{3.6cm}YL{1.6cm}@{}}\n\\toprule\nBarrido & Canal más alto por ganancia (\\%) & Ganancia segura\\\\\n\\midrule\n"
    + "\n".join(" & ".join(r) + "\\\\" for r in filas) + "\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n")

filas = [[x.corrida.replace("sin2", "sin (2)").replace("sin ", "Sin atenuador, ").replace("con ", "Con atenuador, ").replace("sin (2) ", "Sin atenuador (2), "),
          f(x.max_pct_05x, 1), f(x.espectral_pct_05x, 1), f(x.cv_nir_pct, 2), x.saturadas_1x] for _, x in m13.iterrows()]
tabla("tC_med13", ["Corrida (13 nov.)", "Canal más alto, VIS (\\%)", "Canal espectral más alto (\\%)", "CV del NIR (\\%)", "Saturadas a 1\\x{}"],
      filas, "lcccc", "Cenit con sol directo a la ganancia mínima (0,5\\x{}), sin y con el atenuador: fracción de la escala que "
      "usan el canal sin filtro (VIS, el que fija la saturación) y el canal espectral más alto.", "tab:C_med13", tam="\\small")

al = rd("tarde11_alturas.csv")
filas = []
for (dia, cod), x in al.groupby(["dia", "codigo"], sort=False):
    filas.append([dia.replace(" nov", " nov."), NOMS.get(cod, cod), str(len(x)), f(x.distancia_lidar_cm.min(), 1) + "--" + f(x.distancia_lidar_cm.max(), 1),
                  f(x.altura_cm.min(), 1) + "--" + f(x.altura_cm.max(), 1),
                  (f(x.biomasa_kg_ms_ha.min(), 0) + "--" + f(x.biomasa_kg_ms_ha.max(), 0)) if cod not in ("T", "A") else "no aplica"])
tabla("tC_alt", ["Día", "Superficie", "Tomas", "LiDAR (cm)", "Altura (cm)", "Biomasa (kg MS/ha)"], filas, "llcccc",
      "Altura y biomasa en las tomas válidas del 10 y el 11 de noviembre (suelo a 58,8~cm).", "tab:C_alt", tam="\\small",
      nota="En tierra y grava la altura aparente es el desfase de la distancia al suelo; por eso la biomasa no aplica.")
print("listo")
