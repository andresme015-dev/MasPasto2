"""Modelo Random Forest de estimacion de biomasa (kg MS/ha).
Requiere el archivo modelo_pasturametrics.pkl en esta misma carpeta."""
import os
import time
import warnings

warnings.filterwarnings("ignore", category=UserWarning)   # aviso de version de scikit-learn

import joblib
import pandas as pd

RUTA_MODELO = os.path.expanduser("~/maspasto2/modelo_pasturametrics.pkl")
modelo = joblib.load(RUTA_MODELO)        # se carga una sola vez al importar


def estimar_biomasa(ndvi, altura_cm):
    entrada = pd.DataFrame(
        [[ndvi, altura_cm, ndvi * altura_cm]],
        columns=["Pre_GSHH_NDVI", "Height_Ave_cm", "NDVI_x_Altura"],
    )
    return round(float(modelo.predict(entrada)[0]), 1)


if __name__ == "__main__":
    t0 = time.perf_counter()
    b = estimar_biomasa(0.70, 15)
    ms = (time.perf_counter() - t0) * 1000
    print(f"NDVI 0,70 y altura 15 cm -> {b} kg MS/ha  ({ms:.2f} ms)")
    print("Valor de referencia del modelo original: 4405.1 kg MS/ha")
