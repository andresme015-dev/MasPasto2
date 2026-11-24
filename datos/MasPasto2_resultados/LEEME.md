# MasPasto2 — Resultados crudos y derivados

Carpeta de datos del proyecto de grado MasPasto2 (Andrés Felipe Méndez Martínez, Ingeniería Electrónica, Uniandes, 2026-20). Sirve como anexo de datos del informe y se amplía con cada sesión de pruebas.

## Contenido

| Elemento | Qué es |
|---|---|
| `indice_corridas.csv` | Una fila por archivo: sesión, fecha real, prueba, **estado** (válido, válido con reservas, exploratorio, auxiliar, descartado), motivo, dónde se usa en el informe, filas, duración, ganancias, pares emparejados y si hay temperatura. Se abre en Excel. |
| `sesiones.md` | Montaje, condiciones y resultados principales de cada sesión. |
| `diccionario_columnas.md` | Qué significa cada columna de los CSV y cómo se normalizan las lecturas. |
| `AAAA-MM-DD_lugar_tema/crudos/` | CSV crudos de la sesión, con el nombre original. `crudos/descartados/` guarda los que no se usan, sin borrarlos. |
| `AAAA-MM-DD_lugar_tema/interfaz/` | Lo que guardó la interfaz web (mediciones, pares crudos, sesión y fotos de la cámara), desde el 4 de noviembre. |
| `AAAA-MM-DD_lugar_tema/fotos/` | Fotos de esa sesión tomadas con el celular. |
| `derivados/` | Tablas recalculadas desde los crudos con `analisis/tablas_derivadas.py`; cada una corresponde a una tabla o figura del informe. |
| `analisis/` | Scripts de Python que leen los crudos y producen los derivados y las figuras. |
| `fotos/` | Fotos de los montajes usadas en el informe. |
| `verificacion_informe_v3.md` | Revisión de cada cifra del informe v3 contra los datos y de su coherencia con la propuesta. |

## Sesiones incluidas (corte 13 nov 2026, informe de avance v6)

| Carpeta | Qué se hizo | Sección del informe v6 |
|---|---|---|
| `2026-10-06_lab_lidar` | Calibración del LiDAR contra cinta métrica (18 000 lecturas) | Documento final, Sec. 8 y Apéndice B.14 |
| `2026-10-21_lab_estabilidad_ganancias` | Estabilidad, criterio de saturación, primeros factores de ganancia, oscuridad, primera sesión A+B | 9.5 |
| `2026-10-22_lab_caja_oscura` | Estabilidad, factores de ganancia 1–8×, factor k, transmitancia del PTFE | 9.5 |
| `2026-10-26_casa_prueba_cenit` | Prueba del cenit armado | — |
| `2026-10-26_campo_uniandes` | Primera salida de campo: saturación, validación y E4 con nubes | 9.6 |
| `2026-10-28_lab_PTFE_E1_E4` | Láminas de PTFE, llenado, E1 y E4 con lámpara | 9.8 |
| `2026-11-04_casa_sensores_reales` | BMP280 y primera prueba de la interfaz con sensores | 9.10 |
| `2026-11-05_campo_sol_nube` | Sol frente a nube, ganancia fija, saturación al sol, interfaz en campo | 9.11 |
| `2026-11-06_casa_ganancias_2a256` | Factores de ganancia de 2 a 256× y oscuridad hasta 512× | 9.12 |
| `2026-11-10_sitio_E2_superficies` | E2 en sitio con la interfaz (referencia gris), fotos de las huellas y fracción verde | 9.13 |
| `2026-11-10_noche_angular_E3_05x` | Oscuridad a 1024×, respuesta angular del cenit, fuga de F6, E3 con luz fija y factor de 0,5× del nadir | 9.14 |
| `2026-11-11_tarde_par_superficies_E_F` | Par blanco–gris, pasto seco, tierra y V1 de control con la interfaz; autosombra, campo de visión, 0,5× del cenit y atenuador | 9.15 |
| `2026-11-13_ventana_cenit_mediodia` | Cenit con sol directo, con y sin atenuador | 9.15 |

