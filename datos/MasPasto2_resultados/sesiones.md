# Sesiones de medición

Cada sesión tiene su carpeta con los CSV crudos tal como salieron de la Raspberry Pi (nombres sin cambiar) y una subcarpeta `descartados/`. El estado de cada archivo y el motivo están en `indice_corridas.csv`. Las secciones citadas son las del informe de avance v3 (corte 29 oct 2026); el detalle de cada decisión está en el registro de decisiones del proyecto (`decisiones_caracterizacion_AS7343.md`, secciones 1–12, y `pruebas_lab_28-29oct.md`).

## 2026-10-06 — Laboratorio: calibración del LiDAR
- **Montaje:** TF-Nova horizontal, elevado y nivelado; cinta métrica bajo el eje del haz, cero en la cara del lente; blanco: caja de cartón de 52 × 39 cm.
- **Protocolo:** 30 distancias de 5 a 150 cm cada 5 cm, 200 lecturas por punto, tres corridas (ida, vuelta, ida): 18 000 lecturas.
- **Resultado:** ajuste d_L = 0,9732 d + 0,77 cm (R² = 0,99982) entre 15 y 150 cm; corrección del dispositivo d = 1,0275 d_L − 0,80 cm; error máximo calibrado 1,4 cm.
- **Archivo:** `2026-10-06_lab_lidar/crudos/lidar_caracterizacion.csv` (programa `lidar_caracterizacion.py`).

## 2026-10-21 — Laboratorio: estabilidad, saturación, ganancias y primera sesión A+B
- **Montaje:** sensor A solo en la madrugada y la mañana; por la tarde (16:31–17:14), A en la Raspberry y B en el ESP32. Incandescente de 120 V primero y después halógena de 12 V y 20 W en fuente DC; en la sesión A+B la lámpara se sostuvo con la mano.
- **Resultados que se usan:** criterio de saturación con el VIS (32→64×: exceso de 889 a 1405 cuentas en los 12 canales; F1 +35 %, F6 +10 %, NIR +5 %); oscuridad de 0 cuentas en A y B de 1× a 16×; factor de 8× de A el 21 oct (−2,7 %); transmitancia de la cápsula con el techo a 2–3 cm (0,094–0,138).
- **Informe:** Sec. 9.5. Registro de decisiones §2–§9.
- **Archivos con fecha 2026-04-15** (reloj sin ajustar): `ganancias_nadir_..._133651` (madrugada, 8/16/32×), `ganancias_nadir_..._133924` (~15:15, 2/4/8×), `registro_estabilidad_..._133605` (madrugada).

## 2026-10-22 — Laboratorio: caja oscura con lámpara fija
- **Montaje:** caja de cartón como recinto oscuro, halógena fija en el techo a 34 cm de los sensores, fuente DC, base negra, luces apagadas, LED de las placas tapados (Fig. 11 del informe).
- **Resultados:** estabilidad (150 pares, 7,1 min: CV del NIR 0,04 % en A, 0,05 % en B, 0,03 % en el cociente); factores de ganancia (8×: −3,1 % en A y −3,2 % en B; Tabla 10); k con difusor común e intercambio A‑B‑A‑B‑A (0,958–0,978, dispersión 0,2–2,6 %; Fig. 12); transmitancia de la pieza de PTFE de 2 mm (0,148–0,197 entre FY y NIR).
- **Derivados:** `derivados/lab22_*.csv`. **Informe:** Sec. 9.5.
- **Nota:** la hora de los nombres de archivo no es la real (se ajustó a mano a 18:00, 19:00 y 20:00 en los reinicios del intercambio); el orden sí es correcto. La sesión real fue entre las 17:00 y las 18:20.

## 2026-10-26 (madrugada) — Casa: prueba del cenit armado
- Barrido de ganancia del cenit con el PTFE a 3 mm (lineal hasta 512×) y una lectura A+B de prueba. Exploratorio.

