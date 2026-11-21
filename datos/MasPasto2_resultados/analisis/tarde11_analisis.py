"""Tarde del 11 nov. 2026: par blanco-gris, V4, T y V1 con la interfaz; autosombra, campo de vision,
factor de 0,5x del cenit y atenuador con caracterizacion_espectro.py.

Uso: python3 -I analisis/tarde11_analisis.py <sesion> derivados [figura.pdf]

<sesion> contiene interfaz/ (mediciones, crudo, blancos y crudo_blancos del 11 nov.), crudos/ (archivos
de caracterizacion_espectro.py y oscuridad_A/B.json) y fotos/ (fotos de la camara de la interfaz).
El factor de ganancia de cada canal se corrige con las tablas ya medidas (referidas a 4x):
  A 0,5x: noche10_factores_05.csv (promedio de las dos corridas); A 1x y 2x: lab22_factores_ganancia.csv;
  A 8-256x y B 1-256x: casa6_factores_ganancia.csv; B 0,5x: el que se mide aqui.

Escribe en <derivados>:
  tarde11_interfaz.csv      cada medicion de la interfaz: estado, cocientes y reflectancias de los 12 canales
  tarde11_par.csv           reflectancia de Gr, N, B2 y C final frente al carton, por canal
  tarde11_superficies.csv   V4, T y V1 (11 nov.) y las superficies del 10 nov.: indices con referencia gris y
                            convertidos a carton blanco, y fraccion verde de la foto de la interfaz
  tarde11_autosombra.csv    cociente nadir/cenit de cada corrida y efecto 15 cm frente a 10 cm por canal
  tarde11_fov.csv           respuesta normalizada a cada disco y semiangulo equivalente
  tarde11_factor05_cenit.csv factor de 0,5x, 1x y 2x del cenit referido a 4x (dos metodos)
  tarde11_atenuador.csv     transmitancia del atenuador por canal y ganancia
"""
import sys, os, glob, json, csv
import numpy as np, pandas as pd

SES, OUT = sys.argv[1], sys.argv[2]
FIG = sys.argv[3] if len(sys.argv) > 3 else None
DER = OUT
os.makedirs(OUT, exist_ok=True)
D = os.path.join(SES, 'crudos')
I = os.path.join(SES, 'interfaz')
CH = ['f1_405nm', 'f2_425nm', 'fz_450nm', 'f3_475nm', 'f4_515nm', 'f5_550nm', 'fy_555nm', 'fxl_600nm',
      'f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm']
osc = {s: {int(k): v for k, v in json.load(open(os.path.join(D, f'oscuridad_{s}.json'))).items()} for s in 'AB'}


def indice(a, b):
    return (a - b) / (a + b)


def indices(r):
    """r: dict o Series con f6, f7, f8 y nir."""
    return dict(ndvi=indice(r['nir_855nm'], r['f6_640nm']), ndre1=indice(r['nir_855nm'], r['f8_745nm']),
                ndre2=indice(r['f8_745nm'], r['f7_690nm']))


# ---------------- factores de ganancia (% referidos a 4x) ----------------
FG = {('A', 4.0): {c: 0.0 for c in CH}, ('B', 4.0): {c: 0.0 for c in CH}}
for r in csv.DictReader(open(os.path.join(DER, 'casa6_factores_ganancia.csv'))):
    FG[(r['sensor'], float(r['ganancia_x']))] = {c: float(r[c]) for c in CH}
for r in csv.DictReader(open(os.path.join(DER, 'lab22_factores_ganancia.csv'), encoding='utf-8-sig')):
    if r['sensor'] == 'A' and float(r['ganancia_x']) in (1.0, 2.0):
        FG[('A', float(r['ganancia_x']))] = {c: float(r[c]) for c in CH}
n05 = pd.read_csv(os.path.join(DER, 'noche10_factores_05.csv'))
FG[('A', 0.5)] = {c: n05[n05.ganancia_x == 0.5][c].mean() for c in CH}


def s_norm(df, p, sensor, usar_factor=True):
    """Senal normalizada por canal: (S - oscuridad) / (G * t_int) / (1 + factor/100)."""
    out = {}
    for c in CH:
        o = df[p + 'ganancia_idx'].astype(int).map(lambda k: osc[sensor].get(k, {}).get(c, 0.0))
        g = df[p + 'ganancia_x'].astype(float)
        f = g.map(lambda x: FG.get((sensor, x), {}).get(c, np.nan)) if usar_factor else 0.0
        if usar_factor:
            f = f.fillna(0.0)
        out[c] = (df[p + c].astype(float) - o) / (g * df[p + 't_int_ms'].astype(float)) / (1 + f / 100)
    return pd.DataFrame(out, index=df.index)


