import glob, os, re, sys
import pandas as pd, numpy as np
D = sys.argv[1]
CH = ['f1_405nm','f2_425nm','fz_450nm','f3_475nm','f4_515nm','f5_550nm','fy_555nm','fxl_600nm','f6_640nm','f7_690nm','f8_745nm','nir_855nm']
rows=[]
for f in sorted(glob.glob(f'{D}/registro_sensorA-B_campo_5nov_*.csv'), key=lambda p: re.search(r'_(\d{6})\.csv$',p).group(1) if re.search(r'_(\d{6})\.csv$',p) else 'z'):
    if f.endswith('_resumen.csv'): continue
    m = re.search(r'campo_5nov_(.+)_2026110\d_(\d{6})\.csv', os.path.basename(f))
    et, hh = m.group(1), m.group(2)
    d = pd.read_csv(f)
    n=len(d)
    zok = d['z_nir_855nm'].notna()
    sn = {c: d[f'n_{c}']/(d['n_ganancia_x']*d['n_t_int_ms']) for c in CH}
    sz = {c: d[f'z_{c}']/(d['z_ganancia_x']*d['z_t_int_ms']) for c in CH}
    q = {c: sn[c]/sz[c] for c in ('f6_640nm','f7_690nm','f8_745nm','nir_855nm')}
    ok = zok & ~d['n_saturado'].astype(bool) & ~d['z_saturado'].fillna(False).astype(bool)
    r = dict(hora=hh, etiqueta=et, n=n, n_sin_cenit=int((~zok).sum()),
             sat_n=int(d['n_saturado'].astype(bool).sum()), sat_z=int(d['z_saturado'].fillna(False).astype(bool).sum()),
             g_n='/'.join(str(x) for x in sorted(d['n_ganancia_x'].unique())),
             g_z='/'.join(str(x) for x in sorted(d['z_ganancia_x'].dropna().unique())),
             maxpct_n=round(100*d['n_max_cuentas'].max()/65535,1),
             maxpct_z=round(100*d['z_max_cuentas'].max()/65535,1) if zok.any() else np.nan,
             f6_n=round(d['n_f6_640nm'].mean(),0), nir_n=round(d['n_nir_855nm'].mean(),0),
             f6_z=round(d['z_f6_640nm'].mean(),0), nir_z=round(d['z_nir_855nm'].mean(),0),
             cv_zNIR=round(100*d['z_nir_855nm'].std()/d['z_nir_855nm'].mean(),2),
             cv_nNIR=round(100*d['n_nir_855nm'].std()/d['n_nir_855nm'].mean(),2),
             cv_qNIR=round(100*q['nir_855nm'][ok].std()/q['nir_855nm'][ok].mean(),2),
             cv_qF6=round(100*q['f6_640nm'][ok].std()/q['f6_640nm'][ok].mean(),2),
             desfase_max=round(d['z_desfase_s'].abs().max(),3) if 'z_desfase_s' in d else np.nan,
             T_n=round(d['n_temp_c'].mean(),2),
             ndvi_raw=round(((q['nir_855nm']-q['f6_640nm'])/(q['nir_855nm']+q['f6_640nm']))[ok].mean(),4))
    for c in q: r['q_'+c]=q[c][ok].mean(); r['sq_'+c]=q[c][ok].std()
    r['nok']=int(ok.sum())
    rows.append(r)
T=pd.DataFrame(rows).sort_values('hora')
T.to_csv(sys.argv[2],index=False)
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)
print(T[['hora','etiqueta','n','nok','n_sin_cenit','sat_n','sat_z','g_n','g_z','maxpct_n','maxpct_z','f6_n','nir_n','nir_z','cv_zNIR','cv_qNIR','cv_qF6','desfase_max','T_n','ndvi_raw']].to_string(index=False))
