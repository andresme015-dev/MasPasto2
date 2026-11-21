"""Validación cruzada agrupada por sitio y fecha del documento final, con la asignación de grupos a pliegues
escrita explícitamente, para que el resultado no dependa de la versión de scikit-learn.

verificacion_modelo.py usa GroupKFold(5). Hasta la versión con que se hizo el documento, GroupKFold ordenaba los
grupos de mayor a menor tamaño y ponía cada uno en el pliegue con menos muestras; versiones posteriores de
scikit-learn reparten los grupos de otra forma y el R² cambia (Random Forest: 0,36 ± 0,20 con la 1.9.1).
Este programa calcula las dos asignaciones. Uso: python3 cv_por_sitio_y_fecha.py  (con train.csv al lado)."""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold, cross_validate
from xgboost import XGBRegressor

df = pd.read_csv("train.csv")
g = df[df.target_name == "GDM_g"].copy().reset_index(drop=True)
g["NDVI_x_Altura"] = g.Pre_GSHH_NDVI * g.Height_Ave_cm
X = g[["Pre_GSHH_NDVI", "Height_Ave_cm", "NDVI_x_Altura"]]
y = g.target * 47.619
grupos = g.State + "_" + g.Sampling_Date

u, inv = np.unique(grupos, return_inverse=True)
n = np.bincount(inv)
peso, pliegue_de = np.zeros(5), np.zeros(len(u), int)
for i in np.argsort(n)[::-1]:                 # de mayor a menor tamaño, al pliegue más liviano
    k = int(np.argmin(peso)); peso[k] += n[i]; pliegue_de[i] = k
pl = pliegue_de[inv]
ASIGNACIONES = {"por tamaño (documento)": [(np.where(pl != k)[0], np.where(pl == k)[0]) for k in range(5)],
                "GroupKFold de la versión instalada": list(GroupKFold(5).split(X, y, grupos))}
MODELOS = {"Random Forest": lambda: RandomForestRegressor(n_estimators=100, random_state=42),
           "XGBoost": lambda: XGBRegressor(n_estimators=100, random_state=42, learning_rate=0.1, verbosity=0),
           "Lineal (NDVI×altura)": lambda: LinearRegression(), "Media (trivial)": lambda: DummyRegressor()}
for nombre, cv in ASIGNACIONES.items():
    print(f"\n== {nombre}")
    for m, f in MODELOS.items():
        XX = X[["NDVI_x_Altura"]] if m.startswith("Lineal") else X
        r = cross_validate(f(), XX, y, cv=cv, scoring="r2")["test_score"]
        print(f"{m:22s} R2 {r.mean():.3f} ± {r.std():.3f}")