def archivo(patron):
    f = [x for x in glob.glob(os.path.join(D, patron)) if 'resumen' not in x and 'pasos' not in x]
    assert len(f) == 1, (patron, f)
    return f[0]


# =========================================================================================
# 1. Interfaz: integridad
# =========================================================================================
M = pd.read_csv(os.path.join(I, 'mediciones_20261111.csv'))
C = pd.read_csv(os.path.join(I, 'crudo_20261111.csv'))
CB = pd.read_csv(os.path.join(I, 'crudo_blancos_20261111.csv'))
M = M[M.id >= 13].copy()
fotos = {os.path.basename(f): os.path.getsize(f) for f in glob.glob(os.path.join(SES, 'fotos', 'medicion_*.jpg'))}
print('Interfaz, 11 nov. tarde:', len(M), 'mediciones, ids', M.id.min(), '-', M.id.max(),
      '| pares crudos', int(C[C.id >= 13].shape[0]), '| ids repetidos:', int(M.id.duplicated().sum()))
for _, r in M.iterrows():
    n = int(r.pares_validos)
    k = int((C.id == r.id).sum())
    assert k == n, (r.id, k, n)
vacias = [f for f, s in fotos.items() if s == 0]
print('  fotos de la tarde:', sum(1 for f in fotos if '_20261111_13' in f), '| vacias (0 bytes):', vacias)

# =========================================================================================
# 2. Cocientes de los 12 canales en cada medicion y en cada blanco (con factores de ganancia)
# =========================================================================================


def cociente(df):
    sn = s_norm(df, 'n_', 'A')
    sz = s_norm(df, 'z_', 'B')
    return (sn / sz).mean(), (sn / sz).std() / (sn / sz).mean() * 100, sz['nir_855nm'].mean()


QB = {}
for h, b in CB.groupby('hora_blanco'):
    q, cv, luz = cociente(b)
    QB[h] = dict(q=q, cv_nir=cv['nir_855nm'], luz=luz, gn=sorted(set(b.n_ganancia_x)), gz=sorted(set(b.z_ganancia_x)))
filas = []
for _, r in M.iterrows():
    p = C[C.id == r.id]
    fila = dict(id=int(r.id), punto=r.punto, hora=r.hora_rpi[11:19], blanco=r.blanco_hora[11:19],
                pares=int(r.pares_validos), gan_nadir=r.ganancia_nadir, gan_cenit=r.ganancia_cenit,
                distancia_lidar_cm=r.distancia_lidar_cm, foto=r.foto if isinstance(r.foto, str) else '',
                foto_bytes=fotos.get(r.foto, '') if isinstance(r.foto, str) else '')
    if len(p):
        q, cv, luz = cociente(p)
        qb = QB[r.blanco_hora]['q']
        rho = q / qb
        fila.update(cv_nir_pct=cv['nir_855nm'], luz_rel=luz / QB[r.blanco_hora]['luz'])
        fila.update({'rho_' + c: rho[c] for c in CH})
        fila.update(indices(rho))
        # comprobacion contra lo que calculo la interfaz (sin factores de ganancia)
        fila['ndvi_interfaz'] = r.ndvi
    filas.append(fila)
T = pd.DataFrame(filas)
T['codigo'] = T.punto.str.split().str[0]
T['valida'] = T.pares > 0
T['motivo'] = np.where(T.pares == 0, 'sin pares validos (cenit sin datos); repetida como id 18', '')
T.to_csv(os.path.join(OUT, 'tarde11_interfaz.csv'), index=False)
print('\nBlancos de la tarde:')
for h, v in QB.items():
    if h.startswith('2026-11-11T13'):
        print(f'  {h[11:]}  nadir {v["gn"]}  cenit {v["gz"]}  CV NIR {v["cv_nir"]:.2f} %  luz cenit NIR {v["luz"]:.3f}')
print('\nNDVI con factores de ganancia frente al de la interfaz (dif. max.):',
      round(float((T.ndvi - T.ndvi_interfaz).abs().max()), 4))

