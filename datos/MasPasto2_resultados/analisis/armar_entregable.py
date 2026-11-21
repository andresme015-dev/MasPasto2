"""Arma el entregable (e) de la propuesta: conjunto de prueba con las mediciones reales del dispositivo,
depurado y trazable. Fuente primaria: el CSV consolidado que exportó la interfaz a la memoria USB el
18 nov 2026 (57 filas). La validez de cada toma sale de las revisiones ya hechas en el paquete de
resultados (sitio10_mediciones.csv y tarde11_interfaz.csv) y de las notas del operador."""
import csv, os, shutil
from datetime import datetime, timedelta
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"           # carpeta MasPasto2_resultados
USB = os.path.join(R, "..", "exportacion_usb_18nov") + "/"                        # lo que copió la interfaz a la USB
DER = R + "derivados/"
OUT = os.path.join(R, "..", "conjunto_de_prueba") + "/"
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT + "fotos/camara_dispositivo"); os.makedirs(OUT + "fotos/celular_huellas")

filas = list(csv.DictReader(open(USB + "mediciones_maspasto2_20260415_1356.csv", encoding="utf-8")))
assert len(filas) == 57
s10 = pd.read_csv(DER + "sitio10_mediciones.csv")
t11 = pd.read_csv(DER + "tarde11_interfaz.csv")
sup = pd.read_csv(DER + "tarde11_superficies.csv")
can = pd.read_csv(DER + "sitio10_canopeo_fotos.csv")

NOMBRES = {"V1": "Pasto alto verde", "V2": "Pasto verde bajo", "V3": "Pasto con parches secos", "T": "Tierra",
           "A": "Grava", "V4": "Pasto seco", "N": "Lámina negra", "Gr": "Lámina gris", "B2": "Pliego blanco",
           "C": "Cartón blanco (control)"}
LAMINAS = {"N", "Gr", "B2", "C"}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def local(hora_utc):
    t = datetime.strptime(hora_utc[:19], "%Y-%m-%dT%H:%M:%S") - timedelta(hours=5)
    return t


