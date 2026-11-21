"""Flujo de medicion integrado de MasPasto2.

Una medicion toma varios pares nadir/cenit con ganancia adaptativa, los divide por la
referencia blanca de la sesion (Ec. rho del informe), calcula NDVI, NDRE1 y NDRE2, lee la
altura con el LiDAR, la inclinacion con el MPU-6050, la temperatura, toma una foto, estima la
biomasa con el modelo y guarda todo como una fila de CSV.

Lo usa el servidor de la interfaz (servidor.py), pero tambien se puede probar solo:

    python3 medir.py --simulado              # sin sensores: datos sinteticos
    python3 medir.py                         # con los sensores reales

Solo lee sensores y escribe en ~/maspasto2/datos_espectro/mediciones/; no cambia nada del
sistema ni de la red.
"""
import argparse
import csv
import json
import math
import os
import random
import statistics as st
import threading
import time
from datetime import datetime

import caracterizacion_espectro as ce

AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(ce.CARPETA, "mediciones")
ARCHIVO_SESION = os.path.join(CARPETA, "sesion.json")

# Canales de los indices: NDVI 855/640, NDRE1 855/745, NDRE2 745/690
C_ROJO, C_F7, C_F8, C_NIR = "f6_640nm", "f7_690nm", "f8_745nm", "nir_855nm"

CONFIG_DEFECTO = {
    "sensor_nadir": "A",            # sensor fisico del nadir (para su lectura oscura)
    "pares_medicion": 5,            # pares nadir/cenit por medicion
    "pares_blanco": 10,             # pares sobre el PTFE para la referencia blanca
    "desfase_max_s": 0.3,           # pares con mas desfase se descartan (como en caracterizacion)
    "lidar_lecturas": 20,           # lecturas del TF-Nova promediadas (mediana) por medicion           # lecturas promediadas por medicion
    "lidar_cal_a": 1.0275,          # distancia real = a * medida + b (calibracion del 6 oct)
    "lidar_cal_b": -0.80,
    "inclinacion_max_deg": 5.0,
    "foto": True,                   # foto en cada medicion (unos 3 s mas)
    "blanco_vigencia_min": 30,      # aviso si la referencia blanca es mas vieja
}

CAMPOS = ["id", "punto", "nota", "hora_celular", "hora_rpi", "hora_rtc", "simulado",
          "blanco_hora", "con_cenit", "pares_validos", "pares_pedidos", "ganancia_nadir", "ganancia_cenit",
          "rho_f6", "rho_f7", "rho_f8", "rho_nir", "ndvi", "ndre1", "ndre2",
          "cv_cociente_nir_pct", "luz_relativa_blanco",
          "distancia_lidar_cm", "suelo_cm", "altura_cm", "inclinacion_deg", "temp_c",
          "biomasa_kg_ms_ha", "foto", "avisos"]


def cargar_config():
    cfg = dict(CONFIG_DEFECTO)
    ruta = os.path.join(AQUI, "config_medicion.json")
    try:
        with open(ruta) as f:
            cfg.update(json.load(f))
    except OSError:
        pass
    except ValueError as e:
        print(f"Aviso: config_medicion.json no es JSON valido ({e}); se usan los valores por defecto.")
    return cfg


def indice(a, b):
    return (a - b) / (a + b) if a is not None and b is not None and (a + b) != 0 else None


def redondear(v, n=4):
    return round(v, n) if isinstance(v, float) and math.isfinite(v) else v


# ----------------------------------------------------------------------------------
# Sensores reales. Cada uno devuelve None si no esta disponible; la medicion sigue.
# ----------------------------------------------------------------------------------
class Lidar:
    """TF-Nova por USB-serie (test_tfnova.py). Mediana de las lecturas validas, en cm."""

    def __init__(self, cfg):
        import test_tfnova                  # abre /dev/ttyUSB0 al importarse
        self.t = test_tfnova
        self.t.leer_tfnova()                # falla aqui si no llegan tramas

    def leer(self, n=20):
        vals = []
        for _ in range(2 * n):
            if len(vals) >= n:
                break
            try:
                r = self.t.leer_tfnova()
            except RuntimeError:
                continue
            if r["lectura_valida"]:
                vals.append(r["distancia_cm"])
        return st.median(vals) if vals else None


