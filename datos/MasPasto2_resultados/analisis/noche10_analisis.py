"""Noche del 10 al 11 nov. 2026: respuesta angular del cenit, fuga de F6, E3 con luz fija y factor de 0,5x.

Uso: python3 -I analisis/noche10_analisis.py 2026-11-10_noche_angular_E3_05x/crudos derivados [figura.pdf]

Escribe en <derivados>:
  noche10_angular.csv     respuesta del cenit en cada posicion, relativa a 0 grados (interpolada en el
                          tiempo entre las lecturas de 0 grados que la rodean) y su error frente al coseno
  noche10_fuga_F6.csv     fuga_sin, fuga_con y fuga_sin2 por canal
  noche10_E3.csv          E3: pendiente de cada canal con la temperatura (por tramo y conjunta) y escalones
  noche10_factores_05.csv factores de 0,5x, 1x y 2x del nadir referidos a 4x, dos corridas
"""
import sys, os, glob, json
import numpy as np, pandas as pd

D, OUT = sys.argv[1], sys.argv[2]
FIG = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)
CH = ['f1_405nm', 'f2_425nm', 'fz_450nm', 'f3_475nm', 'f4_515nm', 'f5_550nm', 'fy_555nm', 'fxl_600nm',
      'f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm', 'vis_c1']
oscB = {int(k): v for k, v in json.load(open(os.path.join(D, 'oscuridad_B.json'))).items()}
oscA = {int(k): v for k, v in json.load(open(os.path.join(D, 'oscuridad_A.json'))).items()}


def archivo(patron):
    f = [x for x in glob.glob(os.path.join(D, patron)) if 'resumen' not in x and 'pasos' not in x]
    assert len(f) == 1, (patron, f)
    return f[0]


def medio_cenit(et):
    d = pd.read_csv(archivo(f'registro_sensorB_{et}_2026*.csv'))
    o = oscB[int(d.z_ganancia_idx.iloc[0])]
    m = {c: (d['z_' + c] - o.get(c, 0)).mean() for c in CH}
    m.update(t=d.z_t.mean(), ganancia=d.z_ganancia_x.iloc[0], max_cuentas=d.z_max_cuentas.max(),
             saturadas=int(d.z_saturado.sum()), cv_nir_pct=100 * d.z_nir_855nm.std() / d.z_nir_855nm.mean())
    return m


# ---------------- respuesta angular ----------------
filas, ceros = [], []
for p in (1, 2):
    M = {et: medio_cenit(f'ang{p}_{et}') for et in ['0a', 'mas30', 'mas60', '0b', 'menos30', 'menos60', '0c']}
    for et in ('0a', '0b', '0c'):
        ceros.append(dict(plano=p, lectura=et, **{c: M[et][c] for c in ('f6_640nm', 'nir_855nm', 'vis_c1')}))
    for et, ang, (ra, rb) in [('mas30', 30, ('0a', '0b')), ('mas60', 60, ('0a', '0b')),
                             ('menos30', -30, ('0b', '0c')), ('menos60', -60, ('0b', '0c'))]:
        a, b = M[ra], M[rb]
        fila = dict(plano=p, angulo=ang, coseno=np.cos(np.radians(ang)), max_cuentas=M[et]['max_cuentas'],
                    saturadas=M[et]['saturadas'])
        for c in CH:
            r0 = a[c] + (b[c] - a[c]) * (M[et]['t'] - a['t']) / (b['t'] - a['t'])
            fila['rel_' + c] = M[et][c] / r0
            fila['err_coseno_pct_' + c] = 100 * (fila['rel_' + c] / fila['coseno'] - 1)
        fila['cociente_NIR_F6'] = fila['rel_nir_855nm'] / fila['rel_f6_640nm']
        fila['cociente_F8_F7'] = fila['rel_f8_745nm'] / fila['rel_f7_690nm']
        filas.append(fila)
ang = pd.DataFrame(filas)
ang.to_csv(os.path.join(OUT, 'noche10_angular.csv'), index=False)
cz = pd.DataFrame(ceros)
print('Lecturas de 0 grados (repeticion al volver a poner la lampara):')
for p in (1, 2):
    s = cz[cz.plano == p].vis_c1.values
    print(f'  plano {p}: VIS 0a/0b/0c = {s[0]:.0f} / {s[1]:.0f} / {s[2]:.0f}; rango {100*(s.max()/s.min()-1):.1f} %')
