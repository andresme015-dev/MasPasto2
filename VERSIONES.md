# Versiones de los programas y verificación

Este repositorio publica **los mismos programas que corren en el equipo**. Se verificaron así:

1. El 20 de noviembre de 2026 se comprimió la carpeta `~/maspasto2` de la Raspberry Pi del prototipo (sin los datos) y se sacó la huella MD5 de cada archivo en la propia Pi (`md5_pi.txt`).
2. Las 34 huellas coincidieron con los archivos del comprimido.
3. Cada archivo de `raspberry_pi/` tiene la misma huella que su original en la Pi (tabla de abajo).

## Módulo nadir (`raspberry_pi/`): versión instalada en el equipo

| Archivo | MD5 | Qué hace |
|---|---|---|
| `medir.py` | `a142c2ccadbee992466d50033700ddd3` | Flujo de una medición: pares nadir/cenit, factores de ganancia, índices, altura, foto y biomasa. |
| `servidor.py` | `a670c99da7cfe67824d0f3954e6d2cf5` | Servidor web de la interfaz (librería estándar de Python) y copia a memoria USB. |
| `interfaz.html` | `857ed75a0bf8430f3903c4006e48fc60` | Pantallas del celular: Inicio, Medir y Datos. |
| `factores_ganancia.json` | `a90d2e41ffb666a6ce89ef8bcbddbcb0` | Desviación de la ganancia real frente a la nominal por sensor, ganancia y canal. |
| `caracterizacion_espectro.py` | `52d3db01082285c272d418e19bbd6979` | Programa de caracterización (registro, ganancias, oscuridad, intercomparación, PTFE, saturación). `medir.py` usa sus rutinas de lectura. |
| `receptor_zenit.py` | `1291ce6e77f6fe6642427f77d5117359` | Recibe los paquetes UDP del cenit (puerto 5005) y le envía órdenes de ganancia (puerto 5006). |
| `test_as7343.py` | `045343d6586ad3d2309e1a2b5d34ec2a` | Lectura del AS7343 del nadir (I²C 0x39) con ganancia adaptativa. |
| `test_bmp280.py` | `af079ede1c0c9b6ba792f511ca6fab1f` | Temperatura (I²C 0x76). |
| `test_tfnova.py` | `7ff8f2052238e848bab852d35d00e93c` | LiDAR TF-Nova por `/dev/ttyUSB0`. |
| `test_camara.py` | `8c459c4914051f109bb6e5ccaccb9b14` | Cámara OV5647 (picamera2). |
| `test_mpu6050.py` | `e5dbb8e539bef4ff3c2a94966eb495ff` | Inclinómetro (I²C 0x69). No quedó integrado en el montaje final. |
| `test_ds3231.py` | `09bd039672af67445af4a29e60bdbe62` | Reloj de tiempo real (I²C 0x68). No quedó integrado en el montaje final. |
| `set_rtc.py`, `rtc_a_sistema.py` | `f340bb20…`, `fb477fac…` | Escribir y leer la hora del DS3231. |
| `lidar_caracterizacion.py` | `604e2c62e40cc4277380bb5df967e62b` | Calibración del LiDAR contra cinta métrica (6 oct.). |
| `lidar_continuo.py` | `7202e3719ba3338ae6e7251406e3b5ad` | LiDAR en medición continua. |
| `modelo_biomasa.py` | `c0626de95c25aa653e3859c199ddd609` | Carga el modelo y estima la biomasa (kg MS/ha). |
| `modelo_pasturametrics.pkl` | `e9c5407ee686b15305e8e66a2cea55e1` | Random Forest entrenado (ver `modelo/`). |
| `LEEME.txt` | `2b00a1274aa03773af7c2ba0fcb743cc` | Notas de la carpeta en la Pi. |

## Versiones anteriores (`raspberry_pi/versiones_anteriores/`)

Se guardan porque algunas sesiones de prueba se hicieron con ellas.