# =========================================================================================
# 3. Par blanco-gris (referencia: carton solo, blanco de las 13:36:21)
# =========================================================================================
par = T[T.codigo.isin(['Gr', 'N', 'B2', 'C']) & T.valida].copy()
# C final (carton medido como superficie al final del par) leyo ~6 % por encima del blanco de las 13:36:
# el cociente nadir/cenit sobre el carton cambio mientras la luz subia. Se corrige suponiendo un cambio
# lineal en el tiempo entre el blanco y C final; se guarda tambien la version sin corregir.
import datetime as dt
seg = lambda h: (dt.datetime.strptime(h, '%H:%M:%S') - dt.datetime(1900, 1, 1)).total_seconds()
cfin = par[par.codigo == 'C'].iloc[0]
t0, t1 = seg('13:36:21'), seg(cfin.hora)
for c in CH:
    par['rhoraw_' + c] = par['rho_' + c]
    par['rho_' + c] = par['rho_' + c] / (1 + (cfin['rho_' + c] - 1) * (par.hora.map(seg) - t0) / (t1 - t0))
PAR_RAW = par.groupby('codigo')[['rhoraw_' + c for c in CH]].mean()
P = par.groupby('codigo')[['rho_' + c for c in CH]].agg(['mean', 'std'])
filasP = []
for cod in ['Gr', 'N', 'B2', 'C']:
    d = dict(codigo=cod, tomas=int((par.codigo == cod).sum()))
    for c in CH:
        d[c] = P.loc[cod, ('rho_' + c, 'mean')]
        d[c + '_sd'] = P.loc[cod, ('rho_' + c, 'std')]
    d.update(indices({c: d[c] for c in CH}))
    for c in CH:
        d[c + '_sin_corregir'] = PAR_RAW.loc[cod, 'rhoraw_' + c]
    filasP.append(d)
PAR = pd.DataFrame(filasP)
PAR.to_csv(os.path.join(OUT, 'tarde11_par.csv'), index=False)
print('\nPar frente al carton (rho medio):')
print(PAR[['codigo', 'tomas', 'f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm', 'ndvi', 'ndre2', 'f6_640nm_sin_corregir', 'nir_855nm_sin_corregir']].round(4).to_string(index=False))
g = {c: float(PAR.loc[PAR.codigo == 'Gr', c].iloc[0]) for c in CH}            # gris frente a carton

# =========================================================================================
# 4. Superficies: 11 nov. (V4, T, V1) y 10 nov., con referencia gris y convertidas a carton
# =========================================================================================
sup = []
for cod in ['V4', 'T', 'V1']:
    v = T[T.codigo == cod]
    for _, r in v.iterrows():
        rg = {c: r['rho_' + c] for c in CH}
        rc = {c: rg[c] * g[c] for c in CH}
        sup.append(dict(dia='11 nov', codigo=cod, id=r.id, **{k + '_gris': x for k, x in indices(rg).items()},
                        **{k + '_carton': x for k, x in indices(rc).items()}, distancia_lidar_cm=r.distancia_lidar_cm,
                        foto=r.foto))
s10 = pd.read_csv(os.path.join(DER, 'sitio10_mediciones.csv'))
s10 = s10[s10.valida & (s10.codigo != 'N')]
for _, r in s10.iterrows():
    rg = {'f6_640nm': r.rho_f6, 'f7_690nm': r.rho_f7, 'f8_745nm': r.rho_f8, 'nir_855nm': r.rho_nir}
    rc = {c: rg[c] * g[c] for c in rg}
    sup.append(dict(dia='10 nov', codigo=r.codigo, id=r.fila, **{k + '_gris': x for k, x in indices(rg).items()},
                    **{k + '_carton': x for k, x in indices(rc).items()}, distancia_lidar_cm=r.distancia_lidar_cm,
                    foto=''))
S = pd.DataFrame(sup)

# fraccion verde (Canopeo) de las fotos de la camara de la interfaz
from PIL import Image


def verde(f):
    im = np.asarray(Image.open(f).convert('RGB')).astype(float)
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    cinta = (B > G + 20) & (B > R + 60)          # cinta metrica azul, excluida (como el 10 nov.)
    with np.errstate(divide='ignore', invalid='ignore'):
        v = (R / G < 0.95) & (B / G < 0.95) & (2 * G - R - B > 20)
    return 100 * v[~cinta].mean()


# la foto de la medicion 32 quedo vacia en la Raspberry; el operador la recupero de la captura de la interfaz
RECUP = {'medicion_0032_20261111_135642.jpg': 'medicion_0032_recuperada_captura.png'}


def foto_ok(f):
    if not (isinstance(f, str) and f):
        return None
    if fotos.get(f, 0) > 0:
        return os.path.join(SES, 'fotos', f)
    r = RECUP.get(f)
    return os.path.join(SES, 'fotos', r) if r and os.path.exists(os.path.join(SES, 'fotos', r)) else None


