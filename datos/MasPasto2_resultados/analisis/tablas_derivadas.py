"""Recalcula desde los CSV crudos las cifras de las tablas del informe y las guarda en CSV.
Uso: python3 -I tablas_derivadas.py <carpeta_MasPasto2_resultados>
Busca cada crudo por nombre dentro de la carpeta (cualquier subcarpeta)."""
import sys, os, glob, math, numpy as np, pandas as pd
BASE=sys.argv[1]; OUT=os.path.join(BASE,"derivados"); os.makedirs(OUT,exist_ok=True)
IDX={os.path.basename(p):p for p in glob.glob(os.path.join(BASE,"**","*.csv"),recursive=True)}
def L(n): return pd.read_csv(IDX[n if n.endswith(".csv") else n+".csv"])
CH=["f1_405nm","f2_425nm","fz_450nm","f3_475nm","f4_515nm","f5_550nm","fy_555nm","fxl_600nm","f6_640nm","f7_690nm","f8_745nm","nir_855nm"]
cv=lambda v: float(np.std(v,ddof=1)/np.mean(v)*100)
nd=lambda a,b:(a-b)/(a+b)
def s(d,p,c): return d[f"{p}_{c}"]/(d[f"{p}_ganancia_x"]*d[f"{p}_t_int_ms"])
def guarda(df,n): df.to_csv(os.path.join(OUT,n),index=False,encoding="utf-8-sig"); print("->",n)
# 1. Estabilidad 22 oct
d=L("registro_sensorA-B_estabilidad_20261022_162025"); k5=len(d)//5
dr=lambda v:(v.iloc[-k5:].mean()/v.iloc[:k5].mean()-1)*100
guarda(pd.DataFrame([{"canal":c,"CV_A_%":cv(d["n_"+c]),"CV_B_%":cv(d["z_"+c]),"CV_B/A_%":cv(d["z_"+c]/d["n_"+c]),"deriva_A_%":dr(d["n_"+c]),"deriva_B_%":dr(d["z_"+c]),"deriva_B/A_%":dr(d["z_"+c]/d["n_"+c])} for c in CH]).round(3),"lab22_estabilidad.csv")
# 2. Factores de ganancia (ida y vuelta, ref 4x)
rows=[]
for p,sen in (("n","A"),("z","B")):
    d=L("ganancias_sensorA-B_fija_20261022_163012"); d=d[d[p+"_ganancia_x"].notna()].copy()
    for c in CH: d["s_"+c]=s(d,p,c)
    a=d.groupby([p+"_ganancia_x","pasada"])[["s_"+c for c in CH]].mean().groupby(level=0).mean(); a.columns=CH
    F=(a/a.loc[4.0]-1)*100
    for g in F.index: rows.append({"sensor":sen,"ganancia_x":g,**F.loc[g].round(3).to_dict(),"mediana_FY_NIR":round(float(np.median(F.loc[g,CH[6:]])),3),"mediana_F2_NIR":round(float(np.median(F.loc[g,CH[1:]])),3)})
guarda(pd.DataFrame(rows),"lab22_factores_ganancia.csv")
# 3. k con difusor común
pos=[("163938","original"),("170015","intercambiada"),("180021","original"),("190012","intercambiada"),("200011","original")]
R=[]
for t,_ in pos:
    d=L(f"intercomparacion_sensorA-B_difusor_20261022_{t}"); R.append({c:(s(d,"z",c)/s(d,"n",c)).mean() for c in CH})
rows=[]
for c in CH:
    r=[x[c] for x in R]; lo=[math.log(v) for v in r]; mo=np.mean([lo[0],lo[2],lo[4]]); mi=np.mean([lo[1],lo[3]])
    est=[math.sqrt(r[0]*r[1]),math.sqrt(r[2]*r[1]),math.sqrt(r[2]*r[3]),math.sqrt(r[4]*r[3])]
    rows.append({"canal":c,"k_B/A":math.exp((mo+mi)/2),"p_sitio":math.exp((mo-mi)/2),"dispersion_%":np.std(est,ddof=1)/np.mean(est)*100,**{f"r_pos{i+1}":r[i] for i in range(5)}})
