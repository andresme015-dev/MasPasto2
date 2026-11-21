"""Analisis de las pruebas de laboratorio del 28-29 oct 2026 (PTFE y pasto).
Uso: python3 -I analisis29.py <carpeta_csv>"""
import sys, os, numpy as np, pandas as pd
D = sys.argv[1]
CH = ["f1_405nm","f2_425nm","fz_450nm","f3_475nm","f4_515nm","f5_550nm","fy_555nm","fxl_600nm","f6_640nm","f7_690nm","f8_745nm","nir_855nm"]
B = {"F6":"f6_640nm","F7":"f7_690nm","F8":"f8_745nm","NIR":"nir_855nm","F4":"f4_515nm","F2":"f2_425nm"}
def L(s): return pd.read_csv(os.path.join(D, f"registro_sensorA-B_{s}.csv"))
def basic(p, d, c): return d[f"{p}_{c}"]/(d[f"{p}_ganancia_x"]*d[f"{p}_t_int_ms"])
def q(d):  # cociente nadir/cenit por canal, todas las filas con ambos datos
    d = d.dropna(subset=["z_nir_855nm"]); return pd.DataFrame({c: basic("n",d,c)/basic("z",d,c) for c in CH})
def mean(d, p): d=d.dropna(subset=[f"{p}_nir_855nm"]); return {c: basic(p,d,c).mean() for c in CH}
cv = lambda v: float(np.std(v, ddof=1)/np.mean(v)*100)
nd = lambda a,b: (a-b)/(a+b)
def idx(r): return {"NDVI": nd(r["nir_855nm"],r["f6_640nm"]), "NDRE1": nd(r["nir_855nm"],r["f8_745nm"]), "NDRE2": nd(r["f8_745nm"],r["f7_690nm"])}

print("="*20, "1. PTFE: intento 1 vs intento 2 (cuentas crudas nadir, G=128)")
P1 = {"solo15x15":"ptfe_lab_solo15x15_20261028_230028","solo15x30":"ptfe_lab_solo15x30_20260415_133639","ref_6mm_negro":"ptfe_lab_ref_6mm_negro_20260415_133828",
      "ref_6mm_blanco":"ptfe_lab_ref_6mm_blanco_20260415_134205","ref_3mm_blanco":"ptfe_lab_ref_3mm_blanco_20260415_134504","solo15x30_b":"ptfe_lab_solo15x30_b_20260415_134743"}
P2 = {"solo15x15":"ptfe_lab_solo15x15_20261028_235232","solo15x30":"ptfe_lab_solo15x30_20261028_235427","ref_6mm_negro":"ptfe_lab_ref_6mm_negro_20261028_235601",
      "ref_6mm_blanco":"ptfe_lab_ref_6mm_blanco_20261028_235836","ref_3mm_blanco":"ptfe_lab_ref_3mm_blanco_20261029_000000","solo15x30_b":"ptfe_lab_solo15x30_b_20261029_000141"}
rows=[]
for k in P1:
    a, b = L(P1[k]), L(P2[k]); qa, qb = q(a).mean(), q(b).mean()
    rows.append([k, a.n_nir_855nm.mean(), b.n_nir_855nm.mean(), (b.n_nir_855nm.mean()/a.n_nir_855nm.mean()-1)*100,
                 a.n_f6_640nm.mean(), b.n_f6_640nm.mean(), (qb["nir_855nm"]/qa["nir_855nm"]-1)*100, (qb["f6_640nm"]/qa["f6_640nm"]-1)*100,
                 a.n_nir_855nm.mean()/a.n_f6_640nm.mean(), b.n_nir_855nm.mean()/b.n_f6_640nm.mean(), a.z_nir_855nm.mean(), b.z_nir_855nm.mean()])