## 2026-10-26 — Campo, prado de la Universidad de los Andes
- **Montaje:** bastón; nadir a ~50 cm del suelo; cenit arriba con el PTFE a ~3 mm del chip (Fig. 13). Sin BMP280.
- **Sesión 1 (15:35–16:01, sol y nubes):** solo el nadir. NDVI crudo: pasto denso 0,85, ralo 0,63, adoquín 0,47–0,48. Barridos de saturación (ganancia segura 2× al sol, 8× sol bajo, 16× sombra).
- **Sesión 2 (16:55–17:38, nublado):** con el cenit. Validación con corrección (Tabla 11: NDVI 0,718 / 0,643 / 0,323 / 0,130); E4 con nubes (113 pares; CV del NIR crudo 25,6 % → cociente 1,1 %).
- **Derivados:** `derivados/campo26_*.csv`. **Informe:** Sec. 9.6.
- **Archivos con fecha 2026-04-15:** `saturacion_sensorB_..._133507`, `registro_..._completo_nublado_..._133610`, `registro_..._completo_sol_p1_..._134121` (reloj sin ajustar, ~16:55–17:05).

## 2026-10-28/29 — Pruebas con lámpara en casa (fuente DC controlada): PTFE, llenado, E1 y E4
- **Lugar:** casa de Andrés, con la halógena en fuente DC regulada (fuera del laboratorio). Luz estable: CV del NIR del cenit ≤ 0,05 % por corrida.
- **Montaje:** nadir en protoboard solo con el AS7343 (fallas del bus I2C; BMP280 retirado), ventana a 15 cm de la lámina; halógena a ~30 cm en horizontal y 35 cm de alto; cenit al lado (Fig. 17).
- **PTFE (dos intentos):** las láminas de 3 y 6 mm no son opacas (Tabla 12). **Llenado:** la lámina se bajó 5 y 10 cm; corregido por irradiancia, semiángulo equivalente entre 30° y 45° (Tabla 13).
- **Pasto, intento 1** (blanco = láminas apiladas): E1 con 50 lecturas (Tabla 14). Luego falló el cenit y se movió el montaje.
- **Pasto, intento 2** (blanco = solo la 15×30): E4 con 12, 11, 10, 9 y 12 V (Tabla 15, Fig. 19).
- **Derivados:** `derivados/lab28_*.csv`. **Informe:** Sec. 9.8.
- **Fechas de archivo:** hay tres relojes: correcto (22:25–23:00 y 23:52–00:02), 2026-04-15 (reinicios) y 2026-10-28 01:00–02:03 (ajustado a mano con un valor equivocado; la hora real es ~00:09–00:45 del 29). Los intentos se separaron con `z_seq` y el nivel del cenit.

## 2026-11-04 — Casa: BMP280 y primera prueba de la interfaz con los sensores reales
- **Montaje:** dispositivo completo en interiores. BMP280 reconectado con CSB a 3,3 V (modo I2C) y SDO a tierra (dirección 0x76), estable junto al AS7343 (0x39). LiDAR por USB: los errores de entrada y salida se debían al bajo voltaje de la fuente; con el power bank adecuado y la reapertura del puerto en el programa, midió.
- **Archivos:** dos registros `prueba_bus_bmp` (reloj sin ajustar, fecha de abril) y, en `interfaz/`, tres mediciones de prueba de la interfaz, que el operador marcó como no válidas por ser en interiores.
- **Informe:** Sec. 9.10.

