"""E2 en sitio y prueba integral, 10 nov. 2026 (primera parte).

Uso: python3 -I analisis/sitio10_e2.py 2026-11-10_sitio_E2_superficies derivados [figura.pdf]

Lee los archivos de la interfaz de esa sesion (interfaz/mediciones_20261110.csv y
interfaz/crudo_20261110.csv), que se guardaron SIN linea de titulos, les pone los titulos de la
version de la interfaz que los escribio, marca la validez de cada toma (criterio del operador y
avisos de la interfaz), comprueba que los pares crudos coincidan con cada medicion y calcula la
fraccion verde de las fotos de las huellas con las reglas de Canopeo (Patrignani y Ochsner, 2015):
pixel verde si R/G < 0,95, B/G < 0,95 y 2G - R - B > 20. La cinta metrica (azul) se excluye.

Escribe en <derivados>:
  sitio10_mediciones.csv   26 mediciones con titulos, codigo, toma, validez y motivo
  sitio10_canopeo_fotos.csv  fraccion verde de cada foto
  sitio10_resumen.csv      por superficie: tomas validas, NDVI, NDRE1, NDRE2, rho y fraccion verde
"""
import sys, os, csv, glob, datetime as dt
import numpy as np, pandas as pd

SES, OUT = sys.argv[1], sys.argv[2]
FIG = sys.argv[3] if len(sys.argv) > 3 else None

CAMPOS = ["id", "punto", "nota", "hora_celular", "hora_rpi", "hora_rtc", "simulado",
          "blanco_hora", "con_cenit", "pares_validos", "pares_pedidos", "ganancia_nadir", "ganancia_cenit",
          "rho_f6", "rho_f7", "rho_f8", "rho_nir", "ndvi", "ndre1", "ndre2",
          "cv_cociente_nir_pct", "luz_relativa_blanco",
          "distancia_lidar_cm", "suelo_cm", "altura_cm", "inclinacion_deg", "temp_c",
          "biomasa_kg_ms_ha", "foto", "avisos"]
CH = ['f1_405nm', 'f2_425nm', 'fz_450nm', 'f3_475nm', 'f4_515nm', 'f5_550nm', 'fy_555nm', 'fxl_600nm',
      'f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm']
MOD = ['t', 'ganancia_idx', 'ganancia_x', 't_int_ms', 'max_espectral', 'max_cuentas', 'saturado', 'vis_saturado',
       'sat_analogica', 'sat_digital'] + CH + ['vis_c1', 'vis_c2', 'vis_c3', 'var_luz_ciclos', 'temp_c']
CRUDO = ['id', 'par'] + ['n_' + c for c in MOD] + ['z_' + c for c in MOD + ['seq', 'rssi_dbm', 'desfase_s',
                                                                           'id_sensor', 'config']]

# Validez de cada fila, en el orden del archivo (0 = primera linea).
# Criterio: el operador declaro validas solo las tres ultimas tomas de T y de A; se descartan
# ademas las tomas con luz muy distinta a la del blanco (cociente de luz del cenit < 0,8),
# lecturas sin cenit, pares incompletos o CV del cociente > 5 %.
DESC = {
    0: "blanco de 15:14 reemplazado a las 15:18; CV del cociente 5,9 %",
    1: "luz al 11 % de la del blanco (nube)",
    2: "luz al 62 % de la del blanco; 2 lecturas sin cenit",
    5: "CV 4,3 %; 3 lecturas sin cenit; 4 de 5 pares",
    6: "luz al 63 % de la del blanco; CV 5,8 %; 1 lectura saturada",
    16: "luz al 64 %; CV 5,2 %; 4 de 5 pares (repetida por el operador)",
    17: "CV del cociente 21 % (repetida por el operador)",
    21: "repetida por el operador (validas solo las tres ultimas de A)",
    22: "luz al 24 % de la del blanco (nube); CV 6,8 % (repetida por el operador)",
}
NOMBRE = {"V1": "Pasto alto verde", "V2": "Pasto verde bajo", "V3": "Pasto con parche seco",
          "T": "Tierra (parche pequeno, con pasto alrededor)", "A": "Grava", "N": "Cartulina negra"}

# --- mediciones ---
m = pd.DataFrame(list(csv.reader(open(os.path.join(SES, 'interfaz', 'mediciones_20261110.csv')))), columns=CAMPOS)
NUM = ['pares_validos', 'pares_pedidos', 'rho_f6', 'rho_f7', 'rho_f8', 'rho_nir', 'ndvi', 'ndre1', 'ndre2',
       'cv_cociente_nir_pct', 'luz_relativa_blanco', 'distancia_lidar_cm', 'suelo_cm', 'altura_cm', 'temp_c']
for c in NUM:
    m[c] = pd.to_numeric(m[c], errors='coerce')
m['fila'] = range(len(m))
m['codigo'] = m.punto.str.split().str[0]
m['toma'] = m.punto.str.extract(r'toma (\d)').astype(int)
m['valida'] = ~m.fila.isin(DESC)
m['motivo_descarte'] = m.fila.map(DESC).fillna('')
m['referencia'] = 'cartulina gris'

# --- pares crudos: comprobacion de que coinciden uno a uno con cada medicion ---
c = pd.DataFrame(list(csv.reader(open(os.path.join(SES, 'interfaz', 'crudo_20261110.csv')))), columns=CRUDO)
i, ok = 0, True
for k, r in m.iterrows():
    n = int(r.pares_validos)
    p = c.iloc[i:i + n]
    i += n
    gn = '/'.join(sorted({f"{float(x):g}" for x in p.n_ganancia_x}))
    gz = '/'.join(sorted({f"{float(x):g}" for x in p.z_ganancia_x if x}))
    t0 = dt.datetime.fromisoformat(r.hora_rpi).timestamp()
    dts = p.n_t.astype(float) - t0
    good = (list(p.par.astype(int)) == list(range(n)) and gn == r.ganancia_nadir and gz == r.ganancia_cenit
            and dts.min() > -5 and dts.max() < 60)
    ok &= bool(good)