from scipy.optimize import minimize_scalar
print('Respuesta relativa (VIS) y error frente al coseno:')
for p in (1, 2):
    s = ang[ang.plano == p]
    th = np.radians(s.angulo.values); y = s.rel_vis_c1.values
    o = minimize_scalar(lambda d: ((np.cos(th - d) / np.cos(d) - y) ** 2).sum(), bounds=(-0.8, 0.8), method='bounded')
    txt = ', '.join(f"{a:+d}: {v:.3f} ({e:+.0f} %)" for a, v, e in zip(s.angulo, y, s['err_coseno_pct_vis_c1']))
    sim = {a: (s[s.angulo == a].rel_vis_c1.values[0] + s[s.angulo == -a].rel_vis_c1.values[0]) / 2 for a in (30, 60)}
    print(f'  plano {p}: {txt}; desalineacion ajustada {np.degrees(o.x):.0f} grados; '
          f'promedio +/-30 {sim[30]:.3f} ({100*(sim[30]/np.cos(np.radians(30))-1):+.0f} %), '
          f'+/-60 {sim[60]:.3f} ({100*(sim[60]/0.5-1):+.0f} %)')
print('  cociente NIR/F6 frente a 0 grados: de %.3f a %.3f; F8/F7: de %.3f a %.3f' % (
    ang.cociente_NIR_F6.min(), ang.cociente_NIR_F6.max(), ang.cociente_F8_F7.min(), ang.cociente_F8_F7.max()))

# ---------------- fuga de F6 ----------------
F = {et: medio_cenit(et) for et in ('fuga_sin', 'fuga_con', 'fuga_sin2')}
fu = pd.DataFrame({et: {c: F[et][c] for c in CH} for et in F})
fu['con_vs_media_sin_pct'] = 100 * (fu.fuga_con / ((fu.fuga_sin + fu.fuga_sin2) / 2) - 1)
fu['sin2_vs_sin_pct'] = 100 * (fu.fuga_sin2 / fu.fuga_sin - 1)
fu.index.name = 'canal'
fu.to_csv(os.path.join(OUT, 'noche10_fuga_F6.csv'))
print('Fuga de F6, con aluminio frente al promedio sin aluminio (%):',
      {c: round(fu.loc[c, 'con_vs_media_sin_pct'], 2) for c in ('fxl_600nm', 'f6_640nm', 'f7_690nm', 'nir_855nm')})

# ---------------- E3 ----------------
fs = sorted(x for x in glob.glob(os.path.join(D, 'registro_sensorA_E3_ciclo_2026*.csv')) if 'resumen' not in x)
e = pd.concat([pd.read_csv(f).assign(corrida=i + 1) for i, f in enumerate(fs)], ignore_index=True)
e['min'] = (e.n_t - e.n_t.iloc[0]) / 60
for c in CH:
    e[c] = e['n_' + c] / e['n_' + c].iloc[:200].mean()
e['T'] = e.n_temp_c
r3 = e[e.corrida == 3].reset_index(drop=True)
t_quita = r3.loc[730, 'min']                     # el operador quito la bolsa en la lectura 730 de la corrida 3
# la bolsa se puso durante la corrida 2: escalon brusco de la senal
r2 = e[e.corrida == 2]
sm = r2.vis_c1.rolling(5, center=True).mean()
t_pone = r2.loc[sm.diff().idxmin(), 'min']
TR = {'sin bolsa, antes': (0.05, t_pone - 0.1), 'con bolsa': (t_pone + 0.4, t_quita - 0.2),
      'sin bolsa, despues': (t_quita + 0.7, e['min'].max())}
e['tramo'] = None
for k, (a, b) in TR.items():
    e.loc[(e['min'] >= a) & (e['min'] <= b), 'tramo'] = k
x = e.dropna(subset=['tramo'])
filas = []
for c in ['f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm', 'vis_c1']:
    X = np.column_stack([x['T'].values] + [(x.tramo == k).astype(float).values for k in TR])
    y = x[c].values * 100
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ beta
    cov = (res ** 2).sum() / (len(y) - X.shape[1]) * np.linalg.inv(X.T @ X)
    f = dict(canal=c, pendiente_conjunta_pct_por_C=beta[0], error_estandar=np.sqrt(cov[0, 0]))
    for k in TR:
        s = x[x.tramo == k]
        f['pendiente_' + k.replace(' ', '_').replace(',', '')] = np.polyfit(s['T'], 100 * s[c] / s[c].mean(), 1)[0]

    def med(a, b):
        return e[(e['min'] >= a) & (e['min'] <= b)][c].mean()
    f['escalon_al_poner_pct'] = 100 * (med(t_pone + 0.1, t_pone + 0.5) / med(t_pone - 0.5, t_pone - 0.1) - 1)
    f['escalon_al_quitar_pct'] = 100 * (med(t_quita + 0.7, t_quita + 1.1) / med(t_quita - 0.6, t_quita - 0.2) - 1)
    filas.append(f)
