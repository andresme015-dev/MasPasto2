"""Saturacion del cenit cerca del mediodia, con y sin atenuador (13 nov. 2026, ventana).

Uso: python3 -I analisis/mediodia13_analisis.py 2026-11-13_ventana_cenit_mediodia derivados

Validas (segun el operador, sin nubes sobre el sol): sin 12:54:35, con 12:55:03 y sin2 12:55:28.
Las corridas anteriores (12:49-12:54:18) quedan en crudos/descartados/ porque pasaban nubes; se
calculan aparte solo como comparacion. Escribe derivados/mediodia13_atenuador.csv.
"""
import sys, os, glob, json
import numpy as np, pandas as pd

SES, OUT = sys.argv[1], sys.argv[2]
CH = ['f1_405nm', 'f2_425nm', 'fz_450nm', 'f3_475nm', 'f4_515nm', 'f5_550nm', 'fy_555nm', 'fxl_600nm',
      'f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm']
osc = {int(k): v for k, v in json.load(open(os.path.join(SES, 'crudos', 'oscuridad_B.json'))).items()}


def corrida(f):
    d = pd.read_csv(f)
    s = pd.DataFrame({c: (d['z_' + c] - d.z_ganancia_idx.map(lambda k: osc.get(k, {}).get(c, 0)))
                      / (d.z_ganancia_x * d.z_t_int_ms) for c in CH})
    s['g'] = d.z_ganancia_x
    s['max_pct'] = 100 * d.z_max_cuentas / 65535
    s['espectral_pct'] = 100 * d.z_max_espectral / 65535
    s['vis_pct'] = 100 * d[['z_vis_c1', 'z_vis_c2', 'z_vis_c3']].max(axis=1) / 65535
    s['saturado'] = d.z_saturado.astype(bool)
    s['cv'] = 0.0
    m = s[s.g == 0.5].mean(numeric_only=True)
    m['cv_nir_pct'] = 100 * s[s.g == 0.5].nir_855nm.std() / s[s.g == 0.5].nir_855nm.mean()
    m['sat_1x'] = int(s[s.g == 1.0].saturado.sum())
    m['lecturas_1x'] = int((s.g == 1.0).sum())
    m['hora'] = os.path.basename(f).split('_')[-1][:6]
    return m


def tabla(carpeta):
    R = {}
    for f in sorted(glob.glob(os.path.join(carpeta, 'saturacion_*.csv'))):
        if 'resumen' in f:
            continue
        k = os.path.basename(f).split('ventana13_')[1].split('_2026')[0] + '_' + os.path.basename(f)[-10:-4]
        R[k] = corrida(f)
    return R


V = tabla(os.path.join(SES, 'crudos'))
sin, con, sin2 = V['sin_125435'], V['con_125503'], V['sin2_125528']
ref = {c: (sin[c] + sin2[c]) / 2 for c in CH}
filas = []
for nombre, r in [('sin 12:54:35', sin), ('con 12:55:03', con), ('sin2 12:55:28', sin2)]:
    filas.append(dict(corrida=nombre, max_pct_05x=r.max_pct, vis_pct_05x=r.vis_pct, espectral_pct_05x=r.espectral_pct,
                      cv_nir_pct=r.cv_nir_pct, saturadas_1x=f"{int(r.sat_1x)} de {int(r.lecturas_1x)}",
                      **{'T_' + c: (r[c] / ref[c] if nombre.startswith('con') else np.nan) for c in CH}))
T = pd.DataFrame(filas)
T.to_csv(os.path.join(OUT, 'mediodia13_atenuador.csv'), index=False)
print(T[['corrida', 'max_pct_05x', 'vis_pct_05x', 'espectral_pct_05x', 'cv_nir_pct', 'saturadas_1x']].round(2).to_string(index=False))
print('Transmitancia (con / promedio de las dos sin):',
      {c: round(con[c] / ref[c], 3) for c in ['fy_555nm', 'f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm']})
print('Del % de la escala a 0,5x:', round(con.max_pct / ((sin.max_pct + sin2.max_pct) / 2), 3),
      '| sin2/sin NIR:', round(100 * (sin2.nir_855nm / sin.nir_855nm - 1), 2), '%')
# proyeccion al mediodia solar y cielo completo
lat, dec = np.radians(4.6), np.radians(-18.0)
def elev(h_desde_mediodia):
    H = np.radians(15 * h_desde_mediodia)
    return np.degrees(np.arcsin(np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(H)))
e_med, e_med13 = elev(0), elev((12 + 55 / 60) - (11 + 40 / 60))
f_sol = np.sin(np.radians(e_med)) / np.sin(np.radians(e_med13))
print(f'Elevacion del sol: {e_med13:.1f} deg a las 12:55 y {e_med:.1f} deg al mediodia solar (11:40) -> factor {f_sol:.3f}')
m = (sin.max_pct + sin2.max_pct) / 2
print(f'Proyeccion sin atenuador al mediodia: {m * f_sol:.0f} % (solo por la altura del sol); '
      f'{m * f_sol * 1.07:.0f} % si ademas se suma el cielo que tapaban los edificios (~7 %)')
c = con.max_pct
print(f'Proyeccion con atenuador: {c * f_sol:.0f}-{c * f_sol * 1.07:.0f} %')
D = tabla(os.path.join(SES, 'crudos', 'descartados'))
print('Descartadas (nubes): ' + '; '.join(f"{k}: {v.max_pct:.1f} % (CV NIR {v.cv_nir_pct:.2f} %)" for k, v in D.items()))