| Archivo | MD5 | Uso |
|---|---|---|
| `medir_v1_29oct.py` | `dffaa508b6c079a7db318a770f502aaa` | Primera versión de la interfaz (29 oct.). Tomada de la copia del portátil del autor; ya no está en la Pi. |
| `medir_antes_10nov.py` | `81eb0d421e1efec8b8a7f3d74929be7f` | Versión del 4 de noviembre, usada hasta el 10 de noviembre. Con ella los archivos del 10 de noviembre quedaron sin línea de títulos y las fotos se sobrescribieron. |
| `respaldo_18nov/medir.py` | `a127b79cbc7f2b4bd71529e215122076` | Versión corregida la noche del 10 de noviembre (títulos y fotos), en el equipo hasta el 18 de noviembre. Calcula los índices con las ganancias nominales. |
| `respaldo_18nov/servidor.py` | `7de4732070ad4e69822fe89bba2716fa` | Servidor anterior al 18 de noviembre; la copia a USB podía fallar en memorias FAT. |
| `respaldo_18nov/interfaz.html` | `4cce19007e2e8fe75b6a38ff4ae29f8b` | Interfaz anterior al 18 de noviembre. |
| `caracterizacion_espectro_6nov.py` | `9b213d3e083b828469c116dfc0d1dd0a` | Versión del programa de caracterización usada hasta el 10 de noviembre. La final solo cambia una línea: tolera que falte la oscuridad de una ganancia. |
| `receptor_zenit_respaldo.py` | `e8d147d6596edabc35bbc6ae11bd41d1` | Receptor anterior, sin envío de órdenes. |
| `lidar_caracterizacion.py.save` | `c8bcb4485f93a06d74c426e738c1cca0` | Copia de seguridad del editor. |
| `test_as7341.py` | `4042c2f5cfc83a018aefc2230309c14e` | Prueba del AS7341, el espectrómetro que se reemplazó por el AS7343. |

El 18 de noviembre se instalaron `medir.py` (que aplica los factores de ganancia), `servidor.py`, `interfaz.html` y `factores_ganancia.json`. Antes de ese día, la interfaz calculaba los índices con las ganancias nominales; la diferencia con el recálculo con factores es de 0,0055 de NDVI como máximo (documento final, Sección 8).

## Firmware del cenit (`firmware_cenit/`)

| Archivo | MD5 del original | MD5 publicado | Uso |
|---|---|---|---|
| `firmware_zenit_as7343/firmware_zenit_as7343.ino` | `fea9be13b0bfe1467c4e38c37c44325f` | `2de099f8c9f61263f649cd0d40ac160a` | Firmware del cenit desde el 26 de octubre (tarde) hasta el final. En el computador del autor: `Descargas/firmware_zenit_as7343_no_apagado/` (26 oct., 16:24). |
| `versiones_anteriores/firmware_zenit_as7343_21oct/` | `f177aa9512809d29546bf2b3ea465ef1` | `f28ce854f8bc8d63397fa13c6b61bf4f` | Versión del 21 de octubre: si el sensor no responde al arrancar, se detiene sin conectar el Wi-Fi. |
| `versiones_anteriores/firmware_zenit_as7343_capsula_ptfe/` | `43dcd7b298ebd1aa43d069984ed01c8e` | `243eb13590ef8f07e34cdf01465be069` | Igual a la del 21 de octubre, con la etiqueta `capsula_ptfe` (archivo del 21 de octubre). Ningún dato del proyecto se tomó con ella (ver abajo). |
| `versiones_anteriores/firmware_zenit/` | `2602ad12f2aa0b20a4e3e8b964e5e626` | `22d6c9b63aa2f49678fe0b4783baff65` | Versión con el AS7341 (respaldo). |

**Cómo se identificó la versión cargada en el ESP32.** Cada paquete del cenit lleva el texto `config` fijado en el firmware. En todos los datos crudos desde la segunda sesión del 26 de octubre hasta el 13 de noviembre ese texto es `cenit_3mm`, que solo existe en la versión `fea9be13…` (la del 21 de octubre envía `desnudo`, y así aparece en los datos del 21 y el 22 de octubre). Es una etiqueta fija: no indica la distancia real entre el sensor y el difusor, que fue de 2 a 3 cm.

**Versión `capsula_ptfe`.** El autor la señaló al principio como la última carga, pero en su carpeta de Descargas está guardada como `firmware_zenit_as7343_medicion` con fecha del 21 de octubre, es decir, es anterior a la versión principal, que está en la misma carpeta como `firmware_zenit_as7343_no_apagado` (26 de octubre, 16:24) y es idéntica byte a byte a la publicada (MD5 `fea9be13…` antes de quitar las claves). Además, la etiqueta `capsula_ptfe` no aparece en ningún dato crudo del proyecto. Lo más probable es que el ESP32 tenga la versión principal; para comprobarlo basta con encenderlo y correr `python3 receptor_zenit.py` en la Pi: el campo `config` de los paquetes dice `cenit_3mm` (principal) o `capsula_ptfe`. Esa versión, si el sensor no responde al arrancar, deja el ESP32 detenido sin Wi-Fi; la principal sigue conectada y envía avisos.