registro = []
i10 = 0
for f in filas:
    t = local(f["hora_celular"])
    d = dict(fecha=t.strftime("%Y-%m-%d"), hora=t.strftime("%H:%M:%S"), id_disp=int(f["id"]), punto=f["punto"],
             nota_operador=f["nota"])
    dia = t.strftime("%m-%d")
    cod, toma, tipo, estado, motivo, ref, lugar = "", "", "Superficie real", "Válida", "", "", ""
    alt_ok, alt_nota = True, ""
    foto_cam, foto_cel, verde, ndvi_c, ndre2_c = "", "", None, None, None
    p = f["punto"]
    if dia == "11-04":
        tipo, estado, lugar = "Prueba", "Prueba (no válida)", "Casa (interiores)"
        motivo = "Prueba de la interfaz en interiores; el operador la marcó como no válida"
        cod = "P"; foto_cam = f"medicion_{int(f['id']):04d}.jpg"; ref = "Cartón blanco"
    elif dia == "11-05":
        lugar = "Zona verde, Universidad de los Andes"; ref = "Cartón blanco"; cod = "U"
        nombre_p = {"campo nublado": "U1", "campo2 nublado": "U2", "punto 1 nublado": "U3", "punto 2 nubaldo": "U4",
                    "punto 3 nubaldo": "U5", "punto 4 nubaldo": "U6"}[p]
        cod = nombre_p; toma = "2" if f["nota"] == "toma 2" else "1"
        alt_ok, alt_nota = False, "Altura no válida: la distancia al suelo se tomó sobre el mismo pasto en cada punto"
        foto_cam = f"medicion_{int(f['id']):04d}.jpg"
        motivo = "" if not f["avisos"] else "Válida (5 de 5 pares; aviso: " + f["avisos"] + ")"
    elif dia == "11-10":
        lugar = "Zona verde cerca de la casa del autor"; ref = "Cartulina gris"
        r = s10.iloc[i10]; assert r["hora_celular"] == f["hora_celular"]; i10 += 1
        cod, toma = r["codigo"], str(int(r["toma"]))
        estado = "Válida" if r["valida"] else "Descartada"
        motivo = "" if r["valida"] else r["motivo_descarte"]
        if cod in LAMINAS:
            tipo = "Lámina de referencia"; alt_ok, alt_nota = False, "No aplica: lámina de calibración"
        elif cod in ("T", "A"):
            alt_nota = "Superficie desnuda: la altura aparente incluye un desfase de unos 4 cm"
        if cod == "T":
            alt_nota += "; parche de 30–45 cm, el sensor ve también el pasto de alrededor"
        if i10 == 26:   # la última toma del día es la única con foto de cámara (las demás se sobrescribieron)
            foto_cam = "medicion_0011_grava_A.jpg"   # medicion_0011.jpg en la USB; renombrada en la carpeta de la sesión
        else:
            foto_cam = "No disponible: la interfaz sobrescribió las fotos de este día (falla corregida el 10 nov)"
        if cod in ("V1", "V2", "V3", "T", "A"):
            cc = can[can.codigo == cod]
            foto_cel = ", ".join(cc.foto); verde = round(cc.verde_pct.mean(), 1)
        if r["valida"] and cod not in LAMINAS:
            s = sup[(sup.dia == "10 nov") & (sup.id == r["fila"])]
            if len(s): ndvi_c, ndre2_c = float(s.ndvi_carton.iloc[0]), float(s.ndre2_carton.iloc[0])
    elif dia == "11-11" and f["punto"] == "Prueba Casa":
        tipo, estado, lugar, cod = "Prueba", "Prueba (no válida)", "Casa (noche)", "P"
        motivo = "Prueba del sistema en casa, de noche"; foto_cam = os.path.basename(f["foto"]); ref = "—"
    else:
        lugar = "Zona verde cerca de la casa del autor"
        r = t11[t11.id == int(f["id"])].iloc[0]
        cod = r["codigo"]; toma = p.split("toma")[-1].strip() if "toma" in p else "1"
        estado = "Válida" if r["valida"] else "Descartada"
        motivo = "" if r["valida"] else r["motivo"]
        foto_cam = os.path.basename(f["foto"])
        if int(f["id"]) == 32:
            foto_cam = "medicion_0032_recuperada_captura.png"
        if cod in LAMINAS:
            tipo = "Lámina de referencia"; ref = "Cartón blanco"; alt_ok, alt_nota = False, "No aplica: lámina de calibración"
        else:
            ref = "Cartulina gris"
            if cod == "T": alt_nota = "Superficie desnuda: la altura aparente incluye un desfase de unos 4 cm"
            s = sup[(sup.dia == "11 nov") & (sup.id == int(f["id"]))]
            if len(s):
                ndvi_c, ndre2_c, verde = float(s.ndvi_carton.iloc[0]), float(s.ndre2_carton.iloc[0]), round(float(s.verde_pct.iloc[0]), 1)
    d.update(lugar=lugar, codigo=cod, superficie=NOMBRES.get(cod, "Pasto (campo)" if cod.startswith("U") else "—"),
             toma=toma, tipo=tipo, estado=estado, motivo=motivo, referencia=ref,
             pares=f"{f['pares_validos']} de {f['pares_pedidos']}", gan_nadir=f["ganancia_nadir"], gan_cenit=f["ganancia_cenit"],
             cv=num(f["cv_cociente_nir_pct"]), luz=num(f["luz_relativa_blanco"]),
             ndvi=num(f["ndvi"]), ndre1=num(f["ndre1"]), ndre2=num(f["ndre2"]),
             f6=num(f["rho_f6"]), f7=num(f["rho_f7"]), f8=num(f["rho_f8"]), nir=num(f["rho_nir"]),
             ndvi_c=ndvi_c, ndre2_c=ndre2_c,
             altura=num(f["altura_cm"]) if alt_ok else None,
             biomasa=num(f["biomasa_kg_ms_ha"]) if alt_ok else None,
             alt_nota=alt_nota if alt_ok or alt_nota else "", temp=num(f["temp_c"]), verde=verde,
             foto_cam=foto_cam, foto_cel=foto_cel, avisos=f["avisos"])
    if d["fecha"] == "2026-11-05":   # la referencia de ese día fue el cartón: el valor frente al cartón es el mismo
        d["ndvi_c"], d["ndre2_c"] = d["ndvi"], d["ndre2"]
    if cod in ("T", "A") and d["biomasa"] is not None:
        d["biomasa"] = None
        d["alt_nota"] += "; biomasa no aplica (superficie sin pasto: la altura aparente es el desfase)"
    if alt_ok and d["altura"] is None:
        d["alt_nota"] = (d["alt_nota"] + "; " if d["alt_nota"] else "") + "Sin lectura del LiDAR"
    registro.append(d)