S['foto_usada'] = [os.path.basename(foto_ok(f)) if foto_ok(f) else '' for f in S.foto]
S['verde_pct'] = [verde(foto_ok(f)) if foto_ok(f) else np.nan for f in S.foto]
S.to_csv(os.path.join(OUT, 'tarde11_superficies.csv'), index=False)
RS = S.groupby(['dia', 'codigo']).agg(n=('ndvi_gris', 'size'), ndvi_gris=('ndvi_gris', 'mean'),
                                      ndvi_gris_rango=('ndvi_gris', lambda x: x.max() - x.min()),
                                      ndre2_gris=('ndre2_gris', 'mean'), ndvi_carton=('ndvi_carton', 'mean'),
                                      ndre2_carton=('ndre2_carton', 'mean'), ndre1_carton=('ndre1_carton', 'mean'),
                                      verde_pct=('verde_pct', 'mean'), lidar=('distancia_lidar_cm', 'mean')).reset_index()
print('\nSuperficies (tomas validas):')
print(RS.round(3).to_string(index=False))

# =========================================================================================
# 5. Autosombra: cociente nadir/cenit, 10 frente a 15 cm (A-B-A-B-A-B)
# =========================================================================================
au = []
for f in sorted(glob.glob(os.path.join(D, 'registro_sensorA-B_autosombra_1[05]cm_[123]_2026*.csv'))):
    if 'resumen' in f:
        continue
    d = pd.read_csv(f)
    hora = os.path.basename(f).split('_')[-1][:6]
    if hora < '164800':          # intentos anteriores con el cenit fallando (15:42 y 16:28)
        continue
    sin_z = int(d.z_t.isna().sum())
    if sin_z:
        print(f'  autosombra {d.etiqueta.iloc[0]}: {sin_z} lecturas sin cenit (se excluyen)')
    d = d[d.z_t.notna()].reset_index(drop=True)
    q = s_norm(d, 'n_', 'A') / s_norm(d, 'z_', 'B')
    et = d.etiqueta.iloc[0]
    for i in range(len(d)):
        au.append(dict(etiqueta=et, dist_cm=int(et.split('_')[1][:2]), rep=int(et[-1]), t=d.n_t.iloc[i],
                       gn=d.n_ganancia_x.iloc[i], gz=d.z_ganancia_x.iloc[i], **q.iloc[i].to_dict()))
A = pd.DataFrame(au)
A['min'] = (A.t - A.t.min()) / 60
res = []
for c in CH:
    y = np.log(A[c].to_numpy())
    X = np.column_stack([np.ones(len(A)), A['min'], A['min'] ** 2, (A.dist_cm == 15).astype(float)])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    cov = (e @ e / (len(y) - X.shape[1])) * np.linalg.inv(X.T @ X)
    m = A.groupby('etiqueta')[c].mean()
    pares = [m['autosombra_15cm_1'] / ((m['autosombra_10cm_1'] + m['autosombra_10cm_2']) / 2),
             m['autosombra_15cm_2'] / ((m['autosombra_10cm_2'] + m['autosombra_10cm_3']) / 2),
             m['autosombra_15cm_3'] / m['autosombra_10cm_3']]
    res.append(dict(canal=c, efecto_15_vs_10_pct=100 * (np.exp(b[3]) - 1), ee_pct=100 * np.sqrt(cov[3, 3]),
                    vecinos_1_pct=100 * (pares[0] - 1), vecinos_2_pct=100 * (pares[1] - 1),
                    ultimo_pct=100 * (pares[2] - 1),
                    deriva_10cm_pct=100 * (m['autosombra_10cm_3'] / m['autosombra_10cm_1'] - 1),
                    cv_dentro_pct=float(A.groupby('etiqueta')[c].apply(lambda x: x.std() / x.mean() * 100).mean())))
AU = pd.DataFrame(res)
AU.to_csv(os.path.join(OUT, 'tarde11_autosombra.csv'), index=False)
print('\nAutosombra (cociente nadir/cenit, 15 cm frente a 10 cm, %):')
print(AU.round(2).to_string(index=False))
print('  ganancias nadir/cenit por corrida:', A.groupby('etiqueta')[['gn', 'gz']].agg(lambda x: sorted(set(x))).to_dict('index'))

# =========================================================================================
# 6. Campo de vision a 15 cm: discos blancos sobre tela negra
# =========================================================================================
fv = {}
for f in sorted(glob.glob(os.path.join(D, 'registro_sensorA-B_fov_*_2026*.csv'))):
    if 'resumen' in f:
        continue
    d = pd.read_csv(f)
    et = d.etiqueta.iloc[0]
    if d.z_t.isna().any():
        print(f'  {et} ({os.path.basename(f)[-10:-4]}): {int(d.z_t.isna().sum())} lecturas sin cenit (se excluyen)')
    d = d[d.z_t.notna()].reset_index(drop=True)
    q = (s_norm(d, 'n_', 'A') / s_norm(d, 'z_', 'B')).mean()
    fv.setdefault(et, []).append(dict(archivo=os.path.basename(f), n=len(d), t=d.n_t.mean(), q=q,
                                      gn=sorted(set(d.n_ganancia_x)), gz=sorted(set(d.z_ganancia_x))))