class Imu:
    """MPU-6050 (test_mpu6050.py, 0x69): inclinacion total del baston, promedio de n lecturas."""

    def __init__(self, cfg):
        import test_mpu6050
        self.t = test_mpu6050
        self.t.leer_mpu6050()

    def inclinacion(self, n=10):
        v = []
        for _ in range(n):
            v.append(self.t.leer_mpu6050()["angulo_inclinacion_deg"])
            time.sleep(0.02)
        return st.mean(v)


class Reloj:
    """DS3231 (test_ds3231.py, 0x68): hora del reloj de tiempo real y si es valida."""

    def __init__(self, cfg):
        import test_ds3231
        self.t = test_ds3231
        self.t.leer_ds3231()

    def hora(self):
        r = self.t.leer_ds3231()
        return r["timestamp"] if r["hora_valida"] else ""


class Camara:
    """OV5647 con picamera2 (test_camara.py); cada foto tarda unos 3 s por la espera de 2 s."""

    def __init__(self, cfg):
        import test_camara
        from picamera2 import Picamera2
        if not Picamera2.global_camera_info():
            raise RuntimeError("picamera2 no encuentra la camara")
        self.t = test_camara

    def foto(self, archivo):
        try:
            ruta = self.t.capturar_foto(os.path.dirname(archivo))
            os.replace(ruta, archivo)
            return archivo
        except Exception:
            return None


class Modelo:
    """Random Forest de modelo_biomasa.py (modelo_pasturametrics.pkl); devuelve kg MS/ha."""

    def __init__(self, cfg):
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning)
        import modelo_biomasa
        self.f = modelo_biomasa.estimar_biomasa

    def estimar(self, ndvi, altura_cm):
        return self.f(ndvi, altura_cm)


# ----------------------------------------------------------------------------------
# Sensores simulados (sin hardware): mismas claves que los reales
# ----------------------------------------------------------------------------------
REFL_PASTO = {"f1_405nm": .04, "f2_425nm": .04, "fz_450nm": .045, "f3_475nm": .05, "f4_515nm": .10,
              "f5_550nm": .12, "fy_555nm": .12, "fxl_600nm": .08, "f6_640nm": .05, "f7_690nm": .10,
              "f8_745nm": .38, "nir_855nm": .48}


class Simulador:
    def __init__(self):
        self.luz = 1.0
        self.superficie = "pasto"
        self.vigor = 1.0
        self.suelo = 62.0
        self.altura = 15.0

    def nuevo_punto(self):
        self.vigor = random.uniform(0.4, 1.2)
        self.altura = random.uniform(4, 35) * self.vigor

    def _lectura(self, refl, k, t_fin):
        g = 16.0
        d = {"ganancia_idx": ce.idx_de_x(g), "ganancia_x": g, "t_int_ms": 182.4, "saturado": False,
             "vis_saturado": False, "t": t_fin - 0.55, "t_fin": t_fin, "temp_c": 21.0 + random.gauss(0, .1)}
        for n in ce.NOMBRES:
            d[n] = int(min(ce.TECHO, refl[n] * k * 20000 * self.luz * random.gauss(1, .003)))
        for v in ce.VIS:
            d[v] = int(sum(d[n] for n in ce.NOMBRES) / 4)
        d["max_cuentas"] = d["max_espectral"] = max(d[n] for n in ce.NOMBRES)
        return d

    def par(self):
        self.luz = min(1.5, max(0.3, self.luz * random.gauss(1, .03)))
        if self.superficie == "blanco":
            refl = {n: .95 for n in ce.NOMBRES}
        else:
            refl = {n: REFL_PASTO[n] * (self.vigor if n in (C_F8, C_NIR) else 1 / self.vigor ** .3)
                    for n in ce.NOMBRES}
        t = time.time()
        time.sleep(0.15)
        dn = self._lectura(refl, 0.6, t)
        dz = self._lectura({n: 1.0 for n in ce.NOMBRES}, 0.8, t)
        dz.update(seq=int(t), desfase_s=round(random.gauss(0, .05), 3), id_sensor="B")
        return dn, dz

    def distancia(self):
        return (self.suelo if self.superficie == "suelo" else self.suelo - self.altura) + random.gauss(0, .3)

    def inclinacion(self):
        return abs(random.gauss(2.5, 2))

    def foto(self, archivo):
        return None