## Cómo regenerar los derivados nuevos
- 5 nov: `python3 -I analisis/campo5_porarchivo.py 2026-11-05_campo_sol_nube/crudos derivados/campo_5nov_cocientes_por_archivo.csv` y luego `python3 -I analisis/campo5_bloques.py derivados/campo_5nov_cocientes_por_archivo.csv derivados/campo_5nov_indices_por_bloque.csv`.
- 6 nov: `python3 -I analisis/casa6_factores_ganancia.py 2026-11-06_casa_ganancias_2a256/crudos derivados/casa6_factores_ganancia.csv`.
- 10 nov: `python3 -I analisis/sitio10_e2.py 2026-11-10_sitio_E2_superficies derivados` (agrega `figura.pdf` como tercer argumento para la figura del informe). Comprueba también que los pares crudos coincidan con cada medición.
- Noche del 10 nov: `python3 -I analisis/noche10_analisis.py 2026-11-10_noche_angular_E3_05x/crudos derivados` (agrega `figura.pdf` para la figura del informe).
- Tarde del 11 nov: `python3 -I analisis/tarde11_analisis.py 2026-11-11_tarde_par_superficies_E_F derivados` (agrega `figura.pdf` para la figura del informe). Comprueba también los pares de la interfaz y las fotos vacías.
- Cenit con sol del 13 nov: `python3 -I analisis/mediodia13_analisis.py 2026-11-13_ventana_cenit_mediodia derivados`.
- Todos se comprobaron: reproducen exactamente las tablas guardadas.

## Cómo regenerar las figuras del documento final
Las versiones de Python y de las librerías con que se generaron están en `requirements.txt` (`pip install -r requirements.txt`); con ellas las figuras salen idénticas a las del documento.
Desde esta carpeta, cada programa vuelve a dibujar las figuras de datos a partir de los crudos y los derivados:
- `python3 -I analisis/figuras_documento_final.py . <salida>`: Figs. 4, 5, 7, 8, 9 y 10 (ganancias, óptica, compensación, saturación, E2 y modelo). La del modelo grafica los valores que calculan `modelo/verificacion_modelo.py` y `modelo/cv_por_sitio_y_fecha.py` del repositorio, que necesitan el `train.csv` de CSIRO.
- `python3 -I analisis/lidar_calibracion.py [salida]`: Fig. 6 (LiDAR) y todas las métricas de la calibración.
- `python3 -I analisis/generar_apC.py`: tablas y figuras del informe de validación (Apéndice B).
- `python3 -I analisis/figuras_avance2.py` y `figuras_avance3.py`: figuras de k y de las láminas de PTFE del Apéndice B (`lab_k.pdf` y `lab29_ptfe.pdf`, en `salidas/figuras_avance/`).
Las fotos del montaje, del prototipo y de la interfaz no salen de los datos: son fotos y capturas de pantalla.

## Reglas
1. **Los crudos no se editan.** Cualquier corrección se hace en el análisis.
2. **Nada se borra:** lo que no sirve va a `descartados/` y su motivo al índice.
3. El nombre del archivo lleva la hora del reloj de la Raspberry, que puede estar mal; la fecha real va en el índice.

## Cómo agregar una sesión nueva
1. Copiar desde la Raspberry (PowerShell):
   `scp andresmendez@192.168.4.1:~/maspasto2/datos_espectro/* C:\Users\andre\Desktop\<carpeta>\`
2. Crear la carpeta `AAAA-MM-DD_lugar_tema/crudos/` y poner allí los CSV de la sesión.
3. Agregar sus filas a `indice_corridas.csv` (o regenerarlo con `analisis/construir_indice.py`, que clasifica por nombre y escribe el índice).
4. Agregar la sesión a `sesiones.md`.
5. Regenerar los derivados: `python3 -I analisis/tablas_derivadas.py <esta carpeta>`.

## Uso como anexo
En el documento final, el anexo de datos puede ser el índice de corridas (tabla) más el enlace a esta carpeta comprimida. Los derivados permiten reproducir cada tabla del informe sin repetir el análisis a mano.
