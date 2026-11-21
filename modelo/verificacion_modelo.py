import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split, cross_val_score, KFold, GroupKFold, RepeatedKFold, cross_validate, LeaveOneGroupOut
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.dummy import DummyRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor
df=pd.read_csv('train.csv')
w=df.pivot_table(index=['sample_id_base'] if False else df.sample_id.str.split('__').str[0], columns='target_name', values='target')
print('GDM = Green+Clover ?', np.allclose(w.GDM_g, w.Dry_Green_g+w.Dry_Clover_g, atol=1e-3), ' Total = Green+Clover+Dead ?', np.allclose(w.Dry_Total_g, w.Dry_Green_g+w.Dry_Clover_g+w.Dry_Dead_g, atol=1e-3))
gdm=df[df.target_name=='GDM_g'].copy().reset_index(drop=True)
gdm['NDVI_x_Altura']=gdm.Pre_GSHH_NDVI*gdm.Height_Ave_cm; gdm['biomasa_kg_ha']=gdm.target*47.619
X=gdm[['Pre_GSHH_NDVI','Height_Ave_cm','NDVI_x_Altura']]; y=gdm.biomasa_kg_ha
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.25,random_state=42)
def mk(n):
    return {'RF':RandomForestRegressor(n_estimators=100,random_state=42),
            'XGB':XGBRegressor(n_estimators=100,random_state=42,learning_rate=0.1,verbosity=0),
            'Lineal (NDVIxAltura)':LinearRegression(),'Media (trivial)':DummyRegressor()}[n]
print('\n== Reproducción del cuaderno (partición 75/25 y CV 5 sin barajar)')
for n in ['RF','XGB','Lineal (NDVIxAltura)','Media (trivial)']:
    m=mk(n); Xa,Xb=(Xtr[['NDVI_x_Altura']],Xte[['NDVI_x_Altura']]) if n.startswith('Lineal') else (Xtr,Xte)
    m.fit(Xa,ytr); p=m.predict(Xb)
    XX=X[['NDVI_x_Altura']] if n.startswith('Lineal') else X
    cv=cross_val_score(mk(n),XX,y,cv=5,scoring='r2')
    print(f"{n:22s} test R2 {r2_score(yte,p):.3f} RMSE {np.sqrt(mean_squared_error(yte,p)):.1f} MAE {mean_absolute_error(yte,p):.1f} | CV5 R2 {cv.mean():.3f} ± {cv.std():.3f} folds {np.round(cv,3)}")
print('\nOrden de datos: ¿está agrupado? primeros estados:', gdm.State.head(10).tolist())
groups=gdm.State+'_'+gdm.Sampling_Date
schemes={'KFold 5 barajado x10':RepeatedKFold(n_splits=5,n_repeats=10,random_state=0),
         'GroupKFold 5 (sitio+fecha)':GroupKFold(n_splits=5)}
for sname,cvs in schemes.items():
    print(f'\n== {sname}')
    for n in ['RF','XGB','Lineal (NDVIxAltura)','Media (trivial)']:
        XX=X[['NDVI_x_Altura']] if n.startswith('Lineal') else X
        r=cross_validate(mk(n),XX,y,cv=cvs,groups=groups if 'Group' in sname else None,scoring=('r2','neg_root_mean_squared_error','neg_mean_absolute_error'))
        print(f"{n:22s} R2 {r['test_r2'].mean():.3f} ± {r['test_r2'].std():.3f}  RMSE {-r['test_neg_root_mean_squared_error'].mean():.0f}  MAE {-r['test_neg_mean_absolute_error'].mean():.0f}")
# leave-one-state-out
print('\n== Dejar un estado fuera (RF)')
for st in gdm.State.unique():
    tr=gdm.State!=st; m=mk('RF').fit(X[tr],y[tr]); p=m.predict(X[~tr])
    print(st, (~tr).sum(), 'R2 %.3f RMSE %.0f'%(r2_score(y[~tr],p),np.sqrt(mean_squared_error(y[~tr],p))))
# final model
mf=mk('RF').fit(X,y); import pandas as pd
e=pd.DataFrame([[0.7,15,10.5]],columns=X.columns); print('\npred 0.7/15:',mf.predict(e))
print('train R2 (in-sample)', r2_score(y,mf.predict(X)))
# heights distribution vs test case
print('altura percentiles', np.percentile(gdm.Height_Ave_cm,[50,90,95,99]), ' n>=15cm', (gdm.Height_Ave_cm>=15).sum())
# residuals vs magnitude (RF on test)
m=mk('RF').fit(Xtr,ytr); p=m.predict(Xte); res=yte-p
for lo,hi in [(0,1000),(1000,2000),(2000,9000)]:
    k=(yte>=lo)&(yte<hi); print(f'residuos {lo}-{hi}: n={k.sum()} MAE {np.abs(res[k]).mean():.0f} sesgo {res[k].mean():.0f}')
