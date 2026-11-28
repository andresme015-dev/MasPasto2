"""Nota: las etiquetas 3mm/6mm de los nombres de archivo son de la adquisición; las láminas son de 2 mm (una o dos apiladas).
Figuras y cifras de las pruebas de laboratorio del 28-29 oct 2026 (informe v3).
Lee 2026-10-28_lab_PTFE_E1_E4/crudos y escribe en salidas/figuras_avance."""
import os, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # carpeta MasPasto2_resultados
D=os.path.join(BASE,"2026-10-28_lab_PTFE_E1_E4","crudos"); F=os.path.join(BASE,"salidas","figuras_avance"); os.makedirs(F,exist_ok=True)
plt.rcParams.update({"text.hinting": "no_hinting", "font.family":"DejaVu Sans","font.size":9,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.alpha":0.25})
AZ, NA, VE = "#3F6FB5", "#C0622B", "#2A8A57"
L=lambda s: pd.read_csv(os.path.join(D,f"registro_sensorA-B_{s}.csv"))
nd=lambda a,b:(a-b)/(a+b)
BANDS=[("F2","f2_425nm",425),("F4","f4_515nm",515),("F6","f6_640nm",640),("F7","f7_690nm",690),("F8","f8_745nm",745),("NIR","nir_855nm",855)]
def q(d): d=d.dropna(subset=["z_nir_855nm"]); return {c:(d[f"n_{c}"]/d[f"z_{c}"]).mean() for _,c,_ in BANDS}
P1={"s15":"ptfe_lab_solo15x15_20261028_230028","s30":"ptfe_lab_solo15x30_20260415_133639","n6":"ptfe_lab_ref_6mm_negro_20260415_133828","b6":"ptfe_lab_ref_6mm_blanco_20260415_134205","b3":"ptfe_lab_ref_3mm_blanco_20260415_134504"}
P2={"s15":"ptfe_lab_solo15x15_20261028_235232","s30":"ptfe_lab_solo15x30_20261028_235427","n6":"ptfe_lab_ref_6mm_negro_20261028_235601","b6":"ptfe_lab_ref_6mm_blanco_20261028_235836","b3":"ptfe_lab_ref_3mm_blanco_20261029_000000"}
Q={k:{c:(q(L(P1[k]))[c]+q(L(P2[k]))[c])/2 for _,c,_ in BANDS} for k in P1}
eff=lambda a,b:[(Q[a][c]/Q[b][c]-1)*100 for _,c,_ in BANDS]
E={"fondo3":eff("b3","s30"),"fondo6":eff("b6","n6"),"grosor":eff("n6","s30"),"tam":eff("s30","s15")}
print("== Efectos PTFE (%)"); [print(k,[round(v,1) for v in E[k]]) for k in E]
wl=[w for *_,w in BANDS]; lab=[n for n,*_ in BANDS]
fig,(a,b)=plt.subplots(1,2,figsize=(7.2,3.0),sharey=True)
a.plot(wl,E["fondo3"],"-o",color=NA,lw=2,ms=5,label="Una lámina de 2 mm"); a.plot(wl,E["fondo6"],"-s",color=AZ,lw=2,ms=5,label="Dos láminas apiladas (4 mm)")
a.set_title("(a) Fondo blanco frente a negro",fontsize=9,loc="left"); a.legend(fontsize=7.5,frameon=False,loc="upper left")
b.plot(wl,E["grosor"],"-s",color=AZ,lw=2,ms=5,label="4 mm frente a 2 mm (fondo negro)"); b.plot(wl,E["tam"],"-o",color=NA,lw=2,ms=5,label="15×30 frente a 15×15 (2 mm, fondo negro)")
b.set_title("(b) Grosor y tamaño",fontsize=9,loc="left"); b.legend(fontsize=7.5,frameon=False,loc="upper left")
for ax in (a,b): ax.set_xticks(wl); ax.set_xticklabels([f"{n}\n{w}" for n,w in zip(lab,wl)],fontsize=7.5); ax.set_xlabel("Canal y pico (nm)"); ax.set_ylim(0,50)
a.set_ylabel("Cambio de la lectura (%)")
fig.tight_layout(); fig.savefig(f"{F}/lab29_ptfe.pdf"); plt.close(fig)

# --- Llenado, con corrección por la irradiancia de la lámina al bajarla
H={15:"ptfe_lab_ref_6mm_negro_20260415_133828",20:"ptfe_lab_llenado_20cm_20260415_135752",25:"ptfe_lab_llenado_25cm_20260415_140110"}
v0,h0=35.0,30.0   # lámpara: 35 cm sobre la lámina y 30 cm en horizontal (montaje a 15 cm)
irr=lambda dz: ((v0+dz)/np.hypot(v0+dz,h0)**3)/(v0/np.hypot(v0,h0)**3)
q15=q(L(H[15])); print("== Llenado")
for h,s in H.items():
    qh=q(L(H[h])); g=irr(h-15)
    print(h,"irr %.3f"%g," medido:",[round(qh[c]/q15[c],3) for _,c,_ in BANDS]," corregido:",[round(qh[c]/q15[c]/g,3) for _,c,_ in BANDS])
def frac(h,a,b,th,n=601):
    x=np.linspace(-a,a,n); y=np.linspace(-b,b,n); X,Y=np.meshgrid(x,y); r2=X**2+Y**2+h**2; c=h/np.sqrt(r2); w=c*c/r2; w[np.arccos(c)>th]=0; return w.sum()*(x[1]-x[0])*(y[1]-y[0])
for t in (30,35,40,45):
    th=np.radians(t); st=lambda h: frac(h,7.5,15,th)+0.149*frac(h,7.5,7.5,th)
    print("modelo %d°: 15x30/15x15 %.3f  20/15 %.3f  25/15 %.3f  radio a 15 cm %.1f cm"%(t,frac(15,7.5,15,th)/frac(15,7.5,7.5,th),st(20)/st(15),st(25)/st(15),15*np.tan(th)))

# --- E4 (intento 2)
W=L("lab_E1_blanco2_20260415_135238")
runs=[("12 V","lab_E4_12V_20260415_133653"),("11 V","lab_E4_11V_20260415_134140"),("10 V","lab_E4_10V_20260415_134439"),("9 V","lab_E4_09V_20260415_134747"),("12 V\n(vuelta)","lab_E4_12Vb_20260415_135009")]
qW=q(W); R=[]
for lb,s in runs:
    d=L(s); qd=q(d); g=d.n_ganancia_x.iloc[0]/W.n_ganancia_x.iloc[0]
    rc={c:qd[c]/qW[c] for _,c,_ in BANDS}; rn={c:d[f"n_{c}"].mean()/g/W[f"n_{c}"].mean() for _,c,_ in BANDS}
    R.append(dict(lb=lb,luz=d.z_nir_855nm.mean(),col=d.z_nir_855nm.mean()/d.z_f6_640nm.mean(),
      ndvi_c=nd(rc["nir_855nm"],rc["f6_640nm"]),ndvi_n=nd(rn["nir_855nm"],rn["f6_640nm"]),
      ndre2_c=nd(rc["f8_745nm"],rc["f7_690nm"]),ndre2_n=nd(rn["f8_745nm"],rn["f7_690nm"]),
      ndre1_c=nd(rc["nir_855nm"],rc["f8_745nm"]),ndre1_n=nd(rn["nir_855nm"],rn["f8_745nm"])))
R=pd.DataFrame(R); R["luz"]=R.luz/R.luz.iloc[0]*100; print("== E4"); print(R.round(3).to_string(index=False))
fig,axs=plt.subplots(1,3,figsize=(7.4,2.9)); x=np.arange(len(R))
for ax,(k,t) in zip(axs,[("ndvi","NDVI"),("ndre2","NDRE$_2$ (745/690)"),("ndre1","NDRE$_1$ (855/745)")]):
    ax.plot(x,R[k+"_n"],"-o",color=NA,lw=2,ms=5,label="Solo nadir"); ax.plot(x,R[k+"_c"],"-s",color=AZ,lw=2,ms=5,label="Corregido con el cenit")
    ax.set_xticks(x); ax.set_xticklabels([f"{a}\n{l:.0f} %" for a,l in zip(["12 V","11 V","10 V","9 V","12 V"],R.luz)],fontsize=7); ax.set_title(t,fontsize=9,loc="left")
    lo=min(R[k+"_n"].min(),R[k+"_c"].min())-0.005; ax.set_ylim(lo,lo+0.07)
axs[0].legend(fontsize=7,frameon=False,loc="upper left"); axs[0].set_ylabel("Índice relativo al blanco")
axs[1].set_xlabel("Voltaje de la lámpara y luz en el cenit")
fig.tight_layout(); fig.savefig(f"{F}/lab29_E4.pdf"); plt.close(fig)

# --- E1 (intento 1)
dp=L("lab_E1_pasto_20261028_010404"); W1=q(L("lab_E1_blanco1_20261028_010058"))
dd=dp.dropna(subset=["z_nir_855nm"]); rc={c:(dd[f"n_{c}"]/dd[f"z_{c}"])/W1[c] for _,c,_ in BANDS}
cv=lambda v: float(np.std(v,ddof=1)/np.mean(v)*100)
print("== E1 n=%d"%len(dd))
for n,c,_ in BANDS: print(n,"CV nadir %.2f  cenit %.2f  cociente %.2f"%(cv(dd['n_'+c]),cv(dd['z_'+c]),cv(dd['n_'+c]/dd['z_'+c])))
for k,v in {"NDVI":nd(rc["nir_855nm"],rc["f6_640nm"]),"NDRE1":nd(rc["nir_855nm"],rc["f8_745nm"]),"NDRE2":nd(rc["f8_745nm"],rc["f7_690nm"])}.items():
    print(k,"media %.3f sd %.4f CV %.2f min %.3f max %.3f"%(v.mean(),v.std(),cv(v),v.min(),v.max()))