## 2026-11-05 — Campo, zona verde de Uniandes: sol frente a nube, ganancia fija y saturación
- **Montaje:** bastón vertical sobre pasto denso y corto; nadir a unos 50 cm del pasto; cartón blanco de 35×50 cm sobre una caja, a 10 cm de la ventana (no a 15 cm como estaba planeado). Fotos en `fotos/` (montaje_1 a 4, superficie_1 a 4).
- **Bloques:** sol 1–5 (8:47–9:05, pasto con ganancia adaptativa G y fija a 0,5× Gf); nube 1–10 (W, G, Gf y Wf). Nube 1 y 7 con cielo mixto; nube 2 a 7 con sombrilla; nube 8 a 10 con nublado natural. Seis archivos con el número de bloque equivocado: la etiqueta real está en el índice (columna motivo) y en `derivados/campo_5nov_revision_por_archivo.csv`.
- **Saturación:** cenit a 0,5× al 52 % de la escala (8:33) y al 78 % (9:28); el nadir sobre el cartón saturó al sol aun a 0,5×.
- **Interfaz (`interfaz/`):** siete mediciones de 9:39 a 10:03 con nublado, el CSV descargado al celular y las fotos de la cámara (oscuras: cámara desalineada).
- **Resultados:** NDVI del mismo pasto 0,739 con sol y 0,743 con nublado; ganancia fija con sesgo de unas 0,003; la corrección redujo unas diez veces la variación de la luz; la sombrilla rompe la compensación.
- **Derivados:** `derivados/campo_5nov_*.csv` (con `analisis/campo5_porarchivo.py` y `analisis/campo5_bloques.py`). **Informe:** Sec. 9.11.

## 2026-11-06 — Casa, de noche: factores de ganancia de 2 a 256× y oscuridad
- **Montaje:** dispositivo completo con el bastón acostado sobre dos apoyos; halógena de 12 V y 20 W en fuente DC, en el eje de cada módulo, a la altura del chip del nadir o del PTFE del cenit. Cuarto oscuro.
- **Tramos (cuatro ganancias, ida y vuelta, 10 lecturas por bloque):** nadir T3 32–256× a 168 cm, T2 8–64× a 84 cm, T1 2–16× a 42 cm; cenit T3 32–256× a 52 cm, T2 8–64× a 26 cm. Oscuridad al final (0,5 y 16–512×).
- **Cenit:** el sensor B está descentrado bajo el PTFE; hubo que reapuntar. El primer T3 (19:35) se descartó porque la luz cayó a la mitad entre ida y vuelta; se usan el T3 de las 19:49 y el T2 de las 19:52. El T2 de las 19:46, con poca luz, queda como repetición (coincide dentro de 0,5 %).
- **Resultados:** la ganancia real se aparta de la nominal entre −3,9 y +1,3 % de 1 a 256×, con el mismo patrón en A y B; el factor de 8× de A repitió el de octubre (−3,2 frente a −3,1 %). Medidas de la cara inferior de la caja del nadir (fotos `foto_ventana_nadir*.jpg`): a = 5, b = 7,5, c = 2,5 y e = 6 cm desde el chip, más 15 cm de estructura triangular; profundidad del hueco 4–5 mm.
- **Otros:** la caja del nadir pasó de 21 a 34 °C en 45 minutos (calor propio); el BMP280 dejó de dar temperatura desde las 19:19.
- **Derivados:** `derivados/casa6_factores_ganancia.csv` (con `analisis/casa6_factores_ganancia.py`). **Informe:** Sec. 9.12.

## 2026-11-10 — Superficies cerca de la casa: E2 en sitio y prueba integral (primera parte)
- **Lugar y cielo:** zona verde cerca de la casa de Andrés, 15:11–15:40, sol con nubes que pasaban. Fotos de reconocimiento de las 11:36 en `fotos/superficies_reconocimiento_1136_*.jpg`.
- **Cambio de plan:** E2 pasó de la bandeja con pasto cortado a superficies reales medidas en sitio, con la interfaz, para cubrir a la vez la prueba integral.
- **Montaje:** bastón vertical con el chip a unos 55 cm del suelo. La referencia va sobre la caja, a 10 cm del chip, como el 5 de noviembre.
- **Referencia:** a las 15:07 el cartón blanco saturó el nadir al sol y la interfaz rechazó el blanco. Desde las 15:11 la referencia es una **cartulina gris mate** sobre el cartón. Las reflectancias de este día son, entonces, relativas a la gris. Falta el par blanco–gris para pasarlas a blanco.
- **Superficies:**
  - **V1:** pasto alto verde.
  - **V2:** pasto verde bajo.
  - **V3:** pasto con parche seco.
  - **T:** tierra. El parche mide unos 30–45 cm y con el chip a 55 cm el sensor vio el pasto de alrededor.
  - **A:** grava, piedras con una rejilla en el centro; no es andén.
  - **N:** cartulina negra sobre la gris.
  - Faltan V4 (seco) y el par blanco–gris.