assert i10 == 26

# Identificadores únicos en orden cronológico; fotos copiadas con el identificador
registro.sort(key=lambda d: (d["fecha"], d["hora"]))
fuentes = {"11-04": R + "2026-11-04_casa_sensores_reales/interfaz/fotos/", "11-05": R + "2026-11-05_campo_sol_nube/interfaz/fotos/",
           "11-10": R + "2026-11-10_sitio_E2_superficies/interfaz/fotos/", "11-11": R + "2026-11-11_tarde_par_superficies_E_F/fotos/"}
for k, d in enumerate(registro, 1):
    d["id"] = f"R{k:02d}"
    fc = d["foto_cam"]
    if fc.startswith("medicion"):
        dia = d["fecha"][5:]
        src = fuentes[dia] + fc
        if not os.path.exists(src): src = USB + "fotos/" + fc
        ext = os.path.splitext(fc)[1]
        nuevo = f"{d['id']}_{d['codigo']}_camara{ext}"
        if os.path.exists(src) and os.path.getsize(src) > 0:
            shutil.copyfile(src, OUT + "fotos/camara_dispositivo/" + nuevo)
            d["foto_cam"] = "camara_dispositivo/" + nuevo + (" (oscura: cámara desalineada)" if dia == "11-05" else "")
        else:
            d["foto_cam"] = "No disponible"
for fn in can.foto:
    shutil.copyfile(R + "2026-11-10_sitio_E2_superficies/fotos/" + fn, OUT + "fotos/celular_huellas/" + fn)
for d in registro:
    if d["foto_cel"]:
        d["foto_cel"] = ", ".join("celular_huellas/" + x for x in d["foto_cel"].split(", "))

validas = [d for d in registro if d["estado"] == "Válida" and d["tipo"] == "Superficie real"]
calib = [d for d in registro if d["estado"] == "Válida" and d["tipo"] == "Lámina de referencia"]
rep = {}
for k, d in enumerate(validas, 1):
    d["id_m"] = f"M{k:02d}"
    clave = (d["fecha"], d["codigo"]); rep[clave] = rep.get(clave, 0) + 1; d["repeticion"] = rep[clave]
    d["origen_verde"] = ("Promedio de las 3 fotos de la huella (celular)" if d["fecha"] == "2026-11-10" else
                         "Foto de la cámara del dispositivo" if d["verde"] is not None else "No calculada (fotos oscuras)")

# ------------------------------------------------------------------------------- libro
AZ = "1F3A93"
hfont = Font(name="Arial", bold=True, color="FFFFFF", size=10)
hfill = PatternFill("solid", fgColor=AZ)
bfont = Font(name="Arial", size=10)
thin = Side(style="thin", color="D0D0D0")
borde = Border(left=thin, right=thin, top=thin, bottom=thin)
wb = Workbook()


def hoja(nombre, columnas, datos, anchos):
    ws = wb.create_sheet(nombre)
    for j, (titulo, _, fmt) in enumerate(columnas, 1):
        c = ws.cell(row=1, column=j, value=titulo); c.font = hfont; c.fill = hfill
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center"); c.border = borde
    for i, d in enumerate(datos, 2):
        for j, (_, clave, fmt) in enumerate(columnas, 1):
            v = d.get(clave)
            c = ws.cell(row=i, column=j, value=v if v not in ("",) else None)
            c.font = bfont; c.border = borde; c.alignment = Alignment(vertical="top", wrap_text=clave in ("motivo", "alt_nota", "foto_cel", "foto_cam", "nota_operador", "origen_verde"))
            if fmt: c.number_format = fmt
    for j, w in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.row_dimensions[1].height = 42
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(columnas))}{len(datos) + 1}"
    return ws