print(pd.DataFrame(rows, columns=["config","NIR_i1","NIR_i2","dNIR%","F6_i1","F6_i2","dq_NIR%","dq_F6%","NIR/F6_i1","NIR/F6_i2","zNIR_i1","zNIR_i2"]).round(2).to_string(index=False))
x = L("ptfe_lab_ref_6mm_blanco_20260415_134042"); print("descartada ref_6mm_blanco_134042: VIS saturado en", int(x.n_vis_saturado.sum()), "de", len(x), "| NIR", round(x.n_nir_855nm.mean()), "F6", round(x.n_f6_640nm.mean()), "max %", round(x.n_max_cuentas.max()/655.35,1))
y = L("ptfe_lab_ref_6mm_blanco_20260415_134317"); print("repeticion 134317 vs 134205 NIR", round((y.n_nir_855nm.mean()/L(P1['ref_6mm_blanco']).n_nir_855nm.mean()-1)*100,2),"%")
# efectos (promedio de los dos intentos, sobre el cociente q)
def qq(k): return np.mean([q(L(P1[k])).mean()[["f2_425nm","f4_515nm","f6_640nm","f7_690nm","f8_745nm","nir_855nm"]] , q(L(P2[k])).mean()[["f2_425nm","f4_515nm","f6_640nm","f7_690nm","f8_745nm","nir_855nm"]]],axis=0)
lab=["F2 425","F4 515","F6 640","F7 690","F8 745","NIR 855"]
E = pd.DataFrame({"llenado 15x30/15x15": qq("solo15x30")/qq("solo15x15"), "6mm/3mm sobre negro": qq("ref_6mm_negro")/qq("solo15x30"),
                  "6mm blanco/negro": qq("ref_6mm_blanco")/qq("ref_6mm_negro"), "3mm blanco/negro": qq("ref_3mm_blanco")/qq("solo15x30"),
                  "6mm/3mm sobre blanco": qq("ref_6mm_blanco")/qq("ref_3mm_blanco")}, index=lab)
print(((E-1)*100).round(1).to_string())

print("="*20, "2. Llenado (intento 1, láminas apiladas sobre negro)")
H = {15:"ptfe_lab_ref_6mm_negro_20260415_133828", 20:"ptfe_lab_llenado_20cm_20260415_135752", 25:"ptfe_lab_llenado_25cm_20260415_140110"}
q15 = q(L(H[15])).mean()
for h,s in H.items():
    d=L(H[h]); qh=q(d).mean()
    print(h,"cm:", " ".join(f"{n} {(qh[c]/q15[c]-1)*100:+.1f}%" for n,c in [("F2","f2_425nm"),("F4","f4_515nm"),("F6","f6_640nm"),("F7","f7_690nm"),("F8","f8_745nm"),("NIR","nir_855nm")]),
          "| NIR/F6 %.2f"%(d.n_nir_855nm.mean()/d.n_f6_640nm.mean()), "| cenit NIR %.0f"%d.z_nir_855nm.mean())

print("="*20, "3. Pasto")
G = {"i1": dict(blanco1="lab_E1_blanco1_20261028_010058", pasto="lab_E1_pasto_20261028_010404",
                E4=[("12V","lab_E4_12V_20261028_010623"),("11V*","lab_E4_11V_20261028_010934"),("11V","lab_E4_11V_20260415_133412"),
                    ("10V mov","lab_E4_10V_20260415_134842"),("9V mov","lab_E4_09V_20260415_135059"),("12Vb mov","lab_E4_12Vb_20260415_135308")],
                blanco2="lab_E1_blanco1_20261028_020230"),
     "i2": dict(blanco1="lab_E1_blanco1_20261028_020230", pasto="lab_E1_pasto_20260415_133410",
                E4=[("12V","lab_E4_12V_20260415_133653"),("11V a","lab_E4_11V_20260415_133935"),("11V b","lab_E4_11V_20260415_134004"),("11V c","lab_E4_11V_20260415_134140"),
                    ("10V a","lab_E4_10V_20260415_134342"),("10V b","lab_E4_10V_20260415_134439"),("9V","lab_E4_09V_20260415_134747"),("12Vb","lab_E4_12Vb_20260415_135009")],
                blanco2="lab_E1_blanco2_20260415_135238")}