- **Tomas:** 26 mediciones, de las que 17 son válidas: tres de cada superficie del suelo y dos de la negra. En T y en A el operador declaró válidas solo las tres últimas. Las demás se descartaron por nube (luz del cenit < 80 % de la del blanco), CV del cociente > 5 % o lecturas sin cenit. El motivo de cada una está en `derivados/sitio10_mediciones.csv`.
- **Fallas de la interfaz:**
  - `mediciones_20261110.csv` y `crudo_20261110.csv` se guardaron **sin línea de títulos**. Por eso la tabla de la interfaz mostró "undefined" y todas las filas quedaron con el número 11.
  - Las fotos de la cámara se sobrescribieron en `medicion_0011.jpg`. Solo queda la última, de la grava, que muestra que la cámara ya quedó alineada.
  - Los datos no se dañaron: los 128 pares crudos coinciden uno a uno con las 26 mediciones.
  - El análisis agrega los títulos en memoria; los crudos no se editan.
- **LiDAR:** al principio, al sol, no entregó datos. Sobre la caja dio lecturas de 20–34 m y después de 9–10 cm (al límite de su rango mínimo). Sobre el suelo, de 46 a 58 cm. El suelo de la sesión se escribió a mano: 58,8 cm.
- **Fotos de las huellas:** tomadas con el celular a las 16:50–17:30, tres por superficie, a la posición aproximada, con la cinta métrica en pulgadas como escala. Cada foto cubre unos 70 × 50 cm, menos que el círculo del sensor.
- **Resultados (tomas válidas):**

  | | V1 | V2 | V3 | T | A | N |
  |---|---|---|---|---|---|---|
  | NDVI | 0,828 | 0,594 | 0,423 | 0,393 | 0,212 | 0,030 |
  | NDRE₂ | 0,679 | 0,445 | 0,290 | 0,259 | 0,146 | −0,023 |
  | Fracción verde (Canopeo) | 98,6 % | 74,9 % | 47,6 % | 17,5 % | 9,5 % | — |

  El NDVI y el NDRE₂ ordenan las cinco superficies del suelo igual que la fracción verde (Spearman = 1); el NDRE₁ no (0,7). Las tomas de una misma superficie difieren en 0,006 de NDVI como máximo.
- **Derivados:** `derivados/sitio10_*.csv` (con `analisis/sitio10_e2.py`). **Informe:** Sec. 9.13.

## 2026-11-10/11 — Noche en casa: respuesta angular del cenit, fuga de F6, E3 y factor de 0,5× (última sesión con la fuente DC)
- **Horario:** 22:33–01:27. Halógena de 12 V a 12,0 V, encendida desde unos 15 min antes de la respuesta angular.
- **Oscuridad a 1024×:** lámpara y luz del cuarto apagadas, tela negra doblada. Canal más alto: nadir 26,5 cuentas (F4), cenit 15,8. El NIR quedó en 1,6 y 1,0 cuentas.
- **Respuesta angular del cenit (sensor B, 512×):**
  - Montaje: bastón acostado y quieto; lámpara a 100 cm del PTFE en 0°, ±30° y ±60°, en el orden 0 → +30 → +60 → 0 → −30 → −60 → 0.
  - El plano 2 se hizo girando la caja del cenit ¼ de vuelta sobre su tubo; el bastón no se movió.
  - Las tres lecturas de 0° difieren hasta un 10 % (plano 1) y un 6 % (plano 2). Esa es la precisión de volver a poner la lámpara a mano.
  - La respuesta es asimétrica, con el lado + más alto en los dos planos. La explica una desalineación de 10–17° entre la línea de las marcas y la normal del PTFE. Como aparece igual con la caja girada, se atribuye al montaje.
  - Promediando + y −, lo que cancela la desalineación: a 30°, entre −3 y +7 % frente al coseno; a 60°, entre +20 y +25 %.
  - El cociente NIR/F6 cambia entre −4,7 y +3,6 %, y el F8/F7 entre −1,7 y +1,5 %: la forma espectral casi no cambia con el ángulo.