I4, I3, I1 = "0.0000", "0.000", "0.0"
cols_m = [("ID", "id_m", None), ("ID registro", "id", None), ("Fecha", "fecha", None), ("Hora (Bogotá)", "hora", None),
          ("Lugar", "lugar", None), ("Código", "codigo", None), ("Superficie", "superficie", None), ("Repetición", "repeticion", None),
          ("Referencia de la sesión", "referencia", None), ("NDVI", "ndvi", I4), ("NDRE₂ (745/690)", "ndre2", I4),
          ("NDRE₁ (855/745)", "ndre1", I4), ("NDVI frente al cartón", "ndvi_c", I4), ("NDRE₂ frente al cartón", "ndre2_c", I4),
          ("ρ F6 640 nm", "f6", I4), ("ρ F7 690 nm", "f7", I4), ("ρ F8 745 nm", "f8", I4), ("ρ NIR 855 nm", "nir", I4),
          ("Altura (cm)", "altura", I1), ("Biomasa estimada (kg MS/ha)", "biomasa", "0"), ("Nota de altura", "alt_nota", None),
          ("CV del cociente NIR (%)", "cv", "0.00"), ("Luz frente a la referencia", "luz", "0.00"), ("Pares válidos", "pares", None),
          ("Ganancia nadir", "gan_nadir", None), ("Ganancia cenit", "gan_cenit", None), ("Temperatura (°C)", "temp", I1),
          ("Fracción verde (%)", "verde", I1), ("Origen de la fracción verde", "origen_verde", None), ("Foto de la cámara del dispositivo", "foto_cam", None),
          ("Fotos de la huella (celular)", "foto_cel", None)]
anch_m = [6, 9, 11, 10, 22, 8, 22, 6, 14] + [9] * 9 + [9, 11, 30, 10, 10, 9, 9, 9, 10, 9, 26, 34, 34]
cols_r = [("ID registro", "id", None), ("ID en el dispositivo", "id_disp", None), ("Fecha", "fecha", None), ("Hora (Bogotá)", "hora", None),
          ("Lugar", "lugar", None), ("Punto (escrito en la interfaz)", "punto", None), ("Nota del operador", "nota_operador", None),
          ("Código", "codigo", None), ("Superficie", "superficie", None), ("Toma (según la interfaz)", "toma", None), ("Tipo", "tipo", None),
          ("Estado", "estado", None), ("Motivo", "motivo", None), ("Referencia de la sesión", "referencia", None),
          ("NDVI", "ndvi", I4), ("NDRE₂ (745/690)", "ndre2", I4), ("NDRE₁ (855/745)", "ndre1", I4),
          ("CV del cociente NIR (%)", "cv", "0.00"), ("Luz frente a la referencia", "luz", "0.00"), ("Pares válidos", "pares", None),
          ("Ganancia nadir", "gan_nadir", None), ("Ganancia cenit", "gan_cenit", None), ("Altura (cm)", "altura", I1),
          ("Biomasa estimada (kg MS/ha)", "biomasa", "0"), ("Nota de altura", "alt_nota", None), ("Temperatura (°C)", "temp", I1),
          ("Foto de la cámara del dispositivo", "foto_cam", None), ("Avisos de la interfaz", "avisos", None)]
anch_r = [9, 10, 11, 10, 22, 16, 22, 8, 20, 6, 16, 16, 36, 14, 9, 9, 9, 10, 10, 9, 9, 9, 9, 11, 30, 10, 34, 24]
cols_c = [("ID registro", "id", None), ("Fecha", "fecha", None), ("Hora (Bogotá)", "hora", None), ("Código", "codigo", None),
          ("Lámina", "superficie", None), ("Toma", "toma", None), ("Referencia de la sesión", "referencia", None),
          ("NDVI", "ndvi", I4), ("NDRE₂ (745/690)", "ndre2", I4), ("ρ F6 640 nm", "f6", I4), ("ρ F7 690 nm", "f7", I4),
          ("ρ F8 745 nm", "f8", I4), ("ρ NIR 855 nm", "nir", I4), ("CV del cociente NIR (%)", "cv", "0.00"),
          ("Luz frente a la referencia", "luz", "0.00"), ("Pares válidos", "pares", None), ("Altura y biomasa", "alt_nota", None),
          ("Foto de la cámara del dispositivo", "foto_cam", None)]