# ----------------------------------------------------------------------------------
# Dispositivo
# ----------------------------------------------------------------------------------
class Dispositivo:
    def __init__(self, simulado=False, cfg=None):
        self.cfg = cfg or cargar_config()
        self.simulado = simulado
        self.lock = threading.Lock()
        self.estado_sensores = {}
        os.makedirs(os.path.join(CARPETA, "fotos"), exist_ok=True)
        ce.SENSORES["nadir"] = self.cfg["sensor_nadir"]
        self.sesion = self._cargar_sesion()
        self.nadir = self.zenit = self.lidar = self.imu = self.reloj = self.camara = self.modelo = None
        self.sim = Simulador() if simulado else None
        self._abrir()
        self.osc = {"nadir": ce.cargar_osc("nadir"), "zenit": ce.cargar_osc("zenit")}

    # --- apertura tolerante a fallas ---
    def _probar(self, nombre, fabrica):
        try:
            obj = fabrica()
            self.estado_sensores[nombre] = {"ok": True, "detalle": "conectado"}
            return obj
        except BaseException as e:            # SystemExit del zenit incluido
            self.estado_sensores[nombre] = {"ok": False, "detalle": f"{type(e).__name__}: {e}"[:160]}
            return None

    def _abrir(self):
        if self.simulado:
            for n in ("nadir", "cenit", "lidar", "inclinometro", "temperatura", "reloj", "camara"):
                self.estado_sensores[n] = {"ok": True, "detalle": "simulado"}
        else:
            # solo se abren los que faltan: reabrir el cenit dejaria dos hilos leyendo el mismo puerto
            if self.nadir is None:
                self.nadir = self._probar("nadir", ce.Nadir)
            if self.zenit is None:
                self.zenit = self._probar("cenit", lambda: ce.abrir("zenit", obligatorio=True))
            if self.lidar is None:
                self.lidar = self._probar("lidar", lambda: Lidar(self.cfg))
            if self.imu is None:
                self.imu = self._probar("inclinometro", lambda: Imu(self.cfg))
            if self.reloj is None:
                self.reloj = self._probar("reloj", lambda: Reloj(self.cfg))
            if self.camara is None and self.cfg["foto"]:
                self.camara = self._probar("camara", lambda: Camara(self.cfg))
            ok_t = bool(self.nadir and self.nadir.bmp)
            self.estado_sensores["temperatura"] = {
                "ok": ok_t, "detalle": "BMP280 conectado" if ok_t else "sin sensor de temperatura"}
        if self.modelo is None:
            self.modelo = self._probar("modelo", lambda: Modelo(self.cfg))

    def reconectar(self):
        with self.lock:
            self._abrir()
            self.osc = {"nadir": ce.cargar_osc("nadir"), "zenit": ce.cargar_osc("zenit")}

    # --- sesion (referencia blanca y suelo) ---
    def _cargar_sesion(self):
        try:
            with open(ARCHIVO_SESION) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _guardar_sesion(self):
        with open(ARCHIVO_SESION, "w") as f:
            json.dump(self.sesion, f, indent=1)

    def nueva_sesion(self):
        with self.lock:
            self.sesion = {}
            self._guardar_sesion()

    # --- lecturas ---
    def _par(self):
        if self.simulado:
            return self.sim.par()
        if self.zenit is None:
            return self.nadir.leer(), None
        return ce.leer_par(self.nadir, self.zenit)

    def _pares(self, n, progreso=lambda f, txt: None):
        """n pares validos como maximo en 2n intentos. Devuelve (pares, descartados)."""
        if not self.simulado and self.nadir is None:
            raise RuntimeError("El modulo nadir no esta conectado: no se puede medir.")
        if not self.simulado and self.zenit is not None:
            self.zenit.adaptativa()
        pares, desc = [], {"saturado": 0, "sin_cenit": 0, "desfase": 0}
        for i in range(2 * n):
            if len(pares) >= n:
                break
            progreso(len(pares) / n, f"Lectura espectral {len(pares) + 1} de {n}")
            dn, dz = self._par()
            if dn["saturado"] or (dz and dz["saturado"]):
                desc["saturado"] += 1
            elif dz is None and self._con_cenit():
                desc["sin_cenit"] += 1
            elif dz is not None and abs(dz.get("desfase_s", 0)) > self.cfg["desfase_max_s"]:
                desc["desfase"] += 1
            else:
                pares.append((dn, dz))
        return pares, desc

    def _cociente(self, pares):
        """Media por canal de s_nadir / s_cenit (normalizados con oscuridad, ganancia y t_int).
        Sin cenit, solo s_nadir: los indices quedan sin correccion por cambios de luz."""
        r = {n: [] for n in ce.NOMBRES}
        for dn, dz in pares:
            sn = ce.normalizar(dn, self.osc["nadir"])[0]
            sz = ce.normalizar(dz, self.osc["zenit"])[0] if dz else {n: 1.0 for n in ce.NOMBRES}
            for n in ce.NOMBRES:
                if sz[n] > 0:
                    r[n].append(sn[n] / sz[n])
        media = {n: st.mean(v) for n, v in r.items() if v}
        cv_nir = ce.cv(r[C_NIR]) if len(r[C_NIR]) > 1 else None
        luz = [ce.normalizar(dz, self.osc["zenit"])[0][C_NIR] for _, dz in pares if dz]
        return media, cv_nir, (st.mean(luz) if luz else None)

    def _con_cenit(self):
        return self.simulado or self.zenit is not None

    def _hora_rtc(self):
        try:
            return self.reloj.hora() if self.reloj else ""
        except Exception:
            return ""

    def _distancia(self):
        if self.simulado:
            d = self.sim.distancia()
        elif self.lidar:
            try:
                d = self.lidar.leer(self.cfg["lidar_lecturas"])
            except (OSError, RuntimeError):
                d = None
        else:
            return None
        return None if d is None else self.cfg["lidar_cal_a"] * d + self.cfg["lidar_cal_b"]

    # --- pasos de la interfaz ---
    def tomar_blanco(self, progreso=lambda f, txt: None):
        with self.lock:
            if self.simulado:
                self.sim.superficie = "blanco"
            pares, desc = self._pares(self.cfg["pares_blanco"], progreso)
            if len(pares) < max(3, self.cfg["pares_blanco"] // 2):
                raise RuntimeError(f"Solo {len(pares)} pares validos sobre el blanco ({desc}). "
                                   "Revisa el cenit y la saturacion y repite.")
            media, cv_nir, luz = self._cociente(pares)
            self.sesion["blanco"] = {"cociente": media, "hora": datetime.now().isoformat(timespec="seconds"),
                                     "t": time.time(), "pares": len(pares), "cv_nir_pct": redondear(cv_nir, 3),
                                     "luz_cenit_nir": luz, "con_cenit": self._con_cenit()}
            self._guardar_sesion()
            return {"pares": len(pares), "cv_nir_pct": redondear(cv_nir, 3), "descartados": desc,
                    "con_cenit": self._con_cenit()}

    def tomar_suelo(self, progreso=lambda f, txt: None, manual_cm=None):
        with self.lock:
            if manual_cm is not None:
                d = float(manual_cm)
            else:
                if self.simulado:
                    self.sim.superficie = "suelo"
                progreso(0.3, "Midiendo la distancia al suelo")
                d = self._distancia()
                if d is None:
                    raise RuntimeError("El LiDAR no respondio.")
            self.sesion["suelo_cm"] = round(d, 1)
            self.sesion["suelo_manual"] = manual_cm is not None
            self._guardar_sesion()
            return {"suelo_cm": round(d, 1)}

    def medir(self, punto="", nota="", hora_celular="", progreso=lambda f, txt: None):
        with self.lock:
            avisos = []
            b = self.sesion.get("blanco")
            if not b:
                raise RuntimeError("Primero toma la referencia blanca en Inicio.")
            if b.get("con_cenit", True) != self._con_cenit():
                raise RuntimeError("El blanco se tomo " + ("con" if b.get("con_cenit", True) else "sin") +
                                   " el cenit y ahora " + ("si" if self._con_cenit() else "no") +
                                   " esta conectado: repite el blanco.")
            if not self._con_cenit():
                avisos.append("sin cenit: indices sin correccion de luz")
            if self.simulado:
                self.sim.superficie = "pasto"
                self.sim.nuevo_punto()
            fila = {"id": self._siguiente_id(), "punto": punto, "nota": nota, "hora_celular": hora_celular,
                    "hora_rpi": datetime.now().isoformat(timespec="seconds"), "simulado": int(self.simulado),
                    "hora_rtc": self._hora_rtc(),
                    "blanco_hora": b["hora"], "pares_pedidos": self.cfg["pares_medicion"],
                    "con_cenit": int(self._con_cenit())}
            edad = (time.time() - b["t"]) / 60
            if edad > self.cfg["blanco_vigencia_min"]:
                avisos.append(f"blanco de hace {edad:.0f} min")

            # 1. espectro
            pares, desc = self._pares(self.cfg["pares_medicion"], lambda f, t: progreso(0.6 * f, t))
            fila["pares_validos"] = len(pares)
            if desc["saturado"]:
                avisos.append(f"{desc['saturado']} lecturas saturadas")
            if desc["sin_cenit"]:
                avisos.append(f"{desc['sin_cenit']} lecturas sin cenit")
            if pares:
                media, cv_nir, luz = self._cociente(pares)
                rho = {n: media[n] / b["cociente"][n] for n in (C_ROJO, C_F7, C_F8, C_NIR)
                       if n in media and b["cociente"].get(n)}
                fila.update(rho_f6=rho.get(C_ROJO), rho_f7=rho.get(C_F7), rho_f8=rho.get(C_F8),
                            rho_nir=rho.get(C_NIR), cv_cociente_nir_pct=cv_nir,
                            luz_relativa_blanco=luz / b["luz_cenit_nir"] if luz and b.get("luz_cenit_nir") else None)
                fila["ndvi"] = indice(rho.get(C_NIR), rho.get(C_ROJO))
                fila["ndre1"] = indice(rho.get(C_NIR), rho.get(C_F8))
                fila["ndre2"] = indice(rho.get(C_F8), rho.get(C_F7))
                fila["ganancia_nadir"] = "/".join(sorted({f"{dn['ganancia_x']:g}" for dn, _ in pares}))
                fila["ganancia_cenit"] = "/".join(sorted({f"{dz['ganancia_x']:g}" for _, dz in pares if dz}))
                temps = [dn["temp_c"] for dn, _ in pares if dn.get("temp_c") is not None]
                fila["temp_c"] = st.mean(temps) if temps else None
                if len(pares) < self.cfg["pares_medicion"]:
                    avisos.append(f"solo {len(pares)} de {self.cfg['pares_medicion']} pares validos")
            else:
                avisos.append("sin pares validos: no hay indices")

            # 2. altura
            progreso(0.7, "Altura (LiDAR)")
            d = self._distancia()
            fila["distancia_lidar_cm"] = d
            suelo = self.sesion.get("suelo_cm")
            fila["suelo_cm"] = suelo
            if d is not None and suelo is not None:
                fila["altura_cm"] = max(0.0, suelo - d)
            elif d is None:
                avisos.append("sin LiDAR")
            else:
                avisos.append("sin distancia al suelo: altura no calculada")

            # 3. inclinacion
            progreso(0.8, "Inclinacion")
            try:
                inc = self.sim.inclinacion() if self.simulado else (self.imu.inclinacion() if self.imu else None)
            except OSError:
                inc = None
                avisos.append("el inclinometro no respondio")
            fila["inclinacion_deg"] = inc
            if inc is not None and inc > self.cfg["inclinacion_max_deg"]:
                avisos.append(f"baston inclinado {inc:.1f} grados")

            # 4. foto
            progreso(0.85, "Foto (unos 3 s)")
            archivo = os.path.join(CARPETA, "fotos", f"medicion_{fila['id']:04d}.jpg")
            cam = self.sim if self.simulado else self.camara
            foto = cam.foto(archivo) if cam else None
            fila["foto"] = os.path.basename(foto) if foto else ""

            # 5. biomasa
            progreso(0.95, "Biomasa")
            if self.modelo and fila.get("ndvi") is not None and fila.get("altura_cm") is not None:
                try:
                    fila["biomasa_kg_ms_ha"] = self.modelo.estimar(fila["ndvi"], fila["altura_cm"])
                except Exception as e:
                    avisos.append(f"modelo: {type(e).__name__}")
            elif not self.modelo:
                avisos.append("modelo no cargado")

            fila["avisos"] = "; ".join(avisos)
            fila = {k: redondear(v) for k, v in fila.items()}
            self._guardar_fila(fila, pares)
            progreso(1.0, "Listo")
            return fila

    # --- archivos ---
    def archivo_csv(self):
        return os.path.join(CARPETA, f"mediciones_{datetime.now():%Y%m%d}.csv")

    def _siguiente_id(self):
        n = 0
        for a in os.listdir(CARPETA):
            if a.startswith("mediciones_") and a.endswith(".csv"):
                with open(os.path.join(CARPETA, a)) as f:
                    for r in csv.DictReader(f):
                        try:
                            n = max(n, int(r["id"]))
                        except (KeyError, ValueError):
                            pass
        return n + 1

    def _guardar_fila(self, fila, pares):
        ruta = self.archivo_csv()
        nuevo = not os.path.exists(ruta)
        with open(ruta, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
            if nuevo:
                w.writeheader()
            w.writerow(fila)
        # cuentas crudas de cada par, para revisar despues
        crudo = os.path.join(CARPETA, f"crudo_{datetime.now():%Y%m%d}.csv")
        campos = ["id", "par"] + ["n_" + c for c in ce.CAMPOS_MOD] + ["z_" + c for c in ce.CAMPOS_MOD + ce.CAMPOS_Z]
        nuevo = not os.path.exists(crudo)
        with open(crudo, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            if nuevo:
                w.writeheader()
            for i, (dn, dz) in enumerate(pares):
                r = {"id": fila["id"], "par": i}
                r.update({"n_" + k: v for k, v in dn.items()})
                r.update({"z_" + k: v for k, v in (dz or {}).items()})
                w.writerow(r)

    def mediciones(self):
        filas = []
        for a in sorted(os.listdir(CARPETA)):
            if a.startswith("mediciones_") and a.endswith(".csv"):
                with open(os.path.join(CARPETA, a)) as f:
                    filas += list(csv.DictReader(f))
        return filas

    def estado(self):
        b = self.sesion.get("blanco")
        return {"simulado": self.simulado, "sensores": self.estado_sensores,
                "blanco": None if not b else {"hora": b["hora"], "pares": b["pares"],
                                              "cv_nir_pct": b.get("cv_nir_pct"), "con_cenit": b.get("con_cenit", True),
                                              "edad_min": round((time.time() - b["t"]) / 60, 1)},
                "suelo_cm": self.sesion.get("suelo_cm"), "suelo_manual": self.sesion.get("suelo_manual"),
                "hora_rpi": datetime.now().isoformat(timespec="seconds"),
                "config": {k: self.cfg[k] for k in ("pares_medicion", "pares_blanco", "inclinacion_max_deg")}}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--simulado", action="store_true", help="sin sensores, con datos sinteticos")
    p.add_argument("--suelo", type=float, help="distancia del LiDAR al suelo en cm (si no, se mide)")
    a = p.parse_args()
    d = Dispositivo(simulado=a.simulado)
    for n, e in d.estado_sensores.items():
        print(f"{n:13s} {'OK ' if e['ok'] else 'NO '} {e['detalle']}")
    input("\nPon el blanco (PTFE) bajo el nadir y presiona Enter...")
    print(d.tomar_blanco(lambda f, t: print(" ", t)))
    if a.suelo is None:
        input("Apunta el sensor al suelo desnudo y presiona Enter...")
    print(d.tomar_suelo(lambda f, t: print(" ", t), manual_cm=a.suelo))
    while input("\nPon el sensor sobre el pasto y presiona Enter (q para salir)... ").strip().lower() != "q":
        fila = d.medir(progreso=lambda f, t: print(" ", t))
        for k in ("ndvi", "ndre2", "altura_cm", "inclinacion_deg", "biomasa_kg_ms_ha", "avisos"):
            print(f"  {k:18s} {fila.get(k)}")
    print(f"\nDatos: {d.archivo_csv()}")


if __name__ == "__main__":
    main()