- **Fuga de F6:** lámpara en +60° del plano 2. Con aluminio en los lados de la cápsula, todos los canales cambian menos de 0,5 % frente al promedio sin aluminio, y F6 no se separa de los vecinos (F6/FXL: 1,614, 1,613 y 1,614). La segunda toma sin aluminio quedó 4 % más baja en todos los canales: algo se movió al quitarlo. Sin fuga detectable.
- **E3 (nadir A, 64×, lámpara a 84 cm en el eje de la ventana; bastón girado ¼ con la caja apoyada en libros):**
  - BMP280 reconectado esa noche (CSB y SDO); registró la temperatura en todas las lecturas.
  - Tres corridas seguidas por cortes de la conexión: 01:03:19, 01:06:04 y 01:08:08 (1 s entre una y otra), 2184 lecturas en 22 min.
  - La bolsa de agua tibia se puso en el minuto 3,1 (durante la corrida 2) y se quitó en la lectura 730 de la corrida 3 (minuto 12,2).
  - La temperatura subió de forma pareja de 25,2 a 28,6 °C durante toda la corrida. Casi todo es calor propio de la caja; la bolsa casi no la cambió.
  - Al poner la bolsa, la señal bajó de golpe entre 0,5 y 1,2 %; al quitarla volvió entre 0,55 y 0,97 %. Son escalones mecánicos (peso sobre la caja), no térmicos.
  - Dentro de cada tramo sin movimiento, la pendiente conjunta con la temperatura es de +0,03 (F6), 0,00 (F7), −0,03 (F8) y −0,02 (NIR) %/°C.
- **Factor de 0,5× del nadir:** dos corridas (00:53 a 24,2 °C y 01:27 a 28,7 °C), lámpara a unos 20 cm.
  - Referido a 4×: NIR +0,03 y +0,04 %; F7 −0,13 y +0,17 %; F6 −0,8 y −0,2 % y F8 −0,8 y +0,1 %, con solo 45–73 cuentas, donde 1 cuenta pesa hasta 2 %.
  - 1× y 2× repiten los de octubre: NIR −0,19 a −0,27 % y −0,13 %.
- **Derivados:** `derivados/noche10_*.csv` (con `analisis/noche10_analisis.py`). **Informe:** Sec. 9.14.

## 2026-11-11 — Tarde cerca de la casa: par blanco–gris, V4, T y V1 de control; autosombra, campo de visión, 0,5× del cenit y atenuador
- **Lugar y cielo:** la misma zona verde del 10 de noviembre.
  - Interfaz de 13:36 a 13:56, con nubes que se abrían. La luz del cenit subió hasta 86 % durante el par.
  - `caracterizacion_espectro.py` de 16:44 a 17:08, con el sol bajo y nubes.
- **Cenit:** el contador de paquetes muestra que el ESP32 arrancó de nuevo cinco veces: hacia las 13:20, 13:32, 15:40, 16:27 y 16:41. Por eso se descartan los intentos de autosombra de las 15:35 (sin cenit), las 15:42 (paquetes perdidos) y las 16:28 (4 lecturas). Quedan en `crudos/descartados/`.
- **LiDAR:** no se detectó en la mañana. En la tarde midió sobre el suelo (47–55 cm).
  - La distancia al suelo fue la del 10 de noviembre (58,8 cm, escrita a mano). El operador confirmó el 13 de noviembre que el bastón no cambió de largo, así que esa distancia vale para la sesión, y las alturas y la biomasa se toman como válidas.
  - Lo confirma el V1: 47,5 cm de LiDAR los dos días.
  - Alturas: V1 11,3 cm, V4 4,1–5,1 cm y T 6,2–7,2 cm.
  - Biomasa: V1 2660–2767, V4 375–574 y T 895–1064 kg MS/ha.
  - Sobre la grava (10 nov) y la tierra la altura aparente es de 3–7 cm: un desfase de unos 4 cm o la rugosidad del suelo.
  - Datos de las dos sesiones: `derivados/tarde11_alturas.csv`.
