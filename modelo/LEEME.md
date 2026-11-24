# Modelo de biomasa

| Archivo | Qué es |
|---|---|
| `Entrenamiento_de_ModeloML_maspasto2.ipynb` | Cuaderno de Google Colab con el que se entrenó el modelo instalado en el equipo (`raspberry_pi/modelo_pasturametrics.pkl`). |
| `cv_por_sitio_y_fecha.py` | Validación cruzada por sitio y fecha con la asignación de grupos a pliegues escrita explícitamente, para que no dependa de la versión de scikit-learn. |
| `verificacion_modelo.py` | Evaluación del documento final (Tabla de modelos): validación cruzada barajada 5×10, sin barajar y agrupada por sitio y fecha; comparación con XGBoost, regresión lineal y predictor trivial. |

## Datos
Conjunto público CSIRO de Liao *et al.* (2025), *Estimating Pasture Biomass from Top-View Images: A Dataset for Precision Agriculture*, arXiv:2510.22916. Los programas leen su archivo `train.csv` (columnas `sample_id`, `target_name`, `target`, `Pre_GSHH_NDVI`, `Height_Ave_cm`, `State`, `Sampling_Date`, entre otras), que debe ponerse en la misma carpeta. No se incluye aquí; se descarga de la fuente publicada por los autores.

- Variable objetivo: biomasa verde total (`target_name == "GDM_g"`, 357 muestras), convertida a kg/ha multiplicando los gramos del cuadrante de 70 × 30 cm por 47,619.
- Entradas: NDVI (`Pre_GSHH_NDVI`, medido con GreenSeeker), altura media (`Height_Ave_cm`) y su producto.
- Modelo instalado: `RandomForestRegressor(n_estimators=100, random_state=42)` entrenado con las 357 muestras y guardado con `joblib.dump(..., compress=3)`.

## Desempeño (documento final, Sección 8)
R² de 0,48 ± 0,17 en validación cruzada barajada; 0,23 ± 0,28 cuando las particiones separan sitios y fechas (0,36 ± 0,20 con la asignación de grupos de las versiones recientes de scikit-learn; ver `cv_por_sitio_y_fecha.py`); 0,91 sobre los datos de entrenamiento (sobreajuste). En la partición de prueba de 90 muestras la regresión lineal con NDVI×altura (0,31) quedó a la par del Random Forest (0,28). Inferencia en la Raspberry Pi: 27,3 ms.

**El modelo es demostrativo.** El NDVI del equipo es relativo a su referencia y no es el del GreenSeeker, y el modelo no está calibrado para pasturas colombianas. Para usarlo en campo hay que recalibrarlo con cortes y pesaje medidos junto con el dispositivo.

## Reentrenar
1. Poner `train.csv` junto al cuaderno y ejecutarlo (en Colab o en Python con pandas, scikit-learn, xgboost y matplotlib).
2. Copiar el `modelo_pasturametrics.pkl` resultante a `~/maspasto2/` en la Raspberry Pi. `modelo_biomasa.py` espera las columnas `Pre_GSHH_NDVI`, `Height_Ave_cm` y `NDVI_x_Altura`; si se cambian las entradas hay que cambiar también esa función.
3. Conviene entrenar con la misma versión de scikit-learn que tiene la Pi (1.7.2).

## Revisión del entrenamiento (20 nov 2026)
- **Correcto:** el filtro deja una fila por imagen (357, sin valores faltantes), así que no hay fuga de información entre entrenamiento y prueba; la conversión a kg/ha (× 47,619 para un cuadrante de 0,21 m²) es correcta; el modelo final se entrena con todas las muestras, como corresponde para desplegarlo. Las salidas guardadas del cuaderno (R² de prueba 0,283, RMSE 891, CV 0,572 ± 0,051, importancia de NDVI×altura 0,64, archivo de 769,9 KB y predicción de 4405 kg MS/ha) coinciden con el modelo instalado y con el documento.
- **Límites:** el modelo sobreajusta (R² de 0,91 sobre los datos de entrenamiento frente a 0,48 en validación cruzada); 55 muestras repiten el mismo par NDVI–altura con biomasas distintas, un ruido que ningún modelo con esas dos entradas puede explicar; y generaliza poco a sitios nuevos (dejando fuera un estado completo, R² de 0,12 a 0,64).
- **Mejora posible, no aplicada:** con hojas de al menos 5 muestras (`min_samples_leaf=5`) el R² sube a 0,54 en validación barajada y a 0,29 por sitio y fecha (0,39 con la asignación de grupos de las versiones recientes de scikit-learn), con menos sobreajuste (0,75 en entrenamiento). No se cambió el modelo instalado porque es el que se validó en el equipo; conviene aplicarlo al recalibrar con datos colombianos.
- Las entradas medidas por el dispositivo en campo (NDVI de 0,21 a 0,83 y alturas de 1 a 12 cm) quedan dentro del intervalo de entrenamiento (0,16 a 0,91 y 1 a 70 cm), pero el NDVI del dispositivo es relativo a su referencia y no es el mismo instrumento que el de los datos de entrenamiento.
