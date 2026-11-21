import pandas as pd, numpy as np, sys
T=pd.read_csv(sys.argv[1],dtype={'hora':str}).set_index('hora')
C=['f6_640nm','f7_690nm','f8_745nm','nir_855nm']
# hora -> (rol, bloque, condicion)
M={'085212':('W','n1','mixto'),'085253':('G','n1','mixto'),'085409':('Gf','n1','mixto'),'085526':('Wf','n1','mixto'),
 '083214':('W','n0','mixto (8:32)')}
for k,(g,gf) in enumerate([('084756','085002'),('085746','085825'),('085937','090022'),('090306','090338'),('090430','090507')],1):
    M[g]=('G',f's{k}','sol'); M[gf]=('Gf',f's{k}','sol')
nube={2:('090716','090852','090951','091127'),3:('091224','091336','091426','091558'),4:('091718','091827','091929','092106'),
 5:('092235','092333','092530','092728'),6:('093041','093139','093211','093313'),7:('093413','093503','093540','093652'),
 8:('094414','094458','094534','094638'),9:('094714','094758','094831','094940'),10:('095054','095149','095225','095326')}
for b,hs in nube.items():
    cond='sombrilla' if b<=6 else ('sombrilla, mixto' if b==7 else 'nublado natural')
    for rol,h in zip(('W','G','Gf','Wf'),hs): M[h]=(rol,f'n{b}',cond)
def q(h): return np.array([T.loc[h,'q_'+c] for c in C])
def idx(r):
    f6,f7,f8,nir=r
    return (nir-f6)/(nir+f6),(nir-f8)/(nir+f8),(f8-f7)/(f8+f7)
rows=[]
Wover=np.mean([q(nube[b][0]) for b in (8,9,10)],axis=0)
Wfover=np.mean([q(nube[b][3]) for b in (8,9,10)],axis=0)
for b in ['n1']+[f'n{i}' for i in range(2,11)]:
    hs={M[h][0]:h for h in M if M[h][1]==b}
    for modo,g,w in (('adaptativa','G','W'),('fija 0,5x','Gf','Wf'),('Gf con W','Gf','W')):
        rho=q(hs[g])/q(hs[w]); n,r1,r2=idx(rho)
        rows.append(dict(bloque=b,cond=M[hs[g]][2],modo=modo,G=hs[g],W=hs[w],rho_f6=rho[0],rho_f7=rho[1],rho_f8=rho[2],rho_nir=rho[3],NDVI=n,NDRE1=r1,NDRE2=r2))
for k in range(1,6):
    hs={M[h][0]:h for h in M if M[h][1]==f's{k}'}
    for modo,g,wq,wn in (('adaptativa, W nube1','G',q('085212'),'085212'),('adaptativa, W nublado 8-10','G',Wover,'W8-10'),
                         ('fija, Wf nube1','Gf',q('085526'),'085526'),('fija, Wf nublado 8-10','Gf',Wfover,'Wf8-10')):
        rho=q(hs[g])/wq; n,r1,r2=idx(rho)
        rows.append(dict(bloque=f's{k}',cond='sol',modo=modo,G=hs[g],W=wn,rho_f6=rho[0],rho_f7=rho[1],rho_f8=rho[2],rho_nir=rho[3],NDVI=n,NDRE1=r1,NDRE2=r2))
R=pd.DataFrame(rows); R.to_csv(sys.argv[2],index=False)
pd.set_option('display.width',250)
print(R.round(4).to_string(index=False))
# white consistency
print('\nBlancos: cociente q (nadir/cenit) normalizado')
for h in sorted(M):
    if M[h][0] in('W','Wf'): print(h,M[h], np.round(q(h),4), 'NIR/F6=%.4f'%(q(h)[3]/q(h)[0]))
print('W/Wf por bloque (debe ser 1 si la ganancia nominal es exacta y la luz estable):')
for b,hs in list(nube.items())+[(1,('085212',None,None,'085526'))]:
    print(b, np.round(q(hs[0])/q(hs[3]),3), T.loc[hs[0],'g_n'],T.loc[hs[0],'g_z'])
