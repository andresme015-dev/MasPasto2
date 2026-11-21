"""Figura de factores de ganancia (informe v6). Lee derivados/casa6_factores_ganancia.csv y lab22."""
import os, pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.makedirs(f"{B}/salidas/figuras_avance",exist_ok=True)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.alpha":0.25})
R=pd.read_csv(f"{B}/derivados/casa6_factores_ganancia.csv")
O=pd.read_csv(f"{B}/derivados/lab22_factores_ganancia.csv",encoding="utf-8-sig")
cols={"f6_640nm":("F6 (640 nm)","#C0622B","o"),"f7_690nm":("F7 (690 nm)","#8a5aa8","s"),"f8_745nm":("F8 (745 nm)","#2A8A57","^"),"nir_855nm":("NIR (855 nm)","#3F6FB5","D")}
fig,axs=plt.subplots(1,2,figsize=(7.4,3.2),sharey=True)
for ax,sen,tit in zip(axs,("A","B"),("(a) Sensor A (nadir)","(b) Sensor B (cenit)")):
    r=R[R.sensor==sen].sort_values("ganancia_x"); o=O[(O.sensor==sen)&(O.ganancia_x>=1)].sort_values("ganancia_x")
    ax.axhline(0,color="#888",lw=0.8)
    for c,(lab,col,m) in cols.items():
        ax.plot(np.log2(r.ganancia_x),r[c],"-",marker=m,color=col,ms=4,lw=1.3,label=lab)
        ax.plot(np.log2(o.ganancia_x),o[c],ls="none",marker=m,mfc="none",mec=col,ms=8,mew=1)
    ax.set_xticks(range(0,9)); ax.set_xticklabels([f"{2**i:g}" for i in range(0,9)])
    ax.set_xlabel("Ganancia nominal (×)"); ax.set_title(tit,fontsize=9,loc="left")
axs[0].set_ylabel("Ganancia real / nominal − 1 (%)\n(referida a 4×)")
axs[0].legend(fontsize=7,frameon=False,loc="lower left")
axs[1].text(0.2,1.6,"Círculos vacíos: 22 de octubre",fontsize=7,color="#555")
axs[0].set_ylim(-4.5,2.2)
fig.tight_layout(); fig.savefig(f"{B}/salidas/figuras_avance/casa6_ganancias.pdf"); print("ok")