e3 = pd.DataFrame(filas)
e3.to_csv(os.path.join(OUT, 'noche10_E3.csv'), index=False)
print(f'E3: {len(e)} lecturas en {e["min"].max():.1f} min; temperatura de {e["T"].min():.2f} a {e["T"].max():.2f} C; '
      f'bolsa puesta en el min {t_pone:.1f} y quitada en el min {t_quita:.1f}')
print(e3.round(3).to_string(index=False))
for k, (a, b) in TR.items():
    s = x[x.tramo == k]
    print(f'  {k}: min {a:.1f}-{b:.1f}, T {s["T"].min():.2f}-{s["T"].max():.2f} C')

# ---------------- factor de 0,5x ----------------
filas = []
for f in sorted(glob.glob(os.path.join(D, 'ganancias_sensorA_nadir_T0_2026*.csv'))):
    if 'resumen' in f or 'pasos' in f:
        continue
    d = pd.read_csv(f); d = d[d.fase == 'luz']
    s = {}
    for (g, p), b in d.groupby(['n_ganancia_x', 'pasada']):
        o = oscA[int(b.n_ganancia_idx.iloc[0])]
        s[(g, p)] = {c: ((b['n_' + c] - o.get(c, 0)) / (g * b.n_t_int_ms)).mean() for c in CH}
        s[(g, p)]['cuentas_nir'] = b.n_nir_855nm.mean(); s[(g, p)]['cuentas_f6'] = b.n_f6_640nm.mean()
    for g in (0.5, 1.0, 2.0):
        fila = dict(corrida=os.path.basename(f), ganancia_x=g, temp_c=d.n_temp_c.mean(),
                    cuentas_f6=s[(g, 'ida')]['cuentas_f6'], cuentas_nir=s[(g, 'ida')]['cuentas_nir'])
        for c in CH:
            fila[c] = 100 * ((s[(g, 'ida')][c] + s[(g, 'vuelta')][c]) / (s[(4.0, 'ida')][c] + s[(4.0, 'vuelta')][c]) - 1)
        filas.append(fila)
fg = pd.DataFrame(filas)
fg.to_csv(os.path.join(OUT, 'noche10_factores_05.csv'), index=False)
print('Factores referidos a 4x (%):')
print(fg[['corrida', 'ganancia_x', 'cuentas_f6', 'f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm', 'vis_c1']].round(2).to_string(index=False))

# ---------------- figura ----------------
if FIG:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 3.2), gridspec_kw={'width_ratios': [1, 1.35]})
    tt = np.linspace(-75, 75, 200)
    a1.plot(tt, np.cos(np.radians(tt)), color='#999', lw=1, label='coseno ideal')
    for p, mk, col in [(1, 'o', '#2E6B3A'), (2, 's', '#C0622B')]:
        s = ang[ang.plano == p].sort_values('angulo')
        a1.plot(np.r_[s.angulo.values[:2], 0, s.angulo.values[2:]], np.r_[s.rel_vis_c1.values[:2], 1, s.rel_vis_c1.values[2:]],
                mk + '-', color=col, ms=5, lw=1, label=f'plano {p}')
    a1.set_xlabel('Ángulo de la lámpara (grados)'); a1.set_ylabel('Señal relativa a 0° (canal VIS)')
    a1.set_xticks([-60, -30, 0, 30, 60]); a1.set_ylim(0, 1.25); a1.grid(alpha=0.3); a1.legend(frameon=False, fontsize=8)
    a1.set_title('(a) Respuesta angular del cenit', fontsize=9, loc='left')
    for c, col, lab in [('f6_640nm', '#C0622B', 'F6'), ('f8_745nm', '#7A4FA0', 'F8'), ('nir_855nm', '#2E6B3A', 'NIR')]:
        a2.plot(e['min'], 100 * (e[c].rolling(15, center=True).mean() - 1), color=col, lw=1, label=lab)
    a2.axvspan(t_pone, t_quita, color='#F2A39A', alpha=0.25, label='bolsa puesta')
    a2.set_xlabel('Minutos'); a2.set_ylabel('Cambio de la señal (%)'); a2.set_ylim(-1.6, 0.6); a2.grid(alpha=0.3)
    b2 = a2.twinx(); b2.plot(e['min'], e['T'], color='#3F6FB5', lw=1.2, ls='--'); b2.set_ylabel('Temperatura en la caja (°C)', color='#3F6FB5')
    a2.legend(frameon=False, fontsize=7.5, loc='lower right', ncol=2)
    a2.set_title('(b) E3: señal con luz fija y temperatura', fontsize=9, loc='left')
    fig.tight_layout(); fig.savefig(FIG); print('figura:', FIG)