H = 12.0          # distancia de la ventana del nadir a la lamina medida por el operador (12 cm; no los 10 cm de siempre)
neg = {c: (fv['fov_negro_1'][0]['q'][c] + fv['fov_negro_2'][0]['q'][c]) / 2 for c in CH}
bl = fv['fov_blanco'][-1]['q']          # la completa (17:03:57); la de 17:03:23 tiene 6 lecturas con la ganancia cambiando
CHF = ['fy_555nm', 'fxl_600nm', 'f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm']
filasF = []
for et, lst in fv.items():
    for k, x in enumerate(lst):
        d_cm = float(et[-2:]) if et.startswith('fov_d') else np.nan
        fila = dict(etiqueta=et, archivo=x['archivo'], lecturas=x['n'], completa=x['n'] >= 10,
                    diametro_cm=d_cm, gan_nadir=x['gn'], gan_cenit=x['gz'])
        for c in CH:
            fila['F_' + c] = (x['q'][c] - neg[c]) / (bl[c] - neg[c])
        fila['F_med'] = float(np.median([fila['F_' + c] for c in CHF]))
        if d_cm == d_cm:
            th = np.degrees(np.arctan(d_cm / 2 / H))
            fila['semiangulo_deg'] = th
            fila['F_coseno_hemisferio'] = np.sin(np.radians(th)) ** 2
        filasF.append(fila)
FV = pd.DataFrame(filasF).sort_values(['diametro_cm', 'etiqueta', 'archivo'])
# por disco: promedio de las corridas completas (d10 y d14 se repitieron; la diferencia entre repeticiones
# es la incertidumbre de poner el disco y del cambio de luz del atardecer)
FD = FV[FV.diametro_cm.notna() & FV.completa].groupby('diametro_cm').agg(
    semiangulo_deg=('semiangulo_deg', 'first'), F_coseno_hemisferio=('F_coseno_hemisferio', 'first'),
    corridas=('F_med', 'size'), F_med=('F_med', 'mean'), F_min=('F_med', 'min'), F_max=('F_med', 'max'),
    F_f6=('F_f6_640nm', 'mean'), F_nir=('F_nir_855nm', 'mean')).reset_index()
# modelo: respuesta coseno recortada en un semiangulo maximo: F = min(1, sin^2(th) / sin^2(th_max))
ths = np.arange(15, 50.01, 0.1)
sse = [((np.minimum(1, np.sin(np.radians(FD.semiangulo_deg)) ** 2 / np.sin(np.radians(t)) ** 2) - FD.F_med) ** 2).sum() for t in ths]
th_max = float(ths[int(np.argmin(sse))])
rms = float(np.sqrt(min(sse) / len(FD)))
# rango: ajustes con cada combinacion de repeticiones
alts = []
r10 = FV[(FV.diametro_cm == 10) & FV.completa].F_med.tolist(); r14 = FV[(FV.diametro_cm == 14) & FV.completa].F_med.tolist()
for a10 in r10:
    for a14 in r14:
        y = FD.F_med.copy(); y[FD.diametro_cm == 10] = a10; y[FD.diametro_cm == 14] = a14
        e = [((np.minimum(1, np.sin(np.radians(FD.semiangulo_deg)) ** 2 / np.sin(np.radians(t)) ** 2) - y) ** 2).sum() for t in ths]
        alts.append(float(ths[int(np.argmin(e))]))
for Hs in (12.5, 13.0):          # sensibilidad: chip hundido 4-5 mm detras de la ventana, y 1 cm de error
    th_s = np.degrees(np.arctan(FD.diametro_cm / 2 / Hs))
    e = [((np.minimum(1, np.sin(np.radians(th_s)) ** 2 / np.sin(np.radians(t)) ** 2) - FD.F_med) ** 2).sum() for t in ths]
    FD[f'th_max_H{Hs*10:.0f}mm_deg'] = float(ths[int(np.argmin(e))])