guarda(pd.DataFrame(rows).round(4),"lab22_factor_k.csv")
# 4. Transmitancia de la pieza de PTFE
d=L("ptfe_sensorA-B_pieza_ptfe_pieza_20261022_200408"); g=d.groupby(["rep","fase"])[["z_"+c for c in CH]].mean()
T=pd.DataFrame([{c:g.loc[(r,"con"),"z_"+c]/g.loc[(r,"sin"),"z_"+c] for c in CH} for r in sorted(d.rep.unique())])
guarda(pd.DataFrame({"canal":CH,"T_d":T.mean().values,"CV_rep_%":(T.std()/T.mean()*100).values,"cuentas_B_con_PTFE":[d[d.fase=="con"]["z_"+c].mean() for c in CH]}).round(3),"lab22_transmitancia_pieza.csv")
# 5. Validación de campo (26 oct) relativa a la cartulina
def q(d,ok=True):
    if ok: d=d[(d.z_desfase_s.abs()<=0.3)&(~d.n_saturado.astype(bool))&(~d.z_saturado.astype(bool))]
    d=d.dropna(subset=["z_nir_855nm"]); return {c:(s(d,"n",c)/s(d,"z",c)).mean() for c in CH}, len(d)
V={k:f"registro_sensorA-B_validacion_{k}_{t}" for k,t in [("blanco1","20261026_171508"),("blanco2","20261026_172232"),("pasto1","20261026_171303"),("pasto2","20261026_171700"),("ralo","20261026_172041"),("cemento","20261026_171845")]}
Q={k:q(L(v)) for k,v in V.items()}; W={c:math.sqrt(Q["blanco1"][0][c]*Q["blanco2"][0][c]) for c in CH}
rows=[]
for k in ["pasto2","pasto1","ralo","cemento"]:
    r={c:Q[k][0][c]/W[c] for c in CH}; rows.append({"superficie":k,"pares":Q[k][1],**{"rho_"+c:r[c] for c in CH},"NDVI":nd(r["nir_855nm"],r["f6_640nm"]),"NDRE1":nd(r["nir_855nm"],r["f8_745nm"]),"NDRE2":nd(r["f8_745nm"],r["f7_690nm"])})
guarda(pd.DataFrame(rows).round(4),"campo26_validacion.csv")
# 6. E4 en campo
d=L("registro_sensorA-B_operacion_E4_nubes_20261026_173202"); d=d[(d.z_desfase_s.abs()<=0.3)&(~d.n_saturado.astype(bool))&(~d.z_saturado.astype(bool))]
rr={c:(s(d,"n",c)/s(d,"z",c))/W[c] for c in CH}
guarda(pd.DataFrame([{"pares":len(d),"CV_NIR_nadir_%":cv(s(d,"n","nir_855nm")),"CV_NIR_cenit_%":cv(s(d,"z","nir_855nm")),**{f"CV_cociente_{c}_%":cv(s(d,"n",c)/s(d,"z",c)) for c in CH},
  "NDVI_media":nd(rr["nir_855nm"],rr["f6_640nm"]).mean(),"NDVI_CV_%":cv(nd(rr["nir_855nm"],rr["f6_640nm"])),"NDRE2_media":nd(rr["f8_745nm"],rr["f7_690nm"]).mean(),"NDRE2_CV_%":cv(nd(rr["f8_745nm"],rr["f7_690nm"]))}]).round(3),"campo26_E4.csv")
# 7. Barridos de saturación (resúmenes del programa)
rows=[]
for n in ["saturacion_sensorA_operacion_sat_pasto_sol_1545_20261026_155332","saturacion_sensorA_operacion_sat_pasto_1700_20261026_160101","saturacion_sensorA_operacion_sat_pasto_sombra_20261026_155424","saturacion_sensorB_cenit_3mm_zen_nublado_20260415_133507","saturacion_sensorB_cenit_3mm_zen_nublado_20261026_171133"]:
    r=L(n+"_resumen"); r.insert(0,"barrido",n); rows.append(r)
