"""Calibración del LiDAR TF-Nova frente a cinta métrica (6 oct. 2026): métricas y figura del documento.

Uso: python3 -I analisis/lidar_calibracion.py [carpeta_de_salida]
     (desde la carpeta MasPasto2_resultados; por defecto escribe en salidas/)

Lee 2026-10-06_lab_lidar/crudos/lidar_caracterizacion.csv (30 distancias de 5 a 150 cm, tres corridas
ida/vuelta/ida, 200 lecturas por punto) y:
  - promedia las 200 lecturas de cada punto y ajusta d_L = a d + b entre 15 y 150 cm (84 puntos);
  - calcula el error sin calibrar y con la corrección d = (d_L - b)/a, la validación cruzada
    (ajuste con dos corridas, prueba en la tercera), la precisión (desviación por punto), la
    repetibilidad (corrida 3 frente a 1), la histéresis (vuelta frente a la media de las idas) y la
    lectura cerca del sensor;
  - escribe lidar_calibracion_puntos.csv y lidar_calibracion.pdf (Fig. 6 del documento).
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "salidas")
os.makedirs(OUT, exist_ok=True)
d = pd.read_csv(os.path.join(BASE, "2026-10-06_lab_lidar", "crudos", "lidar_caracterizacion.csv"))

g = d.groupby(["corrida", "d_ref_cm"]).dist_raw.agg(["mean", "std", "count"]).reset_index()
m = g[g.d_ref_cm >= 15]
a, b = np.polyfit(m.d_ref_cm, m["mean"], 1)
r2 = np.corrcoef(m.d_ref_cm, m["mean"])[0, 1] ** 2
g["error_sin_cal_cm"] = g["mean"] - g.d_ref_cm
g["d_calibrada_cm"] = (g["mean"] - b) / a
g["error_cal_cm"] = g["d_calibrada_cm"] - g.d_ref_cm
g.round(4).to_csv(os.path.join(OUT, "lidar_calibracion_puntos.csv"), index=False)
m = g[g.d_ref_cm >= 15]
e, ec = m.error_sin_cal_cm, m.error_cal_cm
rmse = lambda x: float(np.sqrt((x ** 2).mean()))
print(f"Ajuste (15-150 cm, {len(m)} puntos): d_L = {a:.4f} d + {b:.2f} cm, R2 = {r2:.5f}; "
      f"corrección d = {1/a:.4f} d_L - {b/a:.2f} cm")
for r in (1, 2, 3):
    s = m[m.corrida == r]; ar, br = np.polyfit(s.d_ref_cm, s["mean"], 1)
    print(f"  corrida {r}: pendiente {ar:.4f}, desfase {br:.2f} cm")
print(f"Sin calibrar: RMSE {rmse(e):.2f} cm, máximo {e.abs().max():.1f} cm, sesgo medio {e.mean():.2f} cm")
print(f"Calibrado: RMSE {rmse(ec):.2f} cm, máximo {ec.abs().max():.2f} cm")
for r in (1, 2, 3):
    tr, te = m[m.corrida != r], m[m.corrida == r]
    ar, br = np.polyfit(tr.d_ref_cm, tr["mean"], 1); ee = (te["mean"] - br) / ar - te.d_ref_cm
    print(f"  validación cruzada, prueba en la corrida {r}: RMSE {rmse(ee):.2f} cm, máximo {ee.abs().max():.2f} cm")
print(f"Precisión (desviación por punto): media {m['std'].mean():.2f} cm, máxima {m['std'].max():.2f} cm, "
      f"{100*(m['std'] == 0).mean():.0f} % de los puntos sin variación")
p = m.pivot(index="d_ref_cm", columns="corrida", values="mean")
rep, hy = p[3] - p[1], p[2] - (p[1] + p[3]) / 2
print(f"Repetibilidad (corrida 3 frente a 1): diferencia media {rep.abs().mean():.2f} cm, máxima {rep.abs().max():.1f} cm")
print(f"Histéresis (vuelta frente a ida): media {hy.mean():.2f} cm, máxima {hy.abs().max():.2f} cm")
gm = g.groupby("d_ref_cm")["mean"].mean()
print(f"Cerca del sensor: 5 cm se lee como {gm.loc[5.0]:.0f} cm y 10 cm como {gm.loc[10.0]:.0f} cm")

# ---------------- figura ----------------
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6.8, "axes.spines.top": False,
                     "axes.spines.right": False})
COL = {1: "#2E7D32", 2: "#E65100", 3: "#1565C0"}
NOM = {1: "Corrida 1 (ida)", 2: "Corrida 2 (vuelta)", 3: "Corrida 3 (ida)"}
fig, ax = plt.subplots(1, 2, figsize=(5.99, 2.655))
A = ax[0]
A.axvspan(0, 15, color="0.92", zorder=0)
A.text(7.5, 75, "zona no\nconfiable", rotation=90, ha="center", va="center", fontsize=6.5, color="0.4")
x = np.array([0, 155])
A.plot(x, x, "k--", lw=0.8, label="Ideal (y = x)")
A.plot(x, a * x + b, color="0.45", lw=0.8, label=f"Ajuste: y = {a:.4f}x + {b:.2f}".replace(".", ","))
for r in (1, 2, 3):
    s = g[g.corrida == r]
    A.plot(s.d_ref_cm, s["mean"], "o", ms=2.2, color=COL[r], label=NOM[r])
A.set_xlim(0, 155); A.set_ylim(0, 155)
A.set_xlabel("Distancia de referencia, cinta (cm)"); A.set_ylabel("Distancia medida, LiDAR (cm)")
A.set_title("(a) Respuesta del sensor"); A.legend(fontsize=6, loc="upper left", frameon=False)
B = ax[1]
for r in (1, 2, 3):
    s = m[m.corrida == r]
    B.plot(s.d_ref_cm, s.error_sin_cal_cm, "-", lw=0.7, color=COL[r], alpha=0.3)
    B.plot(s.d_ref_cm, s.error_cal_cm, "o-", lw=0.9, ms=2.2, color=COL[r], label=NOM[r])
for y in (5, -5):
    B.axhline(y, color="0.5", lw=0.7, ls=":")
B.text(148, 5.15, "±5 cm (hoja de datos)", ha="right", va="bottom", fontsize=6.2, color="0.4")
B.axhline(0, color="k", lw=0.5)
B.text(148, 1.5, "calibrado", ha="right", fontsize=6.5)
B.text(148, -3.9, "sin calibrar (tenue)", ha="right", fontsize=6.5, color="0.4")
B.set_xlim(12, 152); B.set_ylim(-5.5, 6)
B.set_xlabel("Distancia de referencia, cinta (cm)"); B.set_ylabel("Error (cm)")
B.set_title("(b) Error de 15 a 150 cm"); B.legend(fontsize=6, loc="lower left", frameon=False)
fig.tight_layout(w_pad=1.5)
fig.savefig(os.path.join(OUT, "lidar_calibracion.pdf"))
print("->", os.path.join(OUT, "lidar_calibracion.pdf"))