FD['F_modelo'] = np.minimum(1, np.sin(np.radians(FD.semiangulo_deg)) ** 2 / np.sin(np.radians(th_max)) ** 2)
FD['th_max_ajuste_deg'] = th_max
FD['th_max_min_deg'] = min(alts); FD['th_max_max_deg'] = max(alts); FD['rms_ajuste'] = rms
FV.to_csv(os.path.join(OUT, 'tarde11_fov_corridas.csv'), index=False)
FD.to_csv(os.path.join(OUT, 'tarde11_fov.csv'), index=False)
th50 = np.degrees(np.arcsin(np.sqrt(0.5) * np.sin(np.radians(th_max))))
th90 = np.degrees(np.arcsin(np.sqrt(0.9) * np.sin(np.radians(th_max))))
print('\nCampo de vision (fraccion de la senal del blanco entero; lamina a 12 cm de la ventana):')
print(FV[['etiqueta', 'archivo', 'lecturas', 'semiangulo_deg', 'F_f6_640nm', 'F_nir_855nm', 'F_med']].round(3).to_string(index=False))
print(FD.round(3).to_string(index=False))
print(f'  ajuste coseno recortado: th_max = {th_max:.1f} deg (con las otras repeticiones: {min(alts):.1f}-{max(alts):.1f}); rms {rms:.3f}')
print(f"  con 12,5 cm: {FD.th_max_H125mm_deg.iloc[0]:.1f} deg; con 13 cm: {FD.th_max_H130mm_deg.iloc[0]:.1f} deg")
print(f'  50 % de la senal dentro de {th50:.1f} deg, 90 % dentro de {th90:.1f} deg')
for h in (50, 55):
    print(f'  a {h} cm: circulo del 50 % = {2*h*np.tan(np.radians(th50)):.0f} cm, del 90 % = {2*h*np.tan(np.radians(th90)):.0f} cm, total = {2*h*np.tan(np.radians(th_max)):.0f} cm')
print('  negro_2/negro_1 NIR:', round(fv['fov_negro_2'][0]['q']['nir_855nm'] / fv['fov_negro_1'][0]['q']['nir_855nm'], 3),
      '| negro/blanco NIR:', round(neg['nir_855nm'] / bl['nir_855nm'], 3))

# =========================================================================================
# 7. Factor de 0,5x del cenit (cielo de las 17:06, poca luz)
# =========================================================================================
d = pd.read_csv(archivo('ganancias_sensorB_cenit_T0_cielo_2026*.csv'))
d = d[d.fase == 'luz'].copy()
s = s_norm(d, 'z_', 'B', usar_factor=False)
d = pd.concat([d[['z_ganancia_x', 'pasada', 'z_t']], s], axis=1)
d['min'] = (d.z_t - d.z_t.min()) / 60
fl = []
for gx in (0.5, 1.0, 2.0):
    fila = dict(ganancia_x=gx)
    for c in CH:
        m = d.groupby(['z_ganancia_x', 'pasada'])[c].mean()
        fila[c + '_simetrico'] = 100 * ((m[(gx, 'ida')] + m[(gx, 'vuelta')]) / (m[(4.0, 'ida')] + m[(4.0, 'vuelta')]) - 1)
        # regresion: log s = a_g + b t + c t^2 (la luz caia en el atardecer)
        gs = [0.5, 1.0, 2.0, 4.0]
        X = np.column_stack([(d.z_ganancia_x == x).astype(float) for x in gs] + [d['min'], d['min'] ** 2])
        y = np.log(d[c].clip(lower=1e-9))
        b, *_ = np.linalg.lstsq(X, y, rcond=None)
        e = y - X @ b
        cov = (e @ e / (len(y) - X.shape[1])) * np.linalg.inv(X.T @ X)
        i, j = gs.index(gx), 3
        fila[c + '_regresion'] = 100 * (np.exp(b[i] - b[j]) - 1)
        fila[c + '_ee'] = 100 * np.sqrt(cov[i, i] + cov[j, j] - 2 * cov[i, j])
    fila['cuentas_nir'] = float(pd.read_csv(archivo('ganancias_sensorB_cenit_T0_cielo_2026*.csv')).query(
        'fase == "luz" and z_ganancia_x == @gx').z_nir_855nm.mean())
    fl.append(fila)
F05 = pd.DataFrame(fl)
F05.to_csv(os.path.join(OUT, 'tarde11_factor05_cenit.csv'), index=False)
print('\nFactor del cenit referido a 4x (%), simetrico | regresion +- ee:')
for _, r in F05.iterrows():
    print(f"  {r.ganancia_x}x (NIR {r.cuentas_nir:.0f} cuentas): " + '; '.join(
        f"{c[:3]} {r[c + '_simetrico']:+.2f} | {r[c + '_regresion']:+.2f}+-{r[c + '_ee']:.2f}"
        for c in ['f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm']))
