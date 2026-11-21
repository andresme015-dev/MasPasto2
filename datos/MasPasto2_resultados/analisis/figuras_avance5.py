"""Figuras del campo del 5 nov 2026 (informe v5). Lee 2026-11-05_campo_sol_nube y derivados; escribe en salidas/figuras_avance."""
import os, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from PIL import Image
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D=f"{B}/2026-11-05_campo_sol_nube"; F=f"{B}/salidas/figuras_avance"; os.makedirs(F,exist_ok=True)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.alpha":0.25})
AZ, NA, VE, GR = "#3F6FB5", "#C0622B", "#2A8A57", "#888888"
# --- fotos
def collage(files, out, h=900):
    ims=[Image.open(f).convert("RGB") for f in files]
    ims=[im.resize((int(im.width*h/im.height),h)) for im in ims]
    W=sum(i.width for i in ims)+12*(len(ims)-1); S=Image.new("RGB",(W,h),"white"); x=0
    for im in ims: S.paste(im,(x,0)); x+=im.width+12
    S.save(out,quality=88)
collage([f"{D}/fotos/montaje_1.jpeg",f"{D}/fotos/montaje_2.jpeg",f"{D}/fotos/montaje_4.jpeg"],f"{F}/campo5_montaje.jpg")
collage([f"{D}/fotos/superficie_{i}.jpeg" for i in (1,2,3,4)],f"{F}/campo5_superficies.jpg",h=700)
# --- datos
P=pd.read_csv(f"{B}/derivados/campo_5nov_revision_por_archivo.csv",dtype={"hora":str})
R=pd.read_csv(f"{B}/derivados/campo_5nov_indices_por_bloque.csv")
orden=[f"s{i}" for i in range(1,6)]+[f"n{i}" for i in range(1,11)]
et=[f"S{i}" for i in range(1,6)]+[f"N{i}" for i in range(1,11)]
ad=[];fi=[]
for b in orden:
    if b.startswith("s"):
        ad.append(R[(R.bloque==b)&(R.modo=="adaptativa, W nube1")].NDVI.iloc[0]); fi.append(R[(R.bloque==b)&(R.modo=="fija, Wf nube1")].NDVI.iloc[0])
    else:
        ad.append(R[(R.bloque==b)&(R.modo=="adaptativa")].NDVI.iloc[0]); fi.append(R[(R.bloque==b)&(R.modo=="fija 0,5x")].NDVI.iloc[0])
fig,axs=plt.subplots(2,2,figsize=(7.4,5.6)); a,b,c,d=axs.ravel()
x=np.arange(len(orden))
for lo,hi,col,t in [(-0.5,4.5,"#F6E7B8","Sol"),(4.5,5.5,"#E6E6E6","Mixto"),(5.5,10.5,"#DCE6F2","Sombrilla"),(10.5,11.5,"#E6E6E6","Mixto"),(11.5,14.5,"#D4E8DA","Nublado")]:
    a.axvspan(lo,hi,color=col,lw=0)
    a.text((lo+hi)/2,0.762,t,ha="center",fontsize=6.5)
a.plot(x,ad,"-o",color=AZ,ms=4,lw=1.5,label="Adaptativa"); a.plot(x,fi,"--s",color=NA,ms=4,lw=1.2,label="Fija 0,5×")
a.set_xticks(x); a.set_xticklabels(et,fontsize=6.5); a.set_ylim(0.70,0.77); a.set_ylabel("NDVI relativo al blanco")
a.set_title("(a) NDVI del mismo punto por bloque",fontsize=9,loc="left"); a.legend(fontsize=7,frameon=False,loc="lower left")
# (b) CV cenit vs CV cociente
Q=P[P.condicion.isin(["sol","mixto","sombrilla","sombrilla, mixto","nublado natural"])&(P.nok>=5)]
for cond,col,m in [("sol","#D9A400","o"),("nublado natural",VE,"s"),("mixto",GR,"^"),("sombrilla",NA,"D"),("sombrilla, mixto",NA,"D")]:
    s=Q[Q.condicion==cond]; b.scatter(s.cv_zNIR,s.cv_qNIR,s=18,color=col,marker=m,label=cond.capitalize() if cond!="sombrilla, mixto" else None,alpha=.85)
lim=[0.1,40]; b.plot(lim,lim,color=GR,lw=0.8,ls=":"); b.text(9,13,"sin corrección",fontsize=6.5,color=GR,rotation=40)
b.set_xscale("log"); b.set_yscale("log"); b.set_xlim(lim); b.set_ylim(lim)
b.set_xlabel("CV del NIR en el cenit (%)"); b.set_ylabel("CV del cociente NIR (%)")
b.set_title("(b) Variación de la luz y del cociente por corrida",fontsize=9,loc="left"); b.legend(fontsize=6.5,frameon=False,loc="upper left")
# (c) G_nube_3 lectura a lectura
for f,lab,col in [("registro_sensorA-B_campo_5nov_G_nube_2_20261105_090852.csv","Nube 2",NA),("registro_sensorA-B_campo_5nov_G_nube_3_20261105_091336.csv","Nube 3",AZ)]:
    t=pd.read_csv(f"{D}/crudos/{f}"); qn=t.n_nir_855nm/t.z_nir_855nm; qr=t.n_f6_640nm/t.z_f6_640nm
    qq=(t.n_nir_855nm/t.n_ganancia_x)/(t.z_nir_855nm/t.z_ganancia_x); nd=(qn-qr)/(qn+qr)
    c.plot(qq,nd,"-o",color=col,ms=4,lw=1,label=lab); c.annotate("1.ª",(qq.iloc[0],nd.iloc[0]),fontsize=6.5,xytext=(3,3),textcoords="offset points")
c.set_xlabel("Cociente nadir/cenit del NIR (normalizado)"); c.set_ylabel("NDVI sin blanco")
c.set_title("(c) Sombrilla: lectura a lectura",fontsize=9,loc="left"); c.legend(fontsize=7,frameon=False,loc="upper right")
# (d) cociente del blanco en el tiempo
Wd=P[P.etiqueta_real.str.match(r"Wf?_")&(P.nok>=5)].copy()
qmap=pd.read_csv(f"{B}/derivados/campo_5nov_cocientes_por_archivo.csv",dtype={"hora":str}).set_index("hora")
Wd["q"]=[qmap.loc[h,"q_nir_855nm"] for h in Wd.hora]; Wd["r"]=[qmap.loc[h,"q_nir_855nm"]/qmap.loc[h,"q_f6_640nm"] for h in Wd.hora]
tt=[int(h[:2])*60+int(h[2:4])+int(h[4:])/60 for h in Wd.hora]
colc={"mixto":GR,"sombrilla":NA,"sombrilla, mixto":NA,"nublado natural":VE}
d.scatter(tt,Wd.q,c=[colc[k] for k in Wd.condicion],s=22,marker="o")
d2=d.twinx(); d2.plot(tt,Wd.r,"x",color="k",ms=4); d2.set_ylim(0.9,1.2); d2.set_ylabel("NIR/F6 del cociente del blanco",fontsize=8); d2.grid(False)
d.set_xticks([510,540,570,600]); d.set_xticklabels(["8:30","9:00","9:30","10:00"]); d.set_ylim(0,2.5)
d.set_ylabel("Cociente nadir/cenit del NIR"); d.set_xlabel("Hora")
d.set_title("(d) Blanco a 10 cm: nivel (●) y forma (×)",fontsize=9,loc="left")
fig.tight_layout(); fig.savefig(f"{F}/campo5_resultados.pdf"); plt.close(fig)
print("ok")