print(f"pares crudos: {i} usados de {len(c)}; coincidencia con las mediciones: {'si' if ok and i == len(c) else 'NO'}")

# --- Canopeo ---
from PIL import Image
filas = []
for f in sorted(glob.glob(os.path.join(SES, 'fotos', 'huella_*.jpg'))):
    im = np.asarray(Image.open(f).convert('RGB')).astype(float)
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    cinta = (B > G + 20) & (B > R + 60)
    with np.errstate(divide='ignore', invalid='ignore'):
        verde = (R / G < 0.95) & (B / G < 0.95) & (2 * G - R - B > 20)
    cod = os.path.basename(f).split('_')[1]
    filas.append(dict(foto=os.path.basename(f), codigo=cod, pixeles=im.shape[0] * im.shape[1],
                      cinta_pct=round(100 * cinta.mean(), 1), verde_pct=round(100 * verde[~cinta].mean(), 1)))
fc = pd.DataFrame(filas)

# --- resumen por superficie (solo tomas validas) ---
res = []
for cod in ['V1', 'V2', 'V3', 'T', 'A', 'N']:
    v = m[(m.codigo == cod) & m.valida]
    g = fc[fc.codigo == cod].verde_pct
    d = dict(codigo=cod, superficie=NOMBRE[cod], tomas_validas=len(v), tomas_totales=int((m.codigo == cod).sum()))
    for x in ['ndvi', 'ndre1', 'ndre2', 'rho_f6', 'rho_f7', 'rho_f8', 'rho_nir', 'cv_cociente_nir_pct']:
        d[x + '_media'] = round(v[x].mean(), 4)
        d[x + '_rango'] = round(v[x].max() - v[x].min(), 4)
    d['altura_lidar_media_cm'] = round(v.distancia_lidar_cm.mean(), 1) if v.distancia_lidar_cm.notna().any() else ''
    d['verde_canopeo_pct'] = round(g.mean(), 1) if len(g) else ''
    d['verde_min_pct'] = g.min() if len(g) else ''
    d['verde_max_pct'] = g.max() if len(g) else ''
    res.append(d)
rs = pd.DataFrame(res)

os.makedirs(OUT, exist_ok=True)
cols = ['fila', 'codigo', 'toma', 'valida', 'motivo_descarte', 'referencia'] + CAMPOS
m[cols].to_csv(os.path.join(OUT, 'sitio10_mediciones.csv'), index=False)
fc.to_csv(os.path.join(OUT, 'sitio10_canopeo_fotos.csv'), index=False)
rs.to_csv(os.path.join(OUT, 'sitio10_resumen.csv'), index=False)
print(rs[['codigo', 'tomas_validas', 'ndvi_media', 'ndvi_rango', 'ndre2_media', 'ndre1_media',
          'verde_canopeo_pct', 'verde_min_pct', 'verde_max_pct']].to_string(index=False))
suelo = rs[rs.codigo != 'N'].copy()
for x in ['verde_canopeo_pct', 'verde_min_pct', 'verde_max_pct']:
    suelo[x] = suelo[x].astype(float)
from scipy.stats import spearmanr
for x in ['ndvi_media', 'ndre2_media', 'ndre1_media']:
    print(x, 'Spearman con la fraccion verde:', round(float(spearmanr(suelo[x].to_numpy(float), suelo.verde_canopeo_pct.to_numpy(float))[0]), 3))

# --- figura ---
if FIG:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig = plt.figure(figsize=(7.2, 5.4))
    orden = ['V1', 'V2', 'V3', 'T', 'A']
    for j, cod in enumerate(orden):
        ax = fig.add_axes([0.02 + j * 0.196, 0.66, 0.18, 0.30])
        im = Image.open(os.path.join(SES, 'fotos', f'huella_{cod}_1.jpg'))
        w, h = im.size; s = min(w, h)
        ax.imshow(im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)))
        fila = rs[rs.codigo == cod].iloc[0]
        ax.set_title(f"{cod}: {fila.verde_canopeo_pct:.0f} % verde", fontsize=8.5)
        ax.axis('off')
    ax = fig.add_axes([0.10, 0.09, 0.85, 0.48])
    for x, mk, col, lab in [('ndvi', 'o', '#2E6B3A', 'NDVI'), ('ndre2', 's', '#C0622B', r'NDRE$_2$'),
                            ('ndre1', '^', '#7A7A7A', r'NDRE$_1$')]:
        xs = suelo.verde_canopeo_pct.astype(float)
        ys = suelo[x + '_media']
        xe = [xs - suelo.verde_min_pct.astype(float), suelo.verde_max_pct.astype(float) - xs]
        ax.errorbar(xs, ys, xerr=xe, yerr=suelo[x + '_rango'] / 2, fmt=mk, color=col, ms=6, capsize=2,
                    label=lab, lw=1)
    for _, r in suelo.iterrows():
        ax.annotate(r.codigo, (float(r.verde_canopeo_pct), r.ndvi_media), textcoords='offset points',
                    xytext=(6, -10), fontsize=8.5, color='#2E6B3A')
    ax.set_xlabel('Fracción verde de la foto de la huella (Canopeo), %')
    ax.set_ylabel('Índice (tomas válidas)')
    ax.set_xlim(0, 105); ax.set_ylim(-0.02, 0.9)
    ax.grid(alpha=0.3); ax.legend(loc='upper left', frameon=False)
    fig.savefig(FIG)
    print('figura:', FIG)
