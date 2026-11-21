# Diccionario de columnas de los CSV crudos

Los CSV los escribe `caracterizacion_espectro.py` en la Raspberry Pi (`~/maspasto2/datos_espectro`). Los nombres de archivo siguen `<modo>_<sensores>_<config>_<etiqueta>_<AAAAMMDD>_<HHMMSS>.csv`. **La fecha y la hora del nombre son las del reloj de la Raspberry**, que se reinicia a 2026-04-15 ~13:33 cuando no se ajusta con `sudo date -s`: en esos casos la fecha real está en `indice_corridas.csv`.

Prefijo `n_` = módulo nadir (sensor A, en la Raspberry); prefijo `z_` = módulo cenit (sensor B, en el ESP32, llega por UDP). Los archivos antiguos (21 oct) traen solo el prefijo `n_` y algunas columnas menos.

| Columna | Significado |
|---|---|
| `modo` | Modo del programa: registro, ganancias, oscuridad, intercomparacion, ptfe, saturacion |
| `sensor_id`, `config` | Sensores usados (A, A-B, B) y configuración (lab, ptfe_lab, operacion, validacion, cenit_3mm…) |
| `etiqueta` | Nombre que se le dio a la corrida (p. ej. `E1_pasto`, `ref_6mm_negro`) |
| `fase`, `pasada`, `rep` | Fase (luz/oscuridad/sin/con), pasada (ida/vuelta, o A/B en la intercomparación) y número de lectura o repetición |
| `n_t`, `z_t` | Tiempo Unix de la lectura (s) |
| `*_ganancia_idx`, `*_ganancia_x` | Ganancia (índice del registro AGAIN y factor nominal, 0,5× a 2048×) |
| `*_t_int_ms` | Tiempo de integración por ciclo (182,37 ms con ATIME 99 y ASTEP 655) |
| `*_max_espectral`, `*_max_cuentas` | Canal espectral más alto y canal más alto de los 18, VIS incluido (cuentas) |
| `*_saturado`, `*_vis_saturado` | Lectura saturada según el criterio del proyecto (canal más alto ≥ 90 % de 65 535) y si el VIS superó ese límite |
| `*_sat_analogica`, `*_sat_digital` | Indicadores de saturación del sensor (STATUS2); nunca se activaron |
| `*_f1_405nm` … `*_nir_855nm` | Cuentas crudas de los 12 canales espectrales (F1, F2, FZ, F3, F4, F5, FY, FXL, F6, F7, F8, NIR) |
| `*_vis_c1..c3` | Canal VIS (sin filtro) en cada uno de los tres ciclos del modo de 18 canales |
| `*_var_luz_ciclos` | Variación relativa del VIS entre los tres ciclos: indicador de luz inestable durante la lectura |
| `*_temp_c` | Temperatura del BMP280 (°C); vacía si el sensor no estaba conectado |
| `z_seq` | Contador de paquetes del ESP32 (uno por segundo desde que arranca); sirve para ordenar corridas cuando el reloj de la Raspberry está mal |
| `z_rssi_dbm` | Potencia de la señal Wi-Fi del cenit |
| `z_desfase_s` | Diferencia de tiempo entre la lectura del nadir y el paquete del cenit emparejado (se descartan pares con más de 0,3 s cuando la luz cambia) |
| `z_id_sensor`, `z_config` | Identificación del sensor del cenit y montaje declarado en el firmware (`cenit_3mm`) |

**Normalización:** s = cuentas / (ganancia × t_int). **Cociente:** s_n/s_z por canal. **Reflectancia relativa:** (s_n/s_z)_superficie / (s_n/s_z)_blanco (Ec. 4 del informe).

Archivos `_resumen.csv`: resumen por corrida que calcula el programa al terminar (medias, CV, ganancias, factores). Archivos `_pasos.csv`: comparación de pasos consecutivos en las pruebas de ganancia. `oscuridad_*.json`: lecturas de oscuridad por ganancia (0 cuentas en todos los canales).

## CSV de la interfaz (`interfaz/mediciones_AAAAMMDD.csv`, desde el 4 nov)
Una fila por medición (cada una promedia 5 pares nadir–cenit).
- `id`, `punto`, `nota`: número, punto y nota que escribe el operador.
- `hora_celular` (UTC), `hora_rpi`, `hora_rtc`: hora del celular, de la Raspberry y del DS3231 (vacía si no está conectado).
- `simulado`: 1 si la medición fue con datos sintéticos (modo de prueba). `blanco_hora`: hora del blanco usado. `con_cenit`: 1 si hubo cenit. `pares_validos` / `pares_pedidos`.
- `ganancia_nadir`, `ganancia_cenit`: ganancias usadas (p. ej. `4/8` si cambió entre pares).
- `rho_f6`, `rho_f7`, `rho_f8`, `rho_nir`: reflectancia relativa al blanco (Ec. rho del informe). `ndvi`, `ndre1`, `ndre2`: índices.
- `cv_cociente_nir_pct`: variación del cociente nadir/cenit del NIR entre los 5 pares. `luz_relativa_blanco`: luz del cenit frente a la del blanco.
- `distancia_lidar_cm`, `suelo_cm`, `altura_cm`: LiDAR, distancia al suelo de la sesión y altura (suelo − distancia). `inclinacion_deg`: MPU-6050 (vacía si no está). `temp_c`: BMP280 dentro de la caja del nadir.
- `biomasa_kg_ms_ha`: estimación del modelo. `foto`: archivo de la cámara. `avisos`: sensores ausentes o pares sin cenit.
- `interfaz/crudo_AAAAMMDD.csv`: las cuentas de cada par, con el mismo formato de columnas `n_*` y `z_*` de los CSV de caracterización.