- **Interfaz (`interfaz/`):**
  - Mediciones: 20 en la tarde (ids 13–32), con títulos y sin números repetidos. Los 95 pares coinciden con las mediciones. Los cinco blancos quedaron registrados en `blancos_20261111.csv`.
  - Toma repetida: la 17 (N, toma 2) no tuvo pares porque el cenit no envió datos, y se repitió como la 18.
  - Fotos: cada una con nombre propio (`fotos/`). La de la medición 32 (V1, toma 3) quedó vacía, con 0 bytes; lo más probable es que la Raspberry se apagara sin `shutdown` antes de escribirla. La fila de datos sí quedó, y la foto se recuperó de la captura de pantalla de la interfaz (`medicion_0032_recuperada_captura.png`, 95,6 % verde, igual que las tomas 1 y 2).
- **Par blanco–gris:** blanco con el cartón solo (13:36:21); luego Gr, N y B2, tres tomas cada una, y C final.
  - C final leyó 1,06, porque el cociente sobre el cartón cambió 6 % con la luz. Se corrige linealmente en el tiempo; la corrección no cambia la forma espectral.
  - Gris frente a cartón: 0,423 (F6), 0,431 (F7), 0,439 (F8) y 0,447 (NIR), casi plana.
  - Negra: 0,062–0,068.
  - Pliego blanco: 1,06 (F6) a 1,01 (NIR) y 1,42 a 425 nm (blanqueadores ópticos).
- **Superficies con la referencia gris (blancos de las 13:47, 13:51 y 13:55):**

  | | V4 pasto seco | T tierra (parche mayor) | V1 control |
  |---|---|---|---|
  | NDVI (gris) | 0,285 | 0,281 | 0,829 (10 nov: 0,828) |
  | NDRE₂ (gris) | 0,161 | 0,109 | 0,686 (10 nov: 0,679) |
  | NDVI (cartón) | 0,310 | 0,306 | 0,837 |
  | Verde, foto de la cámara | 7,6 % | 0,6 % | 95,8 % |

  - Pasar de la referencia gris al cartón sube el NDVI entre 0,008 y 0,026 sin cambiar el orden de las superficies.
  - En la tierra del parche mayor el NDVI baja 0,11 frente al parche pequeño del 10 de noviembre.
  - El NDVI no separa el pasto seco de la tierra; el NDRE₂ sí.
- **Autosombra (16:48–16:53):**
  - Montaje: cartón a 10 y 15 cm, alternado tres veces.
  - El cociente varió hasta 17 % en 4 minutos. Con una tendencia cuadrática en el tiempo, el cartón a 15 cm lee entre 8,8 % (F6) y 10,4 % (F8) más que a 10 cm (error estándar de 1 %). Las comparaciones con las tomas vecinas dan entre 3 y 16 %.
  - El efecto es casi igual en todas las bandas: menos de 0,006 de NDVI.
- **Campo de visión (16:55–17:05):**
  - Montaje: discos blancos de 6, 10, 14, 18, 22 y 32 cm de diámetro sobre tela negra (los archivos de los dos mayores quedaron rotulados d24 y d30, el diámetro propuesto; el real es 22 y 32 cm), a 12 cm de la ventana del nadir (medido por el operador), no a los 10 cm habituales.
  - Repeticiones: los discos de 10 y 14 cm se repitieron enseguida y se promedian. El primer pliego blanco (6 lecturas, con la ganancia cambiando) se descartó.
  - Respuesta: coseno recortada en 35° (33,6–36,7° según la repetición; 33,8° si se cuentan los 4–5 mm que el chip está hundido detrás de la ventana). El 50 % de la señal viene de dentro de 24° y el 90 % de dentro de 33°.
  - Con el chip a 55 cm, el 50 % de la señal viene de un círculo de unos 49 cm y el 90 % de uno de unos 71 cm.