guarda(pd.concat(rows),"campo26_barridos_saturacion.csv")
# 8. PTFE 28-29 oct
def qq(n): d=L(n).dropna(subset=["z_nir_855nm"]); return {c:(d["n_"+c]/d["z_"+c]).mean() for c in CH}
P1={"s15":"registro_sensorA-B_ptfe_lab_solo15x15_20261028_230028","s30":"registro_sensorA-B_ptfe_lab_solo15x30_20260415_133639","n6":"registro_sensorA-B_ptfe_lab_ref_6mm_negro_20260415_133828","b6":"registro_sensorA-B_ptfe_lab_ref_6mm_blanco_20260415_134205","b3":"registro_sensorA-B_ptfe_lab_ref_3mm_blanco_20260415_134504"}
P2={"s15":"registro_sensorA-B_ptfe_lab_solo15x15_20261028_235232","s30":"registro_sensorA-B_ptfe_lab_solo15x30_20261028_235427","n6":"registro_sensorA-B_ptfe_lab_ref_6mm_negro_20261028_235601","b6":"registro_sensorA-B_ptfe_lab_ref_6mm_blanco_20261028_235836","b3":"registro_sensorA-B_ptfe_lab_ref_3mm_blanco_20261029_000000"}
M={k:{c:(qq(P1[k])[c]+qq(P2[k])[c])/2 for c in CH} for k in P1}
comp=[("Fondo blanco frente a negro, 3 mm","b3","s30"),("Fondo blanco frente a negro, 6 mm","b6","n6"),("6 mm frente a 3 mm, fondo negro","n6","s30"),("6 mm frente a 3 mm, fondo blanco","b6","b3"),("15x30 frente a 15x15, 3 mm, fondo negro","s30","s15")]
guarda(pd.DataFrame([{"comparacion":t,**{c:(M[a][c]/M[b][c]-1)*100 for c in CH}} for t,a,b in comp]).round(2),"lab28_ptfe_efectos_pct.csv")
# 9. Llenado
H={15:"registro_sensorA-B_ptfe_lab_ref_6mm_negro_20260415_133828",20:"registro_sensorA-B_ptfe_lab_llenado_20cm_20260415_135752",25:"registro_sensorA-B_ptfe_lab_llenado_25cm_20260415_140110"}
irr=lambda dz: ((35+dz)/math.hypot(35+dz,30)**3)/(35/math.hypot(35,30)**3)
q15=qq(H[15]); rows=[]
for h,n in H.items():
    qh=qq(n); g=irr(h-15); rows.append({"ventana_cm":h,"irradiancia_rel":g,**{"medida_"+c:qh[c]/q15[c] for c in CH},**{"corregida_"+c:qh[c]/q15[c]/g for c in CH}})
guarda(pd.DataFrame(rows).round(4),"lab28_llenado.csv")
# 10. E1 (intento 1)
d=L("registro_sensorA-B_lab_E1_pasto_20261028_010404").dropna(subset=["z_nir_855nm"]); Wb=qq("registro_sensorA-B_lab_E1_blanco1_20261028_010058")
r={c:(d["n_"+c]/d["z_"+c])/Wb[c] for c in CH}
rows=[{"variable":c,"CV_nadir_%":cv(d["n_"+c]),"CV_cenit_%":cv(d["z_"+c]),"CV_cociente_%":cv(d["n_"+c]/d["z_"+c])} for c in CH]
for k,v in {"NDVI":nd(r["nir_855nm"],r["f6_640nm"]),"NDRE1":nd(r["nir_855nm"],r["f8_745nm"]),"NDRE2":nd(r["f8_745nm"],r["f7_690nm"])}.items(): rows.append({"variable":k,"media":v.mean(),"desv":v.std(),"CV_cociente_%":cv(v)})
guarda(pd.DataFrame(rows).round(4),"lab28_E1.csv")
# 11. E4 con lámpara (intento 2)
Wd=L("registro_sensorA-B_lab_E1_blanco2_20260415_135238"); Wq=qq("registro_sensorA-B_lab_E1_blanco2_20260415_135238")
runs=[("12V","registro_sensorA-B_lab_E4_12V_20260415_133653"),("11V","registro_sensorA-B_lab_E4_11V_20260415_134140"),("10V","registro_sensorA-B_lab_E4_10V_20260415_134439"),("9V","registro_sensorA-B_lab_E4_09V_20260415_134747"),("12V_vuelta","registro_sensorA-B_lab_E4_12Vb_20260415_135009")]
rows=[]; z0=None
for lb,n in runs:
    d=L(n); qd=qq(n); g=d.n_ganancia_x.iloc[0]/Wd.n_ganancia_x.iloc[0]
    rc={c:qd[c]/Wq[c] for c in CH}; rn={c:d["n_"+c].mean()/g/Wd["n_"+c].mean() for c in CH}
    z=d.z_nir_855nm.mean(); z0=z0 or z
    rows.append({"voltaje":lb,"luz_cenit_%":z/z0*100,"cenit_NIR/F6":z/d.z_f6_640nm.mean(),"NDVI_nadir":nd(rn["nir_855nm"],rn["f6_640nm"]),"NDVI_corr":nd(rc["nir_855nm"],rc["f6_640nm"]),
      "NDRE2_nadir":nd(rn["f8_745nm"],rn["f7_690nm"]),"NDRE2_corr":nd(rc["f8_745nm"],rc["f7_690nm"]),"NDRE1_nadir":nd(rn["nir_855nm"],rn["f8_745nm"]),"NDRE1_corr":nd(rc["nir_855nm"],rc["f8_745nm"])})
guarda(pd.DataFrame(rows).round(4),"lab28_E4.csv")
