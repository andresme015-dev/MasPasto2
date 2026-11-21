"""Factores de ganancia del 6 nov. Uso: python3 -I casa6_factores_ganancia.py <carpeta de la sesión 2026-11-06>/crudos <salida.csv>
Lee oscuridad_A.json y oscuridad_B.json de esa carpeta y los factores de octubre de derivados/lab22_factores_ganancia.csv."""
import sys, json, glob, os, re
import pandas as pd, numpy as np
D=sys.argv[1]; OUT=sys.argv[2]
CH=['f1_405nm','f2_425nm','fz_450nm','f3_475nm','f4_515nm','f5_550nm','fy_555nm','fxl_600nm','f6_640nm','f7_690nm','f8_745nm','nir_855nm']
C11=CH[1:]
osc={'A':{int(k):v for k,v in json.load(open(f'{D}/oscuridad_A.json')).items()},
     'B':{int(k):v for k,v in json.load(open(f'{D}/oscuridad_B.json')).items()}}
def idx(g): return int(round(np.log2(g)+1))
def analiza(f):
    d=pd.read_csv(f); p='n_' if 'n_f6_640nm' in d else 'z_'
    sen='A' if p=='n_' else 'B'
    d=d[d.fase=='luz']
    rows=[];
    gs=sorted(d[p+'ganancia_x'].unique())
    blk={}
    for g in gs:
        for pas in ('ida','vuelta'):
            b=d[(d[p+'ganancia_x']==g)&(d.pasada==pas)]
            o=osc[sen].get(idx(g),{c:0 for c in CH})
            s={c:((b[p+c]-o[c])/(g*b[p+'t_int_ms'])) for c in CH}
            blk[(g,pas)]=dict(n=len(b),sat=int(b[p+'saturado'].astype(bool).sum()),vis=int(b[p+'vis_saturado'].astype(bool).sum()),
                              maxpct=100*b[p+'max_cuentas'].mean()/65535,
                              mean={c:s[c].mean() for c in CH},cv={c:100*s[c].std()/s[c].mean() if s[c].mean() else np.nan for c in CH},
                              cnt={c:b[p+c].mean() for c in CH})
    prom={g:{c:(blk[(g,'ida')]['mean'][c]+blk[(g,'vuelta')]['mean'][c])/2 for c in CH} for g in gs}
    der={c:100*(blk[(gs[-1],'vuelta')]['mean'][c]/blk[(gs[-1],'ida')]['mean'][c]-1) for c in CH}
    return sen,gs,blk,prom,der
res={}
for f in sorted(glob.glob(f'{D}/ganancias_sensor*_2026110[6]_*.csv')):
    if f.endswith(('_resumen.csv','_pasos.csv')): continue
    tag=re.search(r'(nadir|cenit)_(T\d)_(\d{8}_\d{6})',f).group(0)
    res[tag]=analiza(f)
# reporte por corrida
lines=[]
for tag,(sen,gs,blk,prom,der) in res.items():
    ref=gs[1] if len(gs)>1 else gs[0]
    lines.append(f"\n== {tag} (sensor {sen}) ganancias {gs}")
    for g in gs:
        bi,bv=blk[(g,'ida')],blk[(g,'vuelta')]
        rel=[100*(prom[g][c]/prom[gs[0]][c]-1) for c in C11]
        lines.append(f"  {g:5g}x n={bi['n']}+{bv['n']} sat={bi['sat']+bv['sat']} vis={bi['vis']+bv['vis']} max%={bi['maxpct']:.1f}/{bv['maxpct']:.1f} "
                     f"cnt NIR={bi['cnt']['nir_855nm']:.0f} F6={bi['cnt']['f6_640nm']:.0f}  CVmed={np.nanmedian([bi['cv'][c] for c in C11]):.3f}%")
    lines.append(f"  deriva vuelta/ida a {gs[-1]}x: mediana {np.median([der[c] for c in C11]):+.3f}%  NIR {der['nir_855nm']:+.3f}%  F6 {der['f6_640nm']:+.3f}%")
    for a,b in zip(gs,gs[1:]):
        st=[100*(prom[b][c]/prom[a][c]-1) for c in C11]
        lines.append(f"  paso {a:g}->{b:g}x: mediana {np.median(st):+.2f}%  NIR {100*(prom[b]['nir_855nm']/prom[a]['nir_855nm']-1):+.2f}  F6 {100*(prom[b]['f6_640nm']/prom[a]['f6_640nm']-1):+.2f}  F7 {100*(prom[b]['f7_690nm']/prom[a]['f7_690nm']-1):+.2f}  F8 {100*(prom[b]['f8_745nm']/prom[a]['f8_745nm']-1):+.2f}")