anch_c = [9, 11, 10, 8, 20, 6, 14] + [9] * 6 + [10, 10, 9, 28, 34]

# Hoja de presentación con conteos por fórmula sobre el registro
ws = wb.active; ws.title = "Léeme"
ws.column_dimensions["A"].width = 46; ws.column_dimensions["B"].width = 14; ws.column_dimensions["C"].width = 70
lineas = [
    ("MasPasto2 · Conjunto de prueba de mediciones reales (entregable e)", None, None),
    ("Andrés Felipe Méndez Martínez · Proyecto de grado, Ingeniería Electrónica, Universidad de los Andes", None, None),
    ("", None, None),
    ("Qué contiene", None, None),
    ("Conjunto de prueba", None, "Mediciones válidas sobre superficies reales: el conjunto que pide la propuesta (al menos 20)."),
    ("Referencias y calibración", None, "Tomas válidas sobre láminas de referencia (gris, negra, pliego blanco, cartón). No tienen altura ni biomasa."),
    ("Registro completo", None, "Las 57 filas que exportó el dispositivo, cada una con su estado y el motivo si se descartó."),
    ("", None, None),
    ("Conteos (calculados sobre el registro completo)", None, None),
    ("Filas exportadas por el dispositivo", "=COUNTA('Registro completo'!A2:A200)", ""),
    ("Válidas sobre superficies reales (conjunto de prueba)", "=COUNTIFS('Registro completo'!L2:L200,\"Válida\",'Registro completo'!K2:K200,\"Superficie real\")", "Compromiso de la propuesta: al menos 20."),
    ("Válidas sobre láminas de referencia", "=COUNTIFS('Registro completo'!L2:L200,\"Válida\",'Registro completo'!K2:K200,\"Lámina de referencia\")", ""),
    ("Descartadas", "=COUNTIF('Registro completo'!L2:L200,\"Descartada\")", "Nube (luz < 80 % de la referencia), CV del cociente > 5 %, lecturas sin cenit o repetición del operador."),
    ("Pruebas (no válidas)", "=COUNTIF('Registro completo'!L2:L200,\"Prueba (no válida)\")", "Pruebas de la interfaz en casa."),
    ("", None, None),
    ("Cómo leerlo", None, None),
    ("Origen de los datos", None, "CSV consolidado que la interfaz copió a una memoria USB el 18 nov 2026 (mediciones_maspasto2_*.csv). Los valores no se recalcularon: son los que entregó el dispositivo."),
    ("Fecha y hora", None, "Hora del celular convertida a hora de Bogotá. La hora de la Raspberry Pi no se usa: sin reloj ni internet arranca en una fecha errada."),
    ("Identificadores", None, "ID registro (R01–R57) es único y cronológico. El 10 nov la interfaz guardó todas las filas con el número 11 (falla corregida), por eso se renumeró."),
    ("Índices y reflectancias", None, "Relativos a la referencia de la sesión (cartón blanco el 5 nov, cartulina gris el 10 y 11 nov). Son los que calculó el dispositivo, con las ganancias nominales: la corrección por factores de ganancia se instaló el 18 nov y cambia el NDVI en 0,0055 como máximo. Las columnas «frente al cartón» se recalcularon desde las cuentas crudas, con los factores de ganancia, y expresan los índices respecto al cartón, como en la Tabla de E2 del documento final."),
    ("Altura", None, "Distancia al suelo menos la lectura del LiDAR. El 5 nov la distancia al suelo se tomó sobre el mismo pasto, así que esas alturas no son válidas. En tierra y grava hay un desfase de unos 4 cm."),
    ("Biomasa", None, "Estimación del modelo preliminar (Random Forest, datos públicos CSIRO). Es demostrativa: el modelo no está calibrado para pasturas colombianas. Se deja vacía donde la altura no es válida y en tierra y grava, donde la altura aparente es solo el desfase."),
    ("Fotos", None, "Carpeta fotos/: camara_dispositivo (cámara de la Raspberry Pi, renombradas con el ID) y celular_huellas (fotos de las huellas del 10 nov, tomadas con el celular para calcular la fracción verde). Las del 5 nov salieron oscuras (cámara desalineada); las del 10 nov se sobrescribieron salvo la última; la del R57 se recuperó de una captura de pantalla."),
    ("Toma y repetición", None, "«Toma» es el rótulo que escribió el operador en la interfaz (a veces repetido cuando una toma se volvió a medir). En el conjunto de prueba, «Repetición» numera de 1 a 3, en orden de hora, las tomas válidas de cada superficie y día."),
    ("Ganancias", None, "Ganancia automática de cada sensor. Un valor como 4/8 indica que la ganancia cambió entre las lecturas de la misma toma; la interfaz corrige cada lectura con su factor de ganancia."),
    ("Luz frente a la referencia", None, "Luz del cenit en la toma dividida por la luz al registrar la referencia. Menos de 0,80 (nube) se descartó. Más de 1 indica que salió el sol después de la referencia; el cociente nadir/cenit compensa ese cambio."),
    ("Formato abierto", None, "conjunto_de_prueba.csv y registro_completo.csv tienen los mismos datos en texto (UTF-8, separador coma, punto decimal)."),
]
for i, (a, b, c) in enumerate(lineas, 1):
    ws.cell(row=i, column=1, value=a).font = Font(name="Arial", size=10, bold=a in ("Qué contiene", "Conteos (calculados sobre el registro completo)", "Cómo leerlo") or i == 1)
    if i == 1: ws.cell(row=1, column=1).font = Font(name="Arial", size=14, bold=True, color=AZ)
    if b is not None:
        cb = ws.cell(row=i, column=2, value=b); cb.font = Font(name="Arial", size=10, bold=True, color=AZ); cb.alignment = Alignment(horizontal="center")
    if c:
        cc = ws.cell(row=i, column=3, value=c); cc.font = Font(name="Arial", size=10); cc.alignment = Alignment(wrap_text=True, vertical="top")
    ws.cell(row=i, column=1).alignment = Alignment(wrap_text=True, vertical="top")

