"""Clasifica los CSV crudos de MasPasto2 por sesión y prueba, arma la carpeta de resultados
y escribe indice_corridas.csv. Uso: python3 -I construir_indice.py <pool> <carpeta_resultados>"""
import sys, os, re, shutil, json, glob
import pandas as pd
POOL, OUT = sys.argv[1], sys.argv[2]
SES = {
 "S1": ("2026-10-21_lab_estabilidad_ganancias", "2026-10-21", "Laboratorio. Sensor A solo (madrugada y mañana) y primera sesión A+B (tarde, 16:31-17:14)."),
 "S2": ("2026-10-22_lab_caja_oscura", "2026-10-22", "Laboratorio. Caja de cartón como recinto oscuro, halógena 12 V/20 W fija a 34 cm, fuente DC."),
 "S3": ("2026-10-26_casa_prueba_cenit", "2026-10-26", "Casa, ~01:26. Prueba del cenit armado con el PTFE a 3 mm (barrido de ganancia) y lectura de prueba A+B."),
 "S4": ("2026-10-26_campo_uniandes", "2026-10-26", "Campo, prado frente al edificio (Uniandes), 15:35-17:38. Bastón: nadir a ~50 cm, cenit arriba."),
 "S5": ("2026-10-28_lab_PTFE_E1_E4", "2026-10-28/29", "Laboratorio, noche del 28 al 29. Nadir a 15 cm, halógena a ~30 cm en horizontal y 35 cm de alto, cenit al lado."),
 "S6": ("2026-11-04_casa_sensores_reales", "2026-11-04", "Casa. Reconexión del BMP280 (CSB a 3,3 V, SDO a tierra) y primera prueba de la interfaz con los sensores reales."),
 "S7": ("2026-11-05_campo_sol_nube", "2026-11-05", "Campo, zona verde de Uniandes, 7:49-10:03. Bloques de sol y de nube, ganancia fija 0,5x, saturación al sol e interfaz."),
 "S8": ("2026-11-06_casa_ganancias_2a256", "2026-11-06", "Casa, de noche, halógena 12 V/20 W en fuente DC. Bastón acostado; factores de ganancia de 2 a 256x de A y B y oscuridad hasta 512x."),
 "S9": ("2026-11-10_sitio_E2_superficies", "2026-11-10", "Superficies cerca de la casa de Andrés, 15:11-15:40, sol con nubes. E2 en sitio con la interfaz y referencia de cartulina gris (los archivos de la interfaz se agregan a mano al índice)."),
 "S11": ("2026-11-11_tarde_par_superficies_E_F", "2026-11-11", "Zona verde cerca de la casa. Interfaz 13:36-13:56 (par blanco-gris, V4, T y V1 de control; nubes que se abrían). caracterizacion_espectro.py 16:44-17:08, sol bajo y nubes (atenuador, autosombra, campo de visión y 0,5x del cenit). El cenit se reinició cinco veces en la tarde (los archivos de la interfaz se agregan a mano al índice)."),
 "S10": ("2026-11-10_noche_angular_E3_05x", "2026-11-10", "Casa, noche del 10 al 11 nov (22:33-01:27), halógena 12 V con fuente DC. Oscuridad a 1024x, respuesta angular del cenit en dos planos (caja girada sobre su tubo), fuga de F6, E3 con bolsa de agua tibia y BMP280 reconectado, y factor de 0,5x del nadir."),
}
# (regex sobre el nombre, sesión, prueba, estado, motivo, uso en el informe v3)
R = [
 (r"registro_sensorB_prueba_cenit_20261111", "S11","Prueba del cenit tras la caída de la mañana (3 lecturas)","auxiliar","Comprobación",""),
 (r"registro_sensorA_autosombra_10cm_1_20261111_1535", "S11","Autosombra, primer intento sin cenit","descartado","Sin cenit: el ESP32 no enviaba datos",""),
 (r"registro_sensorA-B_autosombra_10cm_1_20261111_1542", "S11","Autosombra, segundo intento","descartado","El cenit envió 6 de 10 lecturas y cambió de ganancia (reinicio a las 15:40)",""),
 (r"registro_sensorA-B_autosombra_10cm_1_20261111_1628", "S11","Autosombra, tercer intento","descartado","Solo 4 lecturas; el cenit volvió a caerse",""),
 (r"registro_sensorA-B_autosombra_1[05]cm_[123]_20261111_16[45]", "S11","Autosombra: cartón a 10 y 15 cm, alternado tres veces","válido","Sol bajo y nubes: tendencia en el tiempo incluida en el ajuste","9.15"),
 (r"saturacion_sensorB_mediodia_sin_20261111_164405", "S11","Atenuador: rotulada sin lámina, hecha con la lámina puesta (operador)","válido con reservas","Etiqueta equivocada; se usa como segunda medición con atenuador","9.15"),
 (r"saturacion_sensorB_mediodia_(sin_20261111_164500|con_|sin2_)", "S11","Atenuador: sin, con y sin otra vez (16:45-16:47, poca luz)","válido","No fue al mediodía: da la transmitancia, no el % de la escala al mediodía","9.15"),
 (r"registro_sensorA-B_fov_blanco_20261111_170323", "S11","Campo de visión: pliego blanco, primer intento","descartado","6 lecturas con la ganancia cambiando; repetida enseguida",""),
 (r"registro_sensorA-B_fov_d1[04]_20261111", "S11","Campo de visión: discos de 10 y 14 cm (cada uno repetido)","válido","Repetida enseguida por el operador; se promedian las dos (difieren 0,08 y 0,12)","9.15"),
 (r"registro_sensorA-B_fov_", "S11","Campo de visión: discos blancos de 6 a 30 cm sobre tela negra, lámina a 12 cm de la ventana","válido","","9.15"),
 (r"registro_sensorB_ajuste_cenit_T0_20261111", "S11","Ajuste a 4x para el factor de 0,5x del cenit","auxiliar","Ajuste",""),
 (r"ganancias_sensorB_cenit_T0_cielo_20261111", "S11","Factor de 0,5x del cenit con el cielo del atardecer","válido con reservas","Poca luz (17,7 % de la escala a 4x; NIR 56 cuentas a 0,5x) y luz que varió 2 %; incertidumbre de unos 2 %","9.15"),
 (r"^registro_estabilidad_20260415_133605", "S1","Estabilidad de la lámpara (30 lecturas, 18 s), incandescente, madrugada","exploratorio","Muy corta para evaluar estabilización (registro de decisiones §4)",""),
 (r"^ganancias_nadir_20260415_133651", "S1","Ganancias 8, 16 y 32x con incandescente (hipótesis del VIS)","exploratorio","Hipótesis refutada después (registro §2a)",""),
 (r"^registro_estabilidad_20261021_09565", "S1","Estabilidad preliminar a 64x","exploratorio","Corrida de ajuste antes de la de 300 lecturas",""),
 (r"^registro_estabilidad_20261021_095839", "S1","Estabilidad preliminar 16-64x","exploratorio","Corrida de ajuste antes de la de 300 lecturas",""),
 (r"^registro_estabilidad_20261021_100111", "S1","Estabilidad de la lámpara, 300 lecturas a 64x (halógena DC, luces LED encendidas)","válido","","Registro §4"),
 (r"^ganancias_nadir_20261021_104619", "S1","Ganancias 32, 64 y 128x ida y vuelta: VIS saturado contamina los canales","válido","","Sec. 9.5 (criterio de saturación)"),
 (r"^ganancias_nadir_20260415_133924", "S1","Ganancias 2, 4 y 8x ida y vuelta, luces apagadas (~15:15)","válido","","Registro §3a; Tabla fG (comparación 8x)"),
 (r"^oscuridad_nadir", "S1","Oscuridad del sensor A sin nombre de sensor (2-8x válidos; 16-128x tomados con luz)","válido con reservas","Solo 2-8x son oscuridad real; ningún programa lo usa desde que se nombra el sensor (oscuridad_A.json)","Sec. 9.5 (oscuridad)"),
 (r"^oscuridad_(A|B)$", "S8","Oscuridad acumulada de A y B (1-16x del 21 oct; 0,5 y 16-512x del 6 nov), la que usan medir.py y el análisis","válido","","Sec. 9.5 y 9.12 (oscuridad)"),
 (r"^oscuridad_sensorA-B_20261021_163102", "S1","Oscuridad A y B, 1-16x","válido","","Sec. 9.5 (oscuridad)"),
 (r"^registro_sensorA-B_estabilidad_20261021_163733", "S1","Estabilidad A+B, 150 pares a 8x, lámpara sostenida a mano","válido","","Registro §9b"),
 (r"^intercomparacion_sensorA-B_prueba1_20261021_164441", "S1","Factor k con intercambio (lámpara a mano)","descartado","La lámpara se movió en el intercambio (registro §9c)",""),
 (r"^ganancias_sensorA-B_20261021_165038", "S1","Ganancias 1-8x de A y B a la vez","válido con reservas","Movimiento de la lámpara no lineal (registro §9d)",""),
 (r"^ptfe_sensorA-B_capsula_ptfe_20261021_171430", "S1","Transmitancia de la cápsula con techo de PTFE a 2-3 cm","válido con reservas","Lámpara a mano; montaje reemplazado","Sec. 9.5 (T_d de la cápsula)"),
 (r"^registro_sensorA-B_estabilidad_20261022_160316", "S2","Estabilidad A+B antes de realinear","descartado","Deriva no común a los dos sensores (registro §10b)",""),
 (r"^registro_sensorA-B_estabilidad_20261022_162025", "S2","Estabilidad A+B, 150 pares a 8x, lámpara fija","válido","","Sec. 9.5 (estabilidad)"),
 (r"^ganancias_sensorA-B_fija_20261022_162930", "S2","Ganancias A+B (arranque interrumpido)","descartado","Archivo vacío",""),
 (r"^ganancias_sensorA-B_fija_20261022_163012", "S2","Factores de ganancia A y B, 1-8x ida y vuelta","válido","","Tabla fG"),
 (r"^intercomparacion_sensorA-B_difusor_20261022_(163938|180021|200011)", "S2","Factor k con difusor común, posición original (1, 3, 5)","válido","","Fig. lab_k"),
 (r"^intercomparacion_sensorA-B_difusor_20261022_(170015|190012)", "S2","Factor k con difusor común, posición intercambiada (2, 4)","válido","","Fig. lab_k"),
 (r"^ptfe_sensorA-B_pieza_ptfe_pieza_20261022_200408", "S2","Transmitancia de la pieza de PTFE de 2 mm sobre B","válido","","Sec. 9.5 (transmitancia)"),
 (r"^registro_sensorA-B_casa_20261026_012619", "S3","Lectura de prueba A+B en casa","exploratorio","Prueba de funcionamiento",""),
 (r"^saturacion_sensorB_prueba_casa_20261026_012713", "S3","Barrido de ganancia del cenit en casa (hasta 512x)","exploratorio","Muestra la linealidad de la ganancia","Registro §12b"),
 (r"^registro_sensorA_inicio_20261026", "S4","Lectura de arranque del nadir","auxiliar","Comprobación de arranque",""),
 (r"^registro_sensorA-B_inicio_20261026", "S4","Lectura de arranque A+B","auxiliar","Comprobación de arranque",""),
 (r"^registro_sensorA_operacion_campo_sol", "S4","Nadir solo sobre pasto al sol (sesión 1)","válido","","Sec. 9.6 (ganancia adaptativa)"),
 (r"^saturacion_sensorA_operacion_sat_pasto_sol_1545_20261026_155032", "S4","Barrido de saturación del nadir al sol, con nube pasando","válido con reservas","La luz cambió durante el barrido","Registro §12c"),
 (r"^saturacion_sensorA_operacion_sat_pasto_sol_1545_20261026_155332", "S4","Barrido de saturación del nadir sobre pasto al sol (15:53)","válido","","Fig. campo_saturacion"),
 (r"^saturacion_sensorA_operacion_sat_pasto_sombra_20261026_155150", "S4","Barrido de saturación del nadir a la sombra (15:51)","válido","","Registro §12c"),
 (r"^saturacion_sensorA_operacion_sat_pasto_sombra_20261026_155424", "S4","Barrido de saturación del nadir a la sombra (15:54)","válido","","Fig. campo_saturacion"),
 (r"^saturacion_sensorA_operacion_sat_pasto_1700", "S4","Barrido de saturación del nadir, sol bajo (tomado a las 16:01)","válido","","Fig. campo_saturacion"),
 (r"^registro_sensorA_validacion_val_", "S4","Validación sin corrección, solo nadir (sesión 1)","válido","","Sec. 9.6 (NDVI crudo)"),
 (r"^saturacion_sensorB_cenit_3mm_zen_nublado_20260415_133507", "S4","Barrido del cenit, nublado (~16:55; reloj sin ajustar)","válido con reservas","La luz cambió durante el barrido","Fig. campo_saturacion"),
 (r"^saturacion_sensorB_cenit_3mm_zen_nublado_20261026_171133", "S4","Barrido del cenit, nublado al anochecer (17:11)","válido con reservas","La luz cambió durante el barrido","Fig. campo_saturacion"),
 (r"^registro_sensorA-B_operacion_completo_nublado_20260415_133610", "S4","Medición completa A+B, nublado (~17:00; reloj sin ajustar)","válido","","Sec. 9.6 (ganancia adaptativa)"),
 (r"^registro_sensorA-B_operacion_completo_sol_p1_20260415_134121", "S4","Medición completa A+B (reloj sin ajustar)","válido","12 de 30 pares descartados por cambio de ganancia","Sec. 9.6 (ganancia adaptativa)"),
 (r"^ptfe_sensorA-B_capsula_ptfe_capsula_fija_20260415_133713", "S4","T_d de la cápsula (interrumpida)","descartado","Interrumpida, sin datos útiles",""),
 (r"^registro_sensorA-B_validacion_", "S4","Validación con corrección A+B (pasto denso 1 y 2, ralo, adoquín, cartulina blanca)","válido","","Tabla validacion; Fig. campo_espectros"),
 (r"^registro_sensorA-B_operacion_E4_nubes_20261026_172414", "S4","E4 con nubes (mal ejecutada)","descartado","Ejecutada mal, según el usuario",""),
 (r"^registro_sensorA-B_operacion_E4_nubes_20261026_173202", "S4","E4 con nubes, bastón quieto 5,5 min","válido","","Fig. campo_E4"),
 (r"^registro_sensorA_ptfe_lab_prueba_G|^registro_sensorA-B_ptfe_lab_prueba_G", "S5","Prueba de ganancia y diagnóstico del bus I2C","auxiliar","Diagnóstico; varias con el nadir en 0",""),
 (r"^registro_sensorA-B_ptfe_lab_solo15x15_20261028_230028|_20260415_1336(39)|ref_6mm_negro_20260415|ref_6mm_blanco_20260415_134(205|317)|ref_3mm_blanco_20260415|solo15x30_b_20260415", "S5","PTFE, intento 1","válido","","Tabla ptfe; Fig. lab29_ptfe"),
 (r"ref_6mm_blanco_20260415_134042", "S5","PTFE, intento 1, 6 mm sobre blanco","descartado","VIS saturado en 20 de 20 lecturas",""),
 (r"llenado_(20|25)cm", "S5","Llenado: láminas apiladas sobre negro, lámina bajada 5 y 10 cm","válido","Corregir por irradiancia (la lámina se bajó)","Tabla llenado"),
 (r"_ptfe_lab_.*_20261028_23(5|59)|_ptfe_lab_.*_20261029_000(000|141)", "S5","PTFE, intento 2 (montaje fijo)","válido","","Tabla ptfe; Fig. lab29_ptfe"),
 (r"lab_E1_blanco1_20261028_010058|lab_E1_pasto_20261028_010404|lab_E4_12V_20261028_010623|lab_E4_11V_20260415_133412", "S5","Pasto, intento 1 (blanco = láminas apiladas)","válido","","Tabla E1"),
 (r"lab_E4_11V_20261028_010934", "S5","Pasto, intento 1, E4 11 V","descartado","Cortada (2 lecturas)",""),
 (r"registro_sensorA_lab_E4_10V_20260415_133653", "S5","Pasto, intento 1, E4 10 V solo nadir","descartado","El cenit no llegó",""),
 (r"lab_E4_(10V_20260415_134842|09V_20260415_135059|12Vb_20260415_135308)", "S5","Pasto, intento 1 tras mover el montaje","descartado","Otra zona del pasto y sin blanco final",""),
 (r"lab_E1_blanco1_20261028_020230", "S5","Pasto, intento 2, blanco inicial (solo 15x30)","válido con reservas","El cenit se movió ~4 % antes del resto del intento","Sec. 9.8 (límites)"),
 (r"lab_E1_pasto_20260415_133410", "S5","Pasto, intento 2, E1","válido con reservas","Cortado en la lectura 37","Sec. 9.8.3"),
 (r"lab_E4_11V_20260415_133935", "S5","Pasto, intento 2, E4 11 V","descartado","Corrió al mismo tiempo que 134004 (dos procesos)",""),
 (r"lab_E4_(12V_20260415_133653|11V_20260415_134004|11V_20260415_134140|10V_20260415_134342|10V_20260415_134439|09V_20260415_134747|12Vb_20260415_135009)|lab_E1_blanco2_20260415_135238", "S5","Pasto, intento 2, E4 y blanco final","válido","","Tabla E4lab; Fig. lab29_E4"),
 (r"^registro_sensorA_prueba_bus_bmp_20260415_1337|^registro_sensorA_prueba_bus_bmp_20260415_1338", "S6","Prueba del bus I2C con el AS7343 y el BMP280 (reloj sin ajustar)","auxiliar","Comprobación de conexión","Sec. 9.10"),
 (r"campo_5nov_prueba_", "S7","Lectura de arranque o de prueba","auxiliar","Comprobación de funcionamiento",""),
 (r"campo_5nov_W_sol_1_20261105_082842", "S7","Blanco (cartón) al sol a 0,5x","válido","Evidencia de saturación: 10 de 10 lecturas saturadas","Sec. 9.11 (procedimiento)"),
 (r"campo_5nov_W_nube_8_20261105_094346", "S7","Blanco del bloque nube 8 (cortado al iniciar)","descartado","Archivo sin lecturas; repetido a las 09:44:14",""),
 (r"saturacion_sensorB_cenit_3mm_sol_pleno_20261105_083324|saturacion_sensorA_carton_15cm_carton_sol_20261105_083352|saturacion_sensorB_cenit_3mm_sol_pleno_20261105_092830", "S7","Barrido de saturación al sol (cenit, o nadir sobre el cartón)","válido","","Sec. 9.11.2 (saturación del cenit)"),
 (r"saturacion_sensorA_carton_15cm_carton_sol_20261105_092954", "S7","Barrido del nadir sobre el cartón (9:29)","válido con reservas","El cartón estaba a la sombra (sombrilla o caja): no representa sol pleno",""),
 (r"campo_5nov_(G|Gf|W|Wf)_(sol|nube)_", "S7","Bloque de sol o de nube (ver motivo)","válido","","Sec. 9.11; Tablas solnube y bloques5"),
 (r"registro_sensorA-B_prueba_noche_20261106", "S8","Comprobación de los dos sensores al iniciar","auxiliar","Comprobación de arranque",""),
 (r"registro_sensorA_ajuste_nadir_T|registro_sensorB_ajuste_cenit_T", "S8","Ajuste de la distancia de la lámpara (3 lecturas a la ganancia más alta del tramo)","auxiliar","Ajuste previo a cada tramo","Tabla tramos6"),
 (r"registro_sensorB_apuntar_cenit_20261106", "S8","Búsqueda del punto de más luz moviendo la lámpara frente al cenit","auxiliar","Muestra que el sensor B está descentrado bajo el PTFE (41 a 10 878 cuentas a 64x)","Sec. 9.12"),
 (r"ganancias_sensorB_cenit_T3_20261106_193509", "S8","Factores de ganancia del cenit, T3 (32-256x), primer intento","descartado","La luz cayó a la mitad entre la ida y la vuelta (cenit mal apuntado)",""),
 (r"ganancias_sensorB_cenit_T2_20261106_194616", "S8","Factores de ganancia del cenit, T2 (8-64x), con poca luz","válido con reservas","Antes de reapuntar (1,7 % de la escala a 8x); se usa como repetición: coincide dentro de 0,5 %","Sec. 9.12 (repetición)"),
 (r"ganancias_sensorA_nadir_T[123]_20261106|ganancias_sensorB_cenit_T3_20261106_194905|ganancias_sensorB_cenit_T2_20261106_195229", "S8","Factores de ganancia por tramos, ida y vuelta","válido","","Tablas tramos6 y fG6; Fig. gan6"),
 (r"oscuridad_sensorA-B_noche6nov_20261106_195455", "S8","Oscuridad de A y B a 0,5, 16, 32, 64, 128, 256 y 512x","válido","","Sec. 9.12 (oscuridad)"),
 (r"registro_sensorA-B_inicio_20261110", "S9","Comprobación de los dos sensores al iniciar (en casa, 14:01)","auxiliar","Comprobación de arranque",""),
 (r"oscuridad_sensorA-B_oscuridad_10nov", "S10","Oscuridad a 1024x con tela negra doblada","válido","","9.14"),
 (r"registro_sensorA-B_inicio_noche_20261110", "S10","Comprobación de los dos sensores al iniciar","auxiliar","Comprobación de arranque",""),
 (r"registro_sensorB_ajuste_angular", "S10","Ajuste de ganancia del cenit para la respuesta angular (512x)","auxiliar","Ajuste",""),
 (r"registro_sensorB_ang[12]_", "S10","Respuesta angular del cenit (plano 1: caja normal; plano 2: caja girada 1/4)","válido","","9.14"),
 (r"registro_sensorB_fuga_", "S10","Fuga de F6 (con y sin aluminio en los lados de la cápsula)","válido","","9.14"),
 (r"registro_sensorA_ajuste_E3", "S10","Ajuste de la luz para E3 (64x)","auxiliar","Ajuste",""),
 (r"registro_sensorA_E3_ciclo_20261111_0103", "S10","E3, corrida 1 (sin bolsa; se cortó la conexión)","válido","Tramo inicial de E3; se analiza unido a las corridas 2 y 3","9.14"),
 (r"registro_sensorA_E3_ciclo_20261111_0106", "S10","E3, corrida 2 (se puso la bolsa; se cortó la conexión)","válido","Se analiza unida a las corridas 1 y 3","9.14"),
 (r"registro_sensorA_E3_ciclo_20261111_0108", "S10","E3, corrida 3 (bolsa hasta la lectura 730 y enfriamiento)","válido","","9.14"),
 (r"registro_sensorA_ajuste_nadir_T0_2026111", "S10","Ajuste a 4x para el factor de 0,5x","auxiliar","Ajuste",""),
 (r"ganancias_sensorA_nadir_T0_2026111", "S10","Factor de 0,5x del nadir (0,5-1-2-4x, ida y vuelta)","válido","Dos corridas; la segunda aprovechando el montaje","9.14"),
]
def clasifica(n):
    base=re.sub(r"(_resumen|_pasos)?\.(csv|json)$","",n)
    for rx,s,pr,es,mo,uso in R:
        if re.search(rx,base): return s,pr,es,mo,uso
    return None