**Única diferencia con el original.** En las copias publicadas se reemplazaron las credenciales de Wi-Fi por textos de ejemplo (`NOMBRE_RED_CASA`, `CLAVE_RED_CASA`, `IP_DE_LA_RPI_EN_CASA`, `CLAVE_RED_PASTURAMETRICS`). La lógica no cambió. Antes de cargar el firmware hay que escribir la clave real de la red del dispositivo en `PASS_AP`.

## Modelo (`modelo/`)

El cuaderno `Entrenamiento_de_ModeloML_maspasto2.ipynb` entrena el Random Forest con `n_estimators=100` y `random_state=42` sobre las 357 muestras de biomasa verde del conjunto público CSIRO y lo guarda como `modelo_pasturametrics.pkl`. El modelo instalado tiene esos mismos parámetros y las mismas tres entradas. Al reentrenarlo con scikit-learn 1.9.1 se obtiene la misma predicción de referencia (4405,1 kg MS/ha para NDVI 0,70 y 15 cm); sobre las muestras de entrenamiento, las predicciones difieren hasta en 41 kg MS/ha, lo que se atribuye a la versión de la librería.

## Análisis (`datos/MasPasto2_resultados/analisis/`)

Programas que leen los datos crudos y escriben las tablas derivadas y las figuras del documento final. El 20 de noviembre se ejecutaron todos desde los crudos de esta carpeta y las 34 tablas de `derivados/` se reprodujeron: 32 idénticas, la de índices por bloque del 5 de noviembre con diferencias de 5×10⁻⁵ (redondeo) y la de cocientes por archivo del 5 de noviembre, que en la versión guardada tiene una fila más de un archivo sin pares válidos (`W_nube_8`, 9:43) que después se movió a `crudos/descartados/`; no cambia ningún resultado. El 22 de noviembre se corrigió el diámetro real de dos discos de la prueba de campo de visión (22 y 32 cm; el programa de medición los había etiquetado con los diámetros propuestos, 24 y 30 cm): cambian solo `tarde11_fov.csv` y `tarde11_fov_corridas.csv`, y el semiángulo ajustado sigue en 35°. El 23 de noviembre, al recalcular todo desde los crudos con un código independiente, se corrigió `campo5_porarchivo.py` para que descarte los pares con más de 0,3 s de desfase (el criterio del documento) y calcule el CV de la luz sobre la señal normalizada por la ganancia (las cuentas crudas subestiman el cambio de luz porque la ganancia adaptativa lo compensa); cambian las tres tablas del 5 de noviembre (por ejemplo, el NDVI con nublado pasa de 0,7430 a 0,7429 y el CV medio de la luz en los bloques de sol, de 10 a 11 %). Usan rutas relativas a la carpeta `MasPasto2_resultados`, así que corren en cualquier computador sin cambiar nada; las figuras y tablas que no van a `derivados/` quedan en `MasPasto2_resultados/salidas/`. `armar_entregable.py` arma el conjunto de prueba desde `datos/exportacion_usb_18nov/` y `generar_apC.py` las tablas y figuras del informe de validación (Apéndice B del documento). También la noche del 23 de noviembre se agregó `lidar_calibracion.py`, que recalcula desde los crudos todas las métricas de la calibración del LiDAR y dibuja la Fig. 6 (antes la figura venía del primer informe de avance, sin programa en esta carpeta), y se corrigió en `figuras_documento_final.py` el R² de XGBoost en validación barajada (0,38 y no 0,39: el valor exacto es 0,3845); al volver a generar todas las figuras de datos desde los crudos coinciden con las del documento. Al probar `requirements.txt` en un entorno de Python nuevo, diez de esas figuras salían corridas unos pocos píxeles porque matplotlib suaviza el texto distinto según la instalación; los cinco programas de figuras fijan ahora ese ajuste (`text.hinting: no_hinting`) y las doce figuras de datos salen idénticas a las del documento en los dos entornos probados.