ws.cell(row=1, column=1).alignment = Alignment(wrap_text=False); ws.cell(row=2, column=1).alignment = Alignment(wrap_text=False)
for i in range(1, len(lineas) + 1):
    ws.cell(row=i, column=2).alignment = Alignment(horizontal="center", vertical="top")
hoja("Conjunto de prueba", cols_m, validas, anch_m)
hoja("Referencias y calibración", cols_c, calib, anch_c)
hoja("Registro completo", cols_r, registro, anch_r)
wb.save(OUT + "MasPasto2_conjunto_de_prueba.xlsx")

pd.DataFrame([{t: d.get(k) for t, k, _ in cols_m} for d in validas]).to_csv(OUT + "conjunto_de_prueba.csv", index=False, encoding="utf-8")
pd.DataFrame([{t: d.get(k) for t, k, _ in cols_r} for d in registro]).to_csv(OUT + "registro_completo.csv", index=False, encoding="utf-8")
open(OUT + "LEEME.txt", "w", encoding="utf-8").write(
    "MasPasto2 - Conjunto de prueba de mediciones reales (entregable e de la propuesta)\n"
    "Andres Felipe Mendez Martinez - Proyecto de grado, Ingenieria Electronica, Universidad de los Andes\n\n"
    "MasPasto2_conjunto_de_prueba.xlsx   libro principal (empiece por la hoja \"Leeme\")\n"
    "conjunto_de_prueba.csv              31 mediciones validas sobre superficies reales (texto, UTF-8)\n"
    "registro_completo.csv               las 57 filas que exporto el dispositivo, con estado y motivo\n"
    "fotos/camara_dispositivo/           fotos de la camara del dispositivo, nombradas con el ID del registro (R##)\n"
    "fotos/celular_huellas/              fotos de las huellas del 10 nov tomadas con el celular\n\n"
    "Origen: CSV consolidado copiado por la interfaz a una memoria USB el 18 nov 2026.\n"
    "Conteo: 31 validas sobre superficies reales, 12 validas sobre laminas de referencia,\n"
    "10 descartadas y 4 pruebas.\n")
from collections import Counter
print(len(registro), Counter((d["tipo"], d["estado"]) for d in registro))
print("validas", len(validas), Counter(d["fecha"] for d in validas))
