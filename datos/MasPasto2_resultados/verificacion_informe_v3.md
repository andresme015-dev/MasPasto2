# Verificación del informe de avance v3 (corte 29 oct 2026)

Revisión hecha el 29 de octubre de 2026. Cada cifra de resultados se recalculó desde los CSV crudos de esta carpeta (scripts en `analisis/`); las del LiDAR, desde `lidar_caracterizacion.csv` (6 oct), y las del modelo, desde `train.csv` (CSIRO/Kaggle).

**Resultado:** las cifras del informe coinciden con los datos. Se encontraron y corrigieron cuatro imprecisiones de redacción y se agregaron cinco ajustes de coherencia con la propuesta (al final).

## 1. Laboratorio, 21 y 22 de octubre (Sec. 9.5)

| Afirmación del informe | Recalculado | Resultado |
|---|---|---|
| Estabilidad: 150 pares en 7,1 min; CV del NIR 0,04 % (A), 0,05 % (B), 0,03 % (cociente) | 150 pares, 7,07 min; 0,042 / 0,051 / 0,029 % | Coincide |
| Deriva del NIR ≤ 0,11 %; cociente FY–NIR: CV ≤ 0,12 %, deriva ≤ 0,23 % | −0,055 / −0,107 / −0,052 %; CV máx. 0,122 %; deriva máx. 0,230 % | Coincide |
| Corrida antes de realinear: B/A derivó 2,3–4,2 %, valía 1,39 en el NIR; después 1,04 | 2,30–4,19 %; 1,389; 1,040 | Coincide |
| Oscuridad: 0 cuentas en A y B a 1, 2, 4, 8 y 16× | Máximo 0 en los 12 canales | Coincide |
| VIS saturado, 32→64×: exceso de 850–1400 cuentas; F1 +35 %, F6 +10 %, NIR +5 %; ida/vuelta 1,4 % | 889–1405; +35,0 / +10,2 / +4,8 %; 1,39 % | Coincide |
| Factores (ref. 4×): A 1× −0,4, 2× −0,25, 8× −3,1 %; B −0,7, −0,5, −3,2 %; rango 8× −2,1 a −3,8 % | A −0,43 / −0,25 / −3,07; B −0,69 / −0,48 / −3,18; rango −2,13 a −3,77 % | Coincide |
| 8× de A el 21 oct: −2,7 % | −2,72 % | Coincide |
| k sin difusor NIR 1,042 / 1,042 / 1,044 / 1,039 | 1,0417 / 1,0419 / 1,0442 / 1,0394 | Coincide |
| k con difusor 0,958–0,978; dispersión 0,2–2,6 %; efecto del sitio hasta 21 % en F6 | 0,958–0,978; 0,2–2,6 %; p(F6) = 1,21 | Coincide |
| T_d pieza: 0,148–0,198 (FY–NIR); F6 0,167, F7 0,181, F8 0,179, NIR 0,198; CV 0,8–2,7 % | 0,148–0,197/0,198 (según se promedie); CV 0,8–2,7 % | Coincide |
| T_d cápsula 0,094–0,138 | 0,094–0,138 | Coincide |

## 2. Campo, 26 de octubre (Sec. 9.6)

| Afirmación | Recalculado | Resultado |
|---|---|---|
| 24 corridas sin lecturas saturadas | 24 corridas de registro (incluidas las 2 de arranque y la E4 descartada), 0 saturadas | Coincide |
| Ganancias del nadir 2–16× al sol, 16× adoquín, 32× ralo, 64× al anochecer; cenit 16–32× y 64× | Coinciden archivo por archivo | Coincide |
| F6 del nadir con 14–30 cuentas en E4 | 14–30 | Coincide |
| Barrido a la sombra 2,5 / 5,0 / 10,1 / 20,5 / 40,5 / 82,8 % | Medias del resumen; los máximos (20,6 / 40,8 / 83,5 %) son los que cita el registro de decisiones | Coincide |
| Ganancia segura 2× al sol con 75,7 %; 8×, 16×; cenit 16× y 64× | Coincide | Coincide |
| Razón sol/nublado ~20 y cenit ~41 % a 0,5× | 14,6/0,723 = 20,2; 2,0 % × 20,2 = 40 % | Coincide |
| NDVI crudo 0,85 > 0,63 > 0,48 | 0,842–0,847 / 0,633 / 0,471–0,481 | Coincide |
| Tabla 11: NDVI 0,718 / 0,643 / 0,323 / 0,130; NDRE₂ 0,531 / 0,477 / 0,216 / 0,008; 26–29 de 30 pares | Coincide | Coincide |
| Blancos: 7 % en el visible y 1 % en el NIR | 7,3–7,5 % y 1,2 % | Coincide |
| E4: 113/120 pares; CV 25,6 / 26,6 %; cociente 1,1 % (F7 1,1, F8 1,0, F6 6,6 %); NDRE₂ 0,506 (CV 0,8 %); NDVI 0,72 → 0,76 (CV 2,2 %) | Coincide | Coincide |

## 3. Pruebas con lámpara, 28 y 29 de octubre (Sec. 9.8)