rows=[]; sin=[]
for f in sorted(os.listdir(POOL)):
    c=clasifica(f)
    if c is None: sin.append(f); continue
    s,pr,es,mo,uso=c
    tipo="resumen" if "_resumen" in f else ("pasos" if "_pasos" in f else ("oscuridad (json)" if f.endswith(".json") else "crudo"))
    carpeta=os.path.join(SES[s][0],"crudos" if es!="descartado" else os.path.join("crudos","descartados"))
    os.makedirs(os.path.join(OUT,carpeta),exist_ok=True); shutil.copy2(os.path.join(POOL,f),os.path.join(OUT,carpeta,f))
    r={"sesion":SES[s][0],"fecha":SES[s][1],"archivo":f,"carpeta":carpeta.replace(os.sep,"/"),"tipo":tipo,"prueba":pr,"estado":es,"motivo":mo,"uso_en_informe":uso}
    if tipo=="crudo":
        try:
            d=pd.read_csv(os.path.join(POOL,f)); r["filas"]=len(d)
            if len(d) and "n_ganancia_x" in d: r["ganancias_nadir"]=" ".join(f"{g:g}" for g in sorted(d.n_ganancia_x.dropna().unique()))
            if len(d) and "z_ganancia_x" in d and d.z_ganancia_x.notna().any(): r["ganancias_cenit"]=" ".join(f"{g:g}" for g in sorted(d.z_ganancia_x.dropna().unique()))
            if len(d) and "z_desfase_s" in d: r["pares_desfase_le_0.3s"]=int((d.z_desfase_s.abs()<=0.3).sum())
            if len(d) and "n_temp_c" in d: r["temperatura"]="sí" if d.n_temp_c.notna().any() else "no"
            if len(d) and "etiqueta" in d: r["etiqueta"]=str(d.etiqueta.iloc[0])
            if len(d) and "n_t" in d: r["duracion_s"]=round(float(d.n_t.iloc[-1]-d.n_t.iloc[0]),1)
        except pd.errors.EmptyDataError: r["filas"]=0
    rows.append(r)