## Derivados del 10 nov (`derivados/sitio10_*.csv`)
- `sitio10_mediciones.csv`: las 26 mediciones de la interfaz con sus títulos, más estas columnas:
  - `fila`: orden en el archivo original.
  - `codigo` y `toma`: salen de la nota escrita en el campo "Punto".
  - `valida` y `motivo_descarte`.
  - `referencia`: cartulina gris.
  - Las reflectancias `rho_*` son relativas a la cartulina gris, no al blanco.
- `sitio10_canopeo_fotos.csv`: por foto, `cinta_pct` (píxeles de la cinta, excluidos) y `verde_pct` (fracción de píxeles verdes con las reglas de Canopeo).
- `sitio10_resumen.csv`: por superficie, la media y el rango (máximo − mínimo) de cada índice en las tomas válidas, y la fracción verde media, mínima y máxima de sus fotos.

## Derivados de la tarde del 11 nov (`derivados/tarde11_*.csv`)
Todas las señales se normalizan igual: `(S − oscuridad) / (G · t_int)`. Además se dividen por `(1 + factor/100)`, con el factor de ganancia de cada canal referido a 4× (tablas `casa6_`, `lab22_` y `noche10_factores_05`).
- `tarde11_interfaz.csv`: una fila por medición de la interfaz.
  - `rho_*`: reflectancia de los 12 canales frente al blanco de esa medición, recalculada desde los pares crudos.
  - `ndvi`, `ndre1` y `ndre2`: índices recalculados.
  - `ndvi_interfaz`: el que calculó la interfaz, sin factores de ganancia. Difiere en 0,0055 como máximo.
  - `luz_rel`: luz del cenit frente a la del blanco.
  - `foto_bytes`: tamaño de la foto; 0 si quedó vacía.
- `tarde11_par.csv`: reflectancia de Gr, N y B2 frente al cartón (media y desviación de tres tomas), corregida con C final. Las columnas `*_sin_corregir` no tienen esa corrección.
- `tarde11_superficies.csv`: índices de cada toma válida del 10 y el 11 de noviembre.
  - `*_gris`: con la referencia gris.
  - `*_carton`: convertidos al cartón, multiplicando cada banda por la reflectancia de la gris.
  - `verde_pct`: fracción verde (Canopeo, sin la cinta azul) de la foto de la cámara del dispositivo; solo el 11 de noviembre. `foto_usada` indica la foto; la de la medición 32 es la recuperada de la captura.
- `tarde11_autosombra.csv`: una fila por canal.
  - `efecto_15_vs_10_pct` y `ee_pct`: ajuste del log del cociente con una tendencia cuadrática en el tiempo y un término para la distancia, y su error estándar.
  - `vecinos_*` y `ultimo_pct`: cada toma a 15 cm frente a las tomas a 10 cm que la rodean.
  - `deriva_10cm_pct`: cambio entre la primera y la última toma a 10 cm.
- `tarde11_fov_corridas.csv`: cada corrida del campo de visión.
  - `F_*`: fracción de la señal del pliego blanco, `(q − q_negro) / (q_blanco − q_negro)`, con `q` el cociente nadir/cenit.
  - `F_med`: mediana entre FY y NIR.
  - `semiangulo_deg`: semiángulo del disco con la lámina a 12 cm de la ventana.
- `tarde11_fov.csv`: por disco, el promedio de las corridas completas.
  - `F_modelo`: coseno recortado en `th_max_ajuste_deg`.
  - `th_max_min_deg` y `th_max_max_deg`: el ajuste con cada combinación de repeticiones.
  - `th_max_H125mm_deg` y `th_max_H130mm_deg`: el ajuste con la lámina a 12,5 o a 13 cm del chip.
- `tarde11_factor05_cenit.csv`: factores del cenit a 0,5×, 1× y 2×, referidos a 4×.
  - `*_simetrico`: promedio de ida y vuelta.
  - `*_regresion` y `*_ee`: regresión con tendencia cuadrática de la luz, y su error estándar.
- `tarde11_atenuador.csv`: por ganancia.
  - `max_pct_*`: % de la escala de cada corrida.
  - `T_*`: transmitancia con / promedio de las dos sin.
  - `T2_*`: lo mismo con la corrida mal rotulada, que también tenía la lámina.
  - `sin2_vs_sin_*` y `descartada_vs_con_*`: concordancia entre corridas.

## Derivados del 13 nov (`derivados/mediodia13_atenuador.csv`)
- Una fila por corrida válida.
- `max_pct_05x`: % de la escala del canal más alto según el programa.
- `vis_pct_05x`: % del VIS más alto.
- `espectral_pct_05x`: % del canal espectral más alto.
- `cv_nir_pct`: CV del NIR en las 5 lecturas.
- `saturadas_1x`: lecturas saturadas a 1×.
- `T_*`: transmitancia de la lámina, con / promedio de las dos sin; solo en la fila con lámina.
- `tarde11_alturas.csv`: una fila por toma válida del 10 y el 11 nov. Columnas: distancia del LiDAR, suelo (58,8 cm), altura y biomasa que calculó la interfaz, y NDVI.