for g in ("i1","i2"):
    print("-"*10, g)
    W1, W2 = q(L(G[g]["blanco1"])).mean(), q(L(G[g]["blanco2"])).mean()
    print("blanco2/blanco1 cociente:", " ".join(f"{n} {(W2[c]/W1[c]-1)*100:+.1f}%" for n,c in [("F2","f2_425nm"),("F6","f6_640nm"),("F7","f7_690nm"),("F8","f8_745nm"),("NIR","nir_855nm")]))
    for wn,W in (("blanco1",W1),("blanco2",W2)):
        dp = L(G[g]["pasto"]); Q = q(dp)
        R = Q.div(W); I = {k: v for k,v in idx(R).items()}
        print(f"E1 ({len(Q)} lecturas) ref {wn}: " + " ".join(f"{k} {v.mean():.3f} (CV {cv(v):.2f}%, sd {v.std():.4f})" for k,v in I.items()))
    dp = L(G[g]["pasto"]); Q=q(dp)
    print("   CV crudo nadir:", " ".join(f"{n} {cv(dp['n_'+c]):.2f}%" for n,c in [("F6","f6_640nm"),("F7","f7_690nm"),("F8","f8_745nm"),("NIR","nir_855nm")]),
          "| CV cenit:", " ".join(f"{n} {cv(dp['z_'+c].dropna()):.2f}%" for n,c in [("F6","f6_640nm"),("NIR","nir_855nm")]),
          "| CV cociente:", " ".join(f"{n} {cv(Q[c]):.2f}%" for n,c in [("F6","f6_640nm"),("F7","f7_690nm"),("F8","f8_745nm"),("NIR","nir_855nm")]))
    t=(dp.n_t-dp.n_t.iloc[0]); sl=np.polyfit(t,dp.n_nir_855nm,1)[0]*60/dp.n_nir_855nm.mean()*100; slz=np.polyfit(t[dp.z_nir_855nm.notna()],dp.z_nir_855nm.dropna(),1)[0]*60/dp.z_nir_855nm.mean()*100
    print(f"   deriva NIR nadir {sl:+.2f} %/min, cenit {slz:+.2f} %/min, duracion {t.iloc[-1]:.0f} s")
    # E4
    ref = q(L(G[g]["E4"][0][1])).mean(); r12 = mean(L(G[g]["E4"][0][1]),"z")
    out=[]
    for lab_,s in G[g]["E4"]:
        d=L(s); Q=q(d); m=Q.mean(); zz=mean(d,"z"); nn=mean(d,"n")
        Rw = m.div(W2 if g=="i2" else W1); I=idx(Rw)
        out.append([lab_, len(Q), zz["nir_855nm"]/r12["nir_855nm"]*100, zz["f6_640nm"]/r12["f6_640nm"]*100, nn["nir_855nm"]/mean(L(G[g]["E4"][0][1]),"n")["nir_855nm"]*100,
                    (m["f6_640nm"]/ref["f6_640nm"]-1)*100,(m["f7_690nm"]/ref["f7_690nm"]-1)*100,(m["f8_745nm"]/ref["f8_745nm"]-1)*100,(m["nir_855nm"]/ref["nir_855nm"]-1)*100,
                    I["NDVI"], I["NDRE1"], I["NDRE2"], zz["nir_855nm"]/zz["f6_640nm"]])
    print(pd.DataFrame(out, columns=["E4","n","cenitNIR%","cenitF6%","nadirNIR%","dqF6%","dqF7%","dqF8%","dqNIR%","NDVI","NDRE1","NDRE2","cenit NIR/F6"]).round(3).to_string(index=False))
# solo nadir (cenit caido)
d=pd.read_csv(os.path.join(D,"registro_sensorA_lab_E4_10V_20260415_133653.csv")); print("solo nadir E4_10V_133653:", len(d), "filas, NIR", round(d.n_nir_855nm.mean()), "F6", round(d.n_f6_640nm.mean()))