# 5 nov: condición del cielo y etiqueta real (notas del operador)
rev=os.path.join(OUT,"derivados","campo_5nov_revision_por_archivo.csv")
if os.path.exists(rev):
    rv=pd.read_csv(rev,dtype={"hora":str}).set_index("hora")
    for r in rows:
        m=re.search(r"campo_5nov_(?:G|Gf|W|Wf)_(?:sol|nube)_\d+_20261105_(\d{6})",r["archivo"])
        if not m or m.group(1) not in rv.index or r["archivo"].endswith("094346.csv"): continue
        x=rv.loc[m.group(1)]; notas=[f"Cielo: {x.condicion}"]
        if x.etiqueta_real!=x.etiqueta: notas.append(f"etiqueta real {x.etiqueta_real}")
        if "sombrilla" in str(x.condicion):
            r["estado"]="válido con reservas"; notas.append("con sombrilla el cenit no siempre quedó en la misma sombra")
        r["motivo"]="; ".join(notas)
cols=["sesion","fecha","archivo","carpeta","tipo","etiqueta","prueba","estado","motivo","uso_en_informe","filas","duracion_s","ganancias_nadir","ganancias_cenit","pares_desfase_le_0.3s","temperatura"]
df=pd.DataFrame(rows).reindex(columns=cols)
df.to_csv(os.path.join(OUT,"indice_corridas.csv"),index=False,encoding="utf-8-sig")
print(len(df),"archivos clasificados; sin clasificar:",sin)
print(df[df.tipo=="crudo"].groupby(["sesion","estado"]).size().to_string())