luz = d.groupby('pasada').apply(lambda x: x['nir_855nm'].iloc[[0, -1]].tolist())
print('  caida de la luz durante el barrido (NIR, primera y ultima lectura de cada pasada):', luz.to_dict())

# =========================================================================================
# 8. Atenuador (lamina de PTFE de 3 mm sobre la capsula del cenit)
# =========================================================================================
corr = {'sin_164405': 'con atenuador (rotulada mediodia_sin por error; descartada)',
        'sin_164500': 'sin atenuador', 'con_164600': 'con atenuador', 'sin2_164636': 'sin atenuador (repeticion)'}
at = {}
for f in sorted(glob.glob(os.path.join(D, 'saturacion_sensorB_mediodia_*_2026*.csv'))):
    if 'resumen' in f:
        continue
    k = os.path.basename(f).split('mediodia_')[1].split('_2026')[0] + '_' + os.path.basename(f)[-10:-4]
    d = pd.read_csv(f)
    s = s_norm(d, 'z_', 'B', usar_factor=False)
    s['g'] = d.z_ganancia_x
    s['max_pct'] = 100 * d.z_max_cuentas / 65535
    at[k] = s.groupby('g').mean()
fa = []
for gx in (0.5, 1.0, 2.0):
    sin = (at['sin_164500'].loc[gx, CH] + at['sin2_164636'].loc[gx, CH]) / 2
    fila = dict(ganancia_x=gx, max_pct_sin=at['sin_164500'].loc[gx, 'max_pct'], max_pct_con=at['con_164600'].loc[gx, 'max_pct'],
                max_pct_sin2=at['sin2_164636'].loc[gx, 'max_pct'], max_pct_descartada=at['sin_164405'].loc[gx, 'max_pct'])
    for c in CH:
        fila['T_' + c] = at['con_164600'].loc[gx, c] / sin[c]
        fila['T2_' + c] = at['sin_164405'].loc[gx, c] / sin[c]     # la corrida descartada tambien tenia la lamina
        fila['sin2_vs_sin_' + c] = 100 * (at['sin2_164636'].loc[gx, c] / at['sin_164500'].loc[gx, c] - 1)
        fila['descartada_vs_con_' + c] = 100 * (at['sin_164405'].loc[gx, c] / at['con_164600'].loc[gx, c] - 1)
    fa.append(fila)
AT = pd.DataFrame(fa)
AT.to_csv(os.path.join(OUT, 'tarde11_atenuador.csv'), index=False)
print('\nAtenuador: transmitancia (con / promedio de las dos sin):')
print(AT[['ganancia_x', 'max_pct_sin', 'max_pct_con', 'max_pct_sin2', 'max_pct_descartada'] +
         ['T_' + c for c in ['fy_555nm', 'f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm']] +
         ['sin2_vs_sin_nir_855nm', 'descartada_vs_con_nir_855nm']].round(3).to_string(index=False))
print(AT[['ganancia_x'] + ['T2_' + c for c in ['fy_555nm', 'f6_640nm', 'f7_690nm', 'f8_745nm', 'nir_855nm']]].round(3).to_string(index=False))
print('  corridas:', corr)

