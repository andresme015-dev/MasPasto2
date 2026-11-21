import pandas as pd, glob, os, sys
D=sys.argv[1]
rows=[]
for f in sorted(glob.glob(os.path.join(D,"*.csv"))):
    if "resumen" in f: continue
    try: d=pd.read_csv(f)
    except Exception as e: print("ERR",f,e); continue
    if len(d)==0: rows.append({"archivo":os.path.basename(f),"n":0}); continue
    hz='z_nir_855nm' in d and d['z_nir_855nm'].notna().any()
    r={"archivo":os.path.basename(f)[:-4].replace("registro_","").replace("sensorA-B_","AB_"),"n":len(d),
       "t0":d.n_t.iloc[0],"t1":d.n_t.iloc[-1],"G":d.n_ganancia_x.iloc[0],"Gvar":d.n_ganancia_x.nunique(),
       "maxn%":round(d.n_max_cuentas.max()/655.35,1),"satn":int(d.n_saturado.astype(bool).sum()),
       "nNIR":round(d.n_nir_855nm.mean(),0),"nF6":round(d.n_f6_640nm.mean(),0),
       "cvnNIR":round(d.n_nir_855nm.std()/d.n_nir_855nm.mean()*100,2)}
    if hz:
        ok=d.z_desfase_s.abs()<=0.3
        r.update({"ok":int(ok.sum()),"zseq0":d.z_seq.dropna().iloc[0] if d.z_seq.notna().any() else None,
                  "zNIR":round(d.z_nir_855nm.mean(),0),"zF6":round(d.z_f6_640nm.mean(),0),"maxz%":round(d.z_max_cuentas.max()/655.35,1),
                  "satz":int(d.z_saturado.astype(bool).sum()),
                  "cvqNIR":round(((d.n_nir_855nm/d.z_nir_855nm)[ok]).std()/((d.n_nir_855nm/d.z_nir_855nm)[ok]).mean()*100,2),
                  "cvqF6":round(((d.n_f6_640nm/d.z_f6_640nm)[ok]).std()/((d.n_f6_640nm/d.z_f6_640nm)[ok]).mean()*100,2),
                  "nanz":int(d.z_nir_855nm.isna().sum())})
    r["temp"]=round(d.n_temp_c.mean(),2) if d.n_temp_c.notna().any() else None
    rows.append(r)
df=pd.DataFrame(rows).sort_values("t0")
df["t0"]=pd.to_datetime(df.t0,unit="s").dt.strftime("%m-%d %H:%M:%S"); df["t1"]=pd.to_datetime(df.t1,unit="s").dt.strftime("%H:%M:%S")
pd.set_option("display.width",300); pd.set_option("display.max_columns",40); pd.set_option("display.max_rows",200)
print(df.to_string(index=False))