- **Factor de 0,5× del cenit (17:06):**
  - Hubo poca luz: 17,7 % de la escala a 4× y 56 cuentas de NIR a 0,5×. La luz subió y bajó 2 %.
  - Factores referidos a 4×: entre −1,0 y −1,6 % (regresión, ±2 %) y entre −2,3 y −3,3 % (ida y vuelta).
  - A 1× y 2× el mismo barrido se aparta 0,1–2,2 % de los factores del 6 de noviembre.
  - Se toma entre −1 y −3 %, con incertidumbre de unos 2 %.
- **Atenuador (16:44–16:47):**
  - La corrida rotulada `mediodia_sin` de las 16:44:05 se hizo con la lámina puesta. Coincide con la de `con` dentro de 3 % y se usa como segunda medición con atenuador.
  - Las dos corridas sin lámina coinciden dentro de 1,2 %.
  - Transmitancia a 0,5×: 0,54–0,59 en una corrida y 0,55–0,61 en la otra (FY a NIR). El % de la escala baja en un factor de 0,56–0,63.
  - No fue al mediodía. Con la estimación de 77–93 % para el mediodía, la lámina dejaría el cenit en 43–59 %.
- **Derivados:** `derivados/tarde11_*.csv`, generados con `analisis/tarde11_analisis.py`.
  - `tarde11_interfaz.csv`: las 20 mediciones con los 12 canales.
  - `tarde11_par.csv`: el par de referencia.
  - `tarde11_superficies.csv`: las superficies del 10 y el 11.
  - `tarde11_autosombra.csv`: la autosombra.
  - `tarde11_fov.csv` y `tarde11_fov_corridas.csv`: el campo de visión.
  - `tarde11_factor05_cenit.csv`: el factor de 0,5× del cenit.
  - `tarde11_atenuador.csv`: el atenuador.
- **Informe:** Sec. 9.15.

## 2026-11-13 — Cenit con sol directo, con y sin atenuador (ventana)
- **Montaje:** cenit apoyado por fuera de la ventana de un piso alto, horizontal y sin vidrio de por medio. Edificios alrededor tapaban parte del cielo; había cúmulos (`fotos/`).
- **Válidas** (según el operador, con el sol despejado):
  - `ventana13_sin` de las 12:54:35;
  - `ventana13_con` de las 12:55:03;
  - `ventana13_sin2` de las 12:55:28.
- **Descartadas, con nubes** (`crudos/descartados/`):
  - tres corridas sin lámina, de las 12:49 a las 12:51 (81–82 % de la escala);
  - una con lámina, de las 12:51 (45,7 %);
  - una sin lámina, de las 12:54:18 (22,8 %, con una nube encima).
- **Resultados a 0,5×** (ganancia mínima):
  - sin lámina: 88,0 y 86,3 % de la escala, con el VIS en 91,4 y 89,6 %;
  - con lámina: 46,8 %;
  - a 1× saturaron todas las lecturas;
  - CV del NIR: 0,12–0,18 %;
  - la segunda corrida sin lámina quedó 2,0 % por debajo de la primera.
- **Transmitancia** (con / promedio de las dos sin): FY 0,52, F6 0,539, F7 0,547, F8 0,559 y NIR 0,573. El % de la escala baja en un factor de 0,536.
- **Proyección al mediodía solar** (11:40):
  - Elevación del sol: 60,8° a las 12:55 y 67,4° al mediodía, un factor de 1,058 sobre un plano horizontal.
  - Sin atenuador: 92 %, y 99 % si se suma el ~7 % de cielo que tapaban los edificios.
  - Con atenuador: 49–53 %.
- **Decisión:** el atenuador queda fijo, según la regla del plan (≥ 90 %: necesario; con él < 60 %: se deja puesto).
- **Derivados:** `derivados/mediodia13_atenuador.csv`, generado con `analisis/mediodia13_analisis.py`.
- **Informe:** Sec. 9.15, tabla tab:mediodia13.