# =========================================================================================
# Figura
# =========================================================================================
if FIG:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})
    fig, ax = plt.subplots(2, 2, figsize=(7.4, 5.6))
    wl = [405, 425, 450, 475, 515, 550, 555, 600, 640, 690, 745, 855]
    a = ax[0, 0]
    for cod, col, lab in [('Gr', '#7A7A7A', 'Cartulina gris'), ('B2', '#C0622B', 'Pliego blanco'),
                          ('N', '#222222', 'Cartulina negra')]:
        r = PAR[PAR.codigo == cod].iloc[0]
        a.errorbar(wl, [r[c] for c in CH], yerr=[r[c + '_sd'] for c in CH], marker='o', ms=3.5, color=col,
                   label=lab, lw=1, capsize=1.5)
    a.set_xlabel('Longitud de onda (nm)'); a.set_ylabel('Reflectancia frente al cartón')
    a.set_ylim(0, 1.5); a.grid(alpha=.3); a.legend(frameon=False, fontsize=7.5, loc='center right'); a.set_title('a) Par de referencia', loc='left')
    a = ax[0, 1]
    orden = [('11 nov', 'V1'), ('10 nov', 'V1'), ('10 nov', 'V2'), ('10 nov', 'V3'), ('11 nov', 'V4'),
             ('10 nov', 'T'), ('11 nov', 'T'), ('10 nov', 'A')]
    xs = np.arange(len(orden))
    for k, (x, mk, col, lab) in enumerate([('ndvi_gris', 'o', '#9DB89F', 'NDVI, ref. gris'),
                                           ('ndvi_carton', 'o', '#2E6B3A', 'NDVI, ref. cartón'),
                                           ('ndre2_carton', 's', '#C0622B', r'NDRE$_2$, ref. cartón')]):
        ys = [float(RS[(RS.dia == d_) & (RS.codigo == c_)][x].iloc[0]) for d_, c_ in orden]
        a.plot(xs + (k - 1) * 0.18, ys, mk, color=col, label=lab, ms=4.5, ls='none')
    a.set_xticks(xs); a.set_xticklabels([f'{c}\n{d_[:2]}' for d_, c in orden], fontsize=7.5)
    a.set_ylabel('Índice'); a.grid(alpha=.3, axis='y'); a.legend(frameon=False, fontsize=7)
    a.set_title('b) Superficies (10 y 11 nov.)', loc='left')
    a = ax[1, 0]
    for et, g_ in A.groupby('etiqueta'):
        col = '#2E6B3A' if '10cm' in et else '#C0622B'
        a.plot(g_['min'], g_['nir_855nm'], '.', color=col, ms=4)
    a.plot([], [], '.', color='#2E6B3A', label='10 cm'); a.plot([], [], '.', color='#C0622B', label='15 cm')
    a.set_xlabel('Minuto (desde 16:48)'); a.set_ylabel('Cociente nadir/cenit, NIR')
    e_ = AU.set_index('canal').loc['nir_855nm', 'efecto_15_vs_10_pct']
    a.set_title(f'c) Autosombra: 15 cm lee {e_:+.1f} % (NIR)', loc='left'); a.grid(alpha=.3); a.legend(frameon=False)
    a = ax[1, 1]
    th = np.linspace(0, 50, 200)
    a.plot(th, np.sin(np.radians(th)) ** 2, '--', color='#7A7A7A', lw=1, label='Coseno, hemisferio completo')
    a.plot(th, np.minimum(1, np.sin(np.radians(th)) ** 2 / np.sin(np.radians(th_max)) ** 2), '-', color='#C0622B',
           lw=1, label=f'Coseno recortado a {th_max:.0f}°')
    fc = FV[FV.diametro_cm.notna() & FV.completa]
    a.plot(fc.semiangulo_deg, fc.F_med, 'o', color='#2E6B3A', ms=4, label='Discos (cada corrida)')
    for _, r in FD.iterrows():
        a.annotate(f"{r.diametro_cm:.0f} cm", (r.semiangulo_deg, r.F_max), textcoords='offset points',
                   xytext=(-8, 5), fontsize=7)
    a.set_xlabel('Semiángulo del disco visto desde el chip (°)'); a.set_ylabel('Fracción de la señal del blanco')
    a.set_ylim(0, 1.15); a.grid(alpha=.3); a.legend(frameon=False, fontsize=7, loc='lower right')
    a.set_title('d) Campo de visión (lámina a 12 cm)', loc='left')
    fig.tight_layout()
    fig.savefig(FIG)
    print('figura:', FIG)

# =========================================================================================
# 9. Altura del LiDAR y biomasa (10 y 11 nov.). El operador confirmo que el baston no cambio de largo,
#    asi que la distancia al suelo escrita el 10 nov. (58,8 cm) vale para las dos sesiones.
# =========================================================================================
s10 = pd.read_csv(os.path.join(DER, 'sitio10_mediciones.csv'))
s10 = s10[s10.valida & (s10.codigo != 'N')].assign(dia='10 nov')
m11 = pd.read_csv(os.path.join(I, 'mediciones_20261111.csv'))
m11 = m11[m11.id >= 24].assign(dia='11 nov', codigo=lambda x: x.punto.str.split().str[0])
cols = ['dia', 'codigo', 'punto', 'distancia_lidar_cm', 'suelo_cm', 'altura_cm', 'biomasa_kg_ms_ha', 'ndvi']
AL = pd.concat([s10[cols], m11[cols]], ignore_index=True)
AL.to_csv(os.path.join(OUT, 'tarde11_alturas.csv'), index=False)
print('\nAltura y biomasa (suelo 58,8 cm):')
print(AL.groupby(['dia', 'codigo']).agg(lidar_min=('distancia_lidar_cm', 'min'), lidar_max=('distancia_lidar_cm', 'max'),
                                        altura_min=('altura_cm', 'min'), altura_max=('altura_cm', 'max'),
                                        biomasa_min=('biomasa_kg_ms_ha', 'min'),
                                        biomasa_max=('biomasa_kg_ms_ha', 'max')).round(1).to_string())