print("\n".join(lines))
# encadenado: factor F(g) = s_g / s_4 (verdadero/nominal) por canal
oct=pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','derivados','lab22_factores_ganancia.csv'),encoding='utf-8-sig')
def chain(tramos, ancla):
    """tramos: lista de prom dicts en orden; ancla: dict g->{c:F} conocido (log). devuelve dict g->{c:F}"""
    F={g:dict(v) for g,v in ancla.items()}
    for prom in tramos:
        gs=sorted(prom); comun=[g for g in gs if g in F]
        for c in CH:
            k=np.exp(np.mean([np.log(F[g][c]/prom[g][c]) for g in comun]))
            for g in gs:
                val=prom[g][c]*k
                if g in F and g not in ancla: F[g][c]=np.sqrt(F[g][c]*val)  # promedio geom. en solapes
                elif g not in F: F[g]={**F.get(g,{}),c:val} if g in F else {c:val} if False else F.setdefault(g,{}) or F[g]
                if g not in ancla: F[g][c]=F[g].get(c,val) if False else (np.sqrt(F[g][c]*val) if c in F[g] and F[g][c]!=val else val)
    return F
def chain2(tramos, ancla):
    F={g:dict(v) for g,v in ancla.items()}; resid=[]
    for prom in tramos:
        gs=sorted(prom); comun=[g for g in gs if g in F]
        k={c:np.exp(np.mean([np.log(F[g][c]/prom[g][c]) for g in comun])) for c in CH}
        for g in comun:
            resid.append((g,{c:100*(prom[g][c]*k[c]/F[g][c]-1) for c in CH}))
        for g in gs:
            if g not in F: F[g]={c:prom[g][c]*k[c] for c in CH}
    return F,resid
# nadir: T1 tiene 4x -> ancla F(4)=1
T={t.split('_')[0]+'_'+t.split('_')[1]:res[t][3] for t in res}
def last(prefix): 
    ks=sorted(t for t in res if t.startswith(prefix)); return res[ks[-1]][3], ks[-1]
pT1,_=last('nadir_T1'); pT2,_=last('nadir_T2'); pT3,_=last('nadir_T3')
anc={4.0:{c:1.0 for c in CH}}
# normalizar T1 a 4x
FA,rA=chain2([pT1,pT2,pT3],{4.0:{c:pT1[4.0][c] for c in CH}})
FA={g:{c:FA[g][c]/pT1[4.0][c] for c in CH} for g in FA}
# cenit: ancla octubre 4x=1, 8x=oct
o=oct[oct.sensor=='B'].set_index('ganancia_x')
ancB={g:{c:1+o.loc[g,c]/100 for c in CH} for g in (1.0,2.0,4.0,8.0)}
cT2,k2=last('cenit_T2'); cT3,k3=last('cenit_T3')
FB,rB=chain2([cT2,cT3],{8.0:ancB[8.0]})
for g in (1.0,2.0,4.0): FB[g]=ancB[g]
oA=oct[oct.sensor=='A'].set_index('ganancia_x')
rows=[]
for sen,F in (('A',FA),('B',FB)):
    for g in sorted(F):
        r={'sensor':sen,'ganancia_x':g}
        r.update({c:round(100*(F[g][c]-1),2) for c in CH})
        r['mediana_11']=round(float(np.median([100*(F[g][c]-1) for c in C11])),2)
        r['dif_NIR_F6']=round(100*(F[g]['nir_855nm']-F[g]['f6_640nm']),2)
        r['dif_F8_F7']=round(100*(F[g]['f8_745nm']-F[g]['f7_690nm']),2)
        rows.append(r)
R=pd.DataFrame(rows); R.to_csv(OUT,index=False)
pd.set_option('display.width',250)
print("\nFACTORES (ganancia real/nominal - 1, %, referidos a 4x):")
print(R[['sensor','ganancia_x','f6_640nm','f7_690nm','f8_745nm','nir_855nm','mediana_11','dif_NIR_F6','dif_F8_F7']].to_string(index=False))
print("\nComparación con octubre para A (2x, 8x):")
for g in (2.0,8.0): print(g, 'oct', round(float(np.median([oA.loc[g,c] for c in C11])),2),'nov', R[(R.sensor=='A')&(R.ganancia_x==g)].mediana_11.values)
print("\nResiduos en solapes (A):"); [print(g, round(float(np.median([v[c] for c in C11])),3), 'NIR',round(v['nir_855nm'],3),'F6',round(v['f6_640nm'],3)) for g,v in rA]
print("Residuos en solapes (B):"); [print(g, round(float(np.median([v[c] for c in C11])),3), 'NIR',round(v['nir_855nm'],3),'F6',round(v['f6_640nm'],3)) for g,v in rB]
print("cenit usados:",k2,k3)
# comparar corridas repetidas del cenit
for pref in ('cenit_T3','cenit_T2'):
    ks=sorted(t for t in res if t.startswith(pref))
    for t in ks:
        pr=res[t][3]; gs=sorted(pr)
        print(t, ' '.join(f"{b:g}/{a:g}:{np.median([100*(pr[b][c]/pr[a][c]-1) for c in C11]):+.2f}%" for a,b in zip(gs,gs[1:])))