| Afirmación | Recalculado | Resultado |
|---|---|---|
| Tabla 12 (efectos del PTFE) | `derivados/lab28_ptfe_efectos_pct.csv` | Coincide |
| "Las cuentas del nadir de los dos intentos difirieron entre −1,8 y +0,1 %, y el cociente entre 0,2 y 3 % en casi todos los canales" | Eso vale solo para el NIR; en todos los canales: −3,3 a +2,6 % y cociente 1,5 % en mediana (máx. 7,9 %) | **Corregido** |
| "Las diferencias de la tabla, de 9 a 43 %" | La fila de grosor sobre fondo blanco es de 1 a 3,5 %; el resto, de 6 a 43 % | **Corregido** |
| Tabla 13 (llenado medido y corregido) | `derivados/lab28_llenado.csv` | Coincide |
| Modelo de cono: 1,05 / 1,19 / 1,34 / 1,48 y 0,82 / 0,79 / 0,76 / 0,70 | Coincide | Coincide |
| Tabla 14 (E1) | `derivados/lab28_E1.csv` | Coincide |
| Tabla 15 y Fig. 19 (E4) | `derivados/lab28_E4.csv` | Coincide |
| "Pasto recién cortado" | Se cortó en la tarde (fotos de las 16:54) y se midió hacia las 00:09–00:45 | **Corregido** ("cortado esa misma tarde") |
| "Se hicieron en laboratorio" | Andrés confirmó que fueron en su casa, con fuente controlada | **Corregido**: el informe dice dónde fueron y justifica que la luz fue tan estable como en el laboratorio (CV del cenit ≤ 0,05 % por corrida) |

## 4. LiDAR, 6 de octubre (Sec. 9.4)

| Afirmación | Recalculado | Resultado |
|---|---|---|
| Ajuste 0,9732 d + 0,77 (R² 0,99982); inversa 1,0275 d − 0,80 | Coincide | Coincide |
| Pendientes por corrida 0,9752 / 0,9707 / 0,9738; desfases 0,48 / 0,97 / 0,87 | Coincide | Coincide |
| Sin calibrar: RMSE 1,87, máx. 3,0, sesgo −1,43 cm; calibrado: RMSE 0,55, máx. 1,40 | Coincide | Coincide |
| Validación cruzada: RMSE 0,54–0,60, máx. 1,06–1,54 | Coincide | Coincide |
| Precisión, repetibilidad, histéresis, zona cercana, 100,6 Hz, 47–49 °C, confianza 100 | Coincide | Coincide |
| "Intensidad de 586 a 414" | Son las lecturas extremas; las medias por punto van de 575 a 431 y no bajan en todos los pasos | **Precisado** |

## 5. Modelo (Sec. 9.9)

| Afirmación | Recalculado (GDM, × 47,619) | Resultado |
|---|---|---|
| CV sin barajar R² 0,572 ± 0,051 | 0,570 ± 0,051 | Coincide |
| Prueba 25 % (90 muestras, semilla 42): R² 0,283, RMSE 891, MAE 565 | 0,284 / 891 / 565 | Coincide |
| CV barajada ×10: R² 0,48 ± 0,17, RMSE 816, MAE 537 | 0,49 ± 0,17, 808, 528 (cambia con la semilla del bosque) | Coincide dentro de la variación por semilla |
| Importancia de NDVI×altura 64 %; R² de entrenamiento 0,91 | 0,64; 0,92 | Coincide |
| Altura máxima 70 cm; 90 % ≤ 16 cm | 70; p90 = 16 | Coincide |
| CV por sitio y fecha R² 0,24 ± 0,28 | Depende de cómo se repartan los grupos: 0,13 a 0,36 en tres repartos | **Precisado** en el texto |
| 4405,1 kg MS/ha en la Raspberry | Depende del modelo guardado en el cuaderno (no se reentrena aquí) | No verificable sin el archivo del modelo |

## 6. Coherencia con la propuesta y ajustes hechos

| Punto | Estado | Cambio en el informe |
|---|---|---|
| E1: 50 lecturas, superficie fija, CV < 5 % | Cumple con lámpara (pasto, 15 cm) | — |
| E3: temperatura registrada en E1 y E4 | **No se hizo** (BMP280 retirado) | Declarado como pendiente en tablas y cronograma |
| E4: prueba de concepto con lámpara y sol, más la respuesta angular | Lámpara y campo hechos; **falta la respuesta angular** | Declarado como pendiente |
| E2: 8 superficies | Pendiente | La distancia de la bandeja se ajustó al campo de visión medido: 15 cm (antes "17 cm o menos" con 40°) |
| Ec. (8), huella con 40° | La prueba de llenado da 30–45° | Agregado el intervalo y la altura máxima con 45° (35 cm para 70 cm) |
| Supuesto de igual irradiancia en los dos módulos | La prueba de llenado mostró que con lámpara cercana no se cumple entre puntos de la mesa | Agregado en "Supuestos y límites" |
| E2 con pasto recién cortado | El pasto cortado horas antes derivó −0,16 %/min en el NIR | Agregado como respaldo de esa condición |
| OE2 "en condiciones de laboratorio de electrónica" | Las pruebas del 28–29 se hicieron en casa, con la misma lámpara y fuente DC | Agregado el párrafo "Lugar de las pruebas" (Sec. 9.8) y la nota en la tabla de ajustes; la respuesta angular se hará en el laboratorio |
| Especificación E1 (Tabla 5) | Cumple | Actualizada |
| Hito H4 (S13) | Faltan E2, E3, respuesta angular y campo de visión | Estado actualizado |
