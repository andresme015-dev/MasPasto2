"""Caracterizacion de los dos AS7343 (nadir en la Raspberry, zenit en el ESP32).

Modos (Etapa 1 y Etapa 2 del informe):

  registro          Ganancia adaptativa en los dos modulos (o en uno con --modulo).
                    Sirve para ver que ganancias usa cada sensor al sol y a la sombra, y para
                    comprobar si la lampara esta estable (CV y deriva por canal al final).
                    python3 caracterizacion_espectro.py registro --etiqueta sol --n 30
                    python3 caracterizacion_espectro.py registro --modulo nadir --etiqueta estabilidad --n 300

  ganancias         Bajo la lampara, ganancias fijas en un modulo: ida (de menor a mayor)
                    y vuelta (de mayor a menor), --n lecturas por ganancia en cada pasada.
                    Al final pide tapar el sensor y toma la lectura oscura de cada ganancia,
                    que queda guardada y se resta en los demas modos.
                    python3 caracterizacion_espectro.py ganancias --modulo nadir --ganancias 2,4,8

  oscuridad         Lampara apagada y sensor tapado: lectura oscura a ganancias fijas.
                    python3 caracterizacion_espectro.py oscuridad --modulo zenit --sensor A --ganancias 0.5,1,2,4,8,16,32,64

  Opciones comunes: --sensor-nadir A (sensor fisico en la Raspberry; el del zenit lo envia el
  firmware), --sensor A para un solo modulo, y --config (montaje). La oscuridad se guarda por
  sensor (oscuridad_A.json, oscuridad_B.json). Todo queda en el nombre del archivo y en el CSV.
  --modulo ambos en "oscuridad" y "ganancias" mide los dos sensores a la vez; la prueba de
  ganancias da ademas k a cada ganancia.

  intercomparacion  Los dos sensores uno al lado del otro bajo la misma luz; luego se
                    intercambian de posicion. Calcula k = s_zenit / s_nadir por canal y su CV.
                    Con --ganancia los dos sensores usan la misma ganancia fija (primera prueba).
                    python3 caracterizacion_espectro.py intercomparacion --ganancia 4 --n 20

  saturacion        Barrido de ganancia de menor a mayor hasta que el modulo satura: da la
                    ganancia mas alta segura con la luz del momento y la senal normalizada como
                    medida relativa de la luz. Repetir en sol, nubes, sombra y con la lampara
                    a varias distancias (saturacion del cenit con PTFE frente a la irradiancia).
                    python3 caracterizacion_espectro.py saturacion --modulo zenit --etiqueta sol_pleno

  ptfe              El sensor de --modulo (zenit por defecto) alterna sin PTFE y con la pieza
                    de la misma lamina encima. Calcula T_d = s_con / s_sin por canal. El otro
                    modulo, si esta disponible, se usa como referencia de la luz.
                    python3 caracterizacion_espectro.py ptfe --repeticiones 3 --n 10

Cada corrida guarda un CSV en ~/maspasto2/datos_espectro/ (cuentas crudas de cada lectura) y
otro con el resumen. Solo lee sensores y escribe archivos en esa carpeta; no cambia nada
del sistema ni de la red.
"""
import argparse
import csv
import json
import math
import os
import socket
import statistics as st
import threading
import time
from collections import deque
from datetime import datetime

CARPETA = os.path.expanduser("~/maspasto2/datos_espectro")
NOMBRES = ["f1_405nm", "f2_425nm", "fz_450nm", "f3_475nm", "f4_515nm", "f5_550nm",
           "fy_555nm", "fxl_600nm", "f6_640nm", "f7_690nm", "f8_745nm", "nir_855nm"]
VIS = ["vis_c1", "vis_c2", "vis_c3"]
TECHO = 65535
LIM_SAT = int(0.90 * TECHO)   # saturacion: canal mas alto de los 18 (VIS incluido) >= 90 %
CAMPOS_MOD = (["t", "ganancia_idx", "ganancia_x", "t_int_ms", "max_espectral", "max_cuentas",
               "saturado", "vis_saturado", "sat_analogica", "sat_digital"] + NOMBRES + VIS +
              ["var_luz_ciclos", "temp_c"])
CAMPOS_Z = ["seq", "rssi_dbm", "desfase_s", "id_sensor", "config"]


def gan_x(i):
    return 2.0 ** (i - 1)


def idx_de_x(x):
    i = round(math.log2(float(x)) + 1)
    if not 0 <= i <= 12 or abs(gan_x(i) - float(x)) > 1e-9:
        raise ValueError(f"ganancia {x} no valida (0.5, 1, 2, 4, ..., 2048)")
    return i


def max_esp(d):
    """Cuentas del canal espectral mas alto (informativo)."""
    return d.get("max_espectral", max(d[n] for n in NOMBRES))


def max_tot(d):
    """Cuentas del canal mas alto de los 18, VIS incluido (criterio de saturacion)."""
    return d.get("max_cuentas", max_esp(d))


def var_vis(d):
    if d.get("vis_saturado"):
        return None                       # con el VIS saturado no se puede verificar
    v = [d.get(k) for k in VIS]
    if None in v or min(v) <= 0:
        return None
    return max(v) / min(v) - 1


# ----------------------------------------------------------------------------------
# Lectura oscura guardada por ganancia (se resta antes de normalizar)
# ----------------------------------------------------------------------------------
SENSORES = {"nadir": "", "zenit": ""}   # sensor fisico en cada modulo, p. ej. A y B
CONFIG = ""      # configuracion del montaje (--config), p. ej. "desnudo" o "capsula_ptfe"


def etiqueta_sensores(modulos):
    return ",".join(SENSORES[m] for m in modulos if SENSORES.get(m))


def _archivo_osc(modulo):
    """La lectura oscura es propia de cada sensor fisico: si se conoce el sensor del modulo
    (--sensor, --sensor-nadir/--sensor-zenit o el id que envia el zenit), el archivo lleva
    su nombre (oscuridad_A.json); si no, el del modulo (oscuridad_nadir.json)."""
    s = SENSORES.get(modulo)
    return os.path.join(CARPETA, f"oscuridad_{s or modulo}.json")


def cargar_osc(modulo):
    try:
        with open(_archivo_osc(modulo)) as f:
            return {int(k): v for k, v in json.load(f).items()}
    except (OSError, ValueError):
        return {}


def guardar_osc(modulo, nuevos):
    osc = cargar_osc(modulo)
    osc.update(nuevos)
    with open(_archivo_osc(modulo), "w") as f:
        json.dump({str(k): v for k, v in sorted(osc.items())}, f, indent=1)


def normalizar(d, osc):
    """s = (S - S_osc) / (G * t_int). Devuelve (dict por canal, se_resto_oscuridad)."""
    o = osc.get(int(d["ganancia_idx"]))
    den = d["ganancia_x"] * d["t_int_ms"]
    return ({n: (d[n] - (o[n] if o else 0.0)) / den for n in NOMBRES}, o is not None)


# ----------------------------------------------------------------------------------
# Modulo nadir (AS7343 en el I2C de la Raspberry)
# ----------------------------------------------------------------------------------
class Nadir:
    def __init__(self):
        import test_as7343 as t          # requiere adafruit-circuitpython-as7343
        self.t = t
        self.dur = 0.56                   # duracion tipica de una lectura (3 ciclos), se actualiza
        t.iniciar()
        self.bmp = None                   # BMP280 (0x76): temperatura en cada lectura (E1/E3)
        try:
            import test_bmp280
            test_bmp280.leer_bmp280()
            self.bmp = test_bmp280.leer_bmp280
        except Exception as e:            # sin BMP280 se sigue midiendo, con temp_c vacia
            print(f"Aviso: sin BMP280 ({type(e).__name__}); no se registrara la temperatura.")

    def leer(self, idx=None):
        d = self.t.leer_as7343(ganancia=idx)
        d["t_fin"] = time.time()
        self.dur = 0.7 * self.dur + 0.3 * (d["t_fin"] - d["t_lectura"])
        d["t"] = d["t_lectura"]
        if self.bmp:
            try:
                d["temp_c"] = self.bmp()["temperatura_c"]
            except Exception:
                pass
        return d


# ----------------------------------------------------------------------------------
# Modulo zenit (paquetes UDP del ESP32; ordenes de ganancia por el puerto 5006)
# ----------------------------------------------------------------------------------
class Zenit:
    def __init__(self):
        from receptor_zenit import _socket, enviar_orden_zenit
        self._enviar = enviar_orden_zenit
        self.sock = _socket()
        self.sock.settimeout(0.5)
        self.paq = deque(maxlen=60)       # (hora de llegada, paquete)
        self.lock = threading.Lock()
        self.ip = None
        self.usado = None                 # seq del ultimo paquete emparejado
        threading.Thread(target=self._bucle, daemon=True).start()

    def _bucle(self):
        while True:
            try:
                datos, origen = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            try:
                p = json.loads(datos.decode())
            except ValueError:
                continue
            if p.get("sensor") != "AS7343":
                continue                  # firmware viejo (AS7341)
            p["t"] = time.time()
            if "max_espectral" not in p:          # firmware anterior
                p["max_espectral"] = max_esp(p)
            p["var_luz_ciclos"] = var_vis(p)
            if not SENSORES["zenit"] and p.get("id_sensor"):
                SENSORES["zenit"] = str(p["id_sensor"])      # lo informa el firmware
            with self.lock:
                self.paq.append((p["t"], p))
                self.ip = origen[0]

    def esperar_conexion(self, timeout=15):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.ip:
                return True
            time.sleep(0.2)
        return False

    def siguiente(self, desde, cond=lambda p: True, timeout=6.0):
        """Primer paquete que llega despues de 'desde' y cumple 'cond'."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            with self.lock:
                for t, p in self.paq:
                    if t > desde and cond(p):
                        return p
            time.sleep(0.05)
        return None

    def emparejar(self, t_fin, timeout=3.0):
        """Paquete cuya lectura termina mas cerca de t_fin (fin de la lectura del nadir).
        El ESP32 envia apenas termina de leer, asi que la hora de llegada marca el fin."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            with self.lock:
                if any(t >= t_fin for t, _ in self.paq):
                    cand = [(abs(t - t_fin), p) for t, p in self.paq
                            if t >= t_fin - 1.5 and p.get("seq") != self.usado]
                    p = dict(min(cand, key=lambda c: c[0])[1])
                    self.usado = p.get("seq")
                    p["desfase_s"] = round(p["t"] - t_fin, 3)
                    return p
            time.sleep(0.05)
        return None

    def fijar(self, idx, timeout=12):
        """Fija la ganancia y espera un paquete que la confirme (reenvia si se pierde)."""
        t_ini = time.time()
        while time.time() - t_ini < timeout:
            t_envio = time.time()
            self._enviar(f"G{idx}", self.ip)
            p = self.siguiente(t_envio, lambda q: q.get("ganancia_fija") and
                               q.get("ganancia_idx") == idx, timeout=2.5)
            if p:
                return True
        return False

    def adaptativa(self):
        if self.ip:
            for _ in range(3):
                self._enviar("GA", self.ip)
                time.sleep(0.1)

    def leer(self, idx=None, desde=None):
        desde = time.time() if desde is None else desde
        if idx is None:
            return self.siguiente(desde)
        return self.siguiente(desde, lambda q: q.get("ganancia_idx") == idx and q.get("ganancia_fija"))


# ----------------------------------------------------------------------------------
# Archivos
# ----------------------------------------------------------------------------------
class Registro:
    def __init__(self, modo, etiqueta, modulos):
        os.makedirs(CARPETA, exist_ok=True)
        sello = datetime.now().strftime("%Y%m%d_%H%M%S")
        sens = etiqueta_sensores(modulos)
        self.sensores = sens
        partes = [modo] + [x for x in (sens and "sensor" + sens.replace(",", "-"), CONFIG, etiqueta)
                           if x] + [sello]
        nombre = "_".join(partes)
        self.base = os.path.join(CARPETA, nombre)
        campos = ["modo", "sensor_id", "config", "etiqueta", "fase", "pasada", "rep"]
        for m in modulos:
            pre = m[0] + "_"
            campos += [pre + c for c in CAMPOS_MOD]
            if m == "zenit":
                campos += [pre + c for c in CAMPOS_Z]
        self.f = open(self.base + ".csv", "w", newline="")
        self.w = csv.DictWriter(self.f, fieldnames=campos, extrasaction="ignore")
        self.w.writeheader()
        self.modo, self.etiqueta = modo, etiqueta

    def fila(self, fase="", pasada="", rep="", **lecturas):
        r = {"modo": self.modo, "sensor_id": self.sensores, "config": CONFIG, "etiqueta": self.etiqueta,
             "fase": fase, "pasada": pasada, "rep": rep}
        for m, d in lecturas.items():
            if d is None:
                continue
            for c in CAMPOS_MOD + CAMPOS_Z:
                if c in d:
                    v = d[c]
                    r[m[0] + "_" + c] = round(v, 6) if isinstance(v, float) else v
        self.w.writerow(r)
        self.f.flush()

    def resumen(self, filas, campos):
        with open(self.base + "_resumen.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(filas)
        print(f"\nDatos:   {self.base}.csv\nResumen: {self.base}_resumen.csv")

    def cerrar(self):
        self.f.close()


def cv(x):
    return st.stdev(x) / abs(st.mean(x)) * 100 if len(x) > 1 and st.mean(x) != 0 else float("nan")


def linea(d, nombre):
    if d is None:
        return f"{nombre}: sin dato"
    m = max_tot(d)
    return (f"{nombre}: G {d['ganancia_x']:g}x  max {m} ({m / TECHO * 100:4.1f} %)  "
            f"NIR {d['nir_855nm']}  F6 {d['f6_640nm']}"
            f"{'  VIS sat' if d.get('vis_saturado') else ''}{'  SATURADO' if d['saturado'] else ''}")


def abrir(modulo, obligatorio=True):
    if modulo == "nadir":
        return Nadir()
    z = Zenit()
    print("Esperando paquetes del zenit (firmware AS7343)...")
    if z.esperar_conexion():
        print(f"Zenit conectado desde {z.ip}")
        return z
    if obligatorio:
        raise SystemExit("No llegan paquetes del zenit: revisa que el ESP32 este encendido, "
                         "conectado a la red de la Raspberry y con el firmware AS7343.")
    print("Zenit no disponible: se continua sin el.")
    return None


# ----------------------------------------------------------------------------------
# Modos
# ----------------------------------------------------------------------------------
def modo_registro(a):
    mods = ["nadir", "zenit"] if a.modulo == "ambos" else [a.modulo]
    sen = {m: abrir(m, obligatorio=(a.modulo != "ambos" or m == "nadir")) for m in mods}
    mods = [m for m in mods if sen[m] is not None]
    idx = idx_de_x(a.ganancia) if a.ganancia else None
    if "zenit" in mods:
        if idx is None:
            sen["zenit"].adaptativa()
        elif not sen["zenit"].fijar(idx):
            raise SystemExit("El zenit no confirmo la ganancia: revisa la conexion.")
    if idx is not None:
        print(f"Ganancia fija {gan_x(idx):g}x")
    reg = Registro("registro", a.etiqueta, mods)
    usadas = {m: [] for m in mods}
    datos = {m: [] for m in mods}
    try:
        for i in range(a.n):
            if "nadir" in mods:
                if "zenit" in mods:
                    dn, dz = leer_par(sen["nadir"], sen["zenit"], idx)
                else:
                    dn, dz = sen["nadir"].leer(idx), None
            else:
                dn, dz = None, sen["zenit"].leer(idx)
                if dz is None:
                    print("  sin paquete del zenit")
                    continue
            reg.fila(rep=i, nadir=dn, zenit=dz)
            for m, d in (("nadir", dn), ("zenit", dz)):
                if d is not None and m in datos:
                    usadas[m].append(d["ganancia_x"])
                    datos[m].append(d)
            print(f"[{i + 1}/{a.n}] " + " | ".join(linea(d, m) for m, d in (("nadir", dn), ("zenit", dz))
                                                    if m in mods))
    except KeyboardInterrupt:
        print("\nDetenido.")
    finally:
        if "zenit" in mods and idx is not None:
            sen["zenit"].adaptativa()
    reg.cerrar()
    filas = []
    for m in mods:
        lect = [d for d in datos[m] if not d["saturado"]]
        gtxt = ", ".join(f"{g:g}x: {usadas[m].count(g)}" for g in sorted(set(usadas[m])))
        print(f"\n{m}: ganancias usadas ({gtxt}); {len(datos[m]) - len(lect)} lecturas saturadas")
        seqs = [d["seq"] for d in datos[m] if "seq" in d]
        if m == "zenit" and len(seqs) > 1 and "nadir" not in mods:
            esperados = seqs[-1] - seqs[0] + 1
            print(f"  enlace Wi-Fi: {len(seqs)} paquetes recibidos de {esperados} enviados "
                  f"({(1 - len(seqs) / esperados) * 100:.1f} % perdidos)")
        if len(lect) < 5:
            continue
        osc = cargar_osc(m)
        k = max(1, len(lect) // 5)          # primer y ultimo quinto de la corrida
        dur = lect[-1]["t"] - lect[0]["t"]
        print(f"  {len(lect)} lecturas en {dur / 60:.1f} min.  CV = variacion entre lecturas;"
              f"  deriva = ultimo quinto / primer quinto - 1")
        for n in NOMBRES:
            v = [normalizar(d, osc)[0][n] for d in lect]
            der = (st.mean(v[-k:]) / st.mean(v[:k]) - 1) * 100 if st.mean(v[:k]) else float("nan")
            fila = {"modulo": m, "canal": n, "lecturas": len(v), "duracion_min": round(dur / 60, 2),
                    "cv_pct": round(cv(v), 2), "deriva_pct": round(der, 2), "ganancias": gtxt}
            filas.append(fila)
            print(f"  {n:10s} CV {fila['cv_pct']:5.2f} %   deriva {fila['deriva_pct']:+6.2f} %")
    if filas:
        reg.resumen(filas, list(filas[0].keys()))


def modo_ganancias(a):
    if not a.ganancias:
        raise SystemExit("Indica las ganancias, por ejemplo --ganancias 2,4,8")
    gans = sorted(idx_de_x(x) for x in a.ganancias.split(","))
    sen = abrir(a.modulo)
    reg = Registro("ganancias", a.etiqueta or a.modulo, [a.modulo])
    luz = {g: [] for g in gans}            # lecturas sin saturar por ganancia
    pasadas = {g: {"ida": [], "vuelta": []} for g in gans}
    n_sat = {g: 0 for g in gans}
    n_vis = {g: 0 for g in gans}          # lecturas validas con el VIS saturado

    def tomar(g, fase, pasada, n, destino=None):
        if a.modulo == "zenit" and not sen.fijar(g):
            raise SystemExit("El zenit no confirmo la ganancia: revisa la conexion.")
        if a.modulo == "nadir":
            sen.leer(g)                    # se descarta la primera lectura tras el cambio
            desde = None
        else:
            desde = time.time()
            sen.leer(g, desde)             # se descarta el primer paquete confirmado
            desde = time.time()
        for i in range(n):
            if a.modulo == "nadir":
                d = sen.leer(g)
            else:
                d = sen.leer(g, desde)
                if d is None:
                    raise SystemExit("Se dejaron de recibir paquetes del zenit.")
                desde = d["t"]
            reg.fila(fase=fase, pasada=pasada, rep=i, **{a.modulo: d})
            print(f"  {fase} {pasada} {gan_x(g):g}x [{i + 1}/{n}] {linea(d, a.modulo)}")
            if destino is not None:
                destino.append(d)

    try:
        input(f"\nLUZ: sensor {a.modulo} bajo la lampara (ya encendida y estable). Enter para empezar...")
        orden = [("ida", gans), ("vuelta", gans[::-1])]
        for pasada, lista in orden:
            for g in lista:
                buf = []
                tomar(g, "luz", pasada, a.n, buf)
                for d in buf:
                    if d["saturado"]:
                        n_sat[g] += 1
                    else:
                        luz[g].append(d)
                        pasadas[g][pasada].append(d)
                        n_vis[g] += bool(d.get("vis_saturado"))
        if a.sin_oscuridad:
            osc = cargar_osc(a.modulo)       # la del modo oscuridad (no se apaga la lampara)
            falta = [gan_x(g) for g in gans if g not in osc]
            print(f"\nSe usa la oscuridad guardada en {_archivo_osc(a.modulo)}"
                  + (f"; FALTA para {falta} (no se resta)" if falta else ""))
        else:
            input("\nOSCURIDAD: APAGA la lampara y tapa el sensor con la caja negra (sin moverlo). "
                  "Enter para seguir...")
            osc = {}
            for g in gans:
                buf = []
                tomar(g, "oscuridad", "", a.n_osc, buf)
                osc[g] = {n: st.mean(d[n] for d in buf) for n in NOMBRES}
            guardar_osc(a.modulo, osc)
            print(f"Lectura oscura guardada en {_archivo_osc(a.modulo)}")
    finally:
        if a.modulo == "zenit":
            sen.adaptativa()
        reg.cerrar()

    # --- analisis ---
    validas = [g for g in gans if luz[g]]
    if not validas:
        raise SystemExit("Todas las lecturas saturaron: baja las ganancias o aleja la lampara.")
    ref = validas[len(validas) // 2]
    s = {g: {n: st.mean(normalizar(d, osc)[0][n] for d in luz[g]) for n in NOMBRES} for g in validas}
    filas = []
    print(f"\nReferencia: {gan_x(ref):g}x.  desv = s_G / s_ref - 1;  deriva = vuelta / ida - 1")
    for g in gans:
        frac = [max_tot(d) / TECHO * 100 for d in luz[g]]
        aviso = ""
        if n_sat[g]:
            aviso = f"  {n_sat[g]} lecturas saturadas excluidas"
        if frac and not (10 <= min(frac) and max(frac) <= 90):
            aviso += "  canal mas alto fuera de 10-90 %"
        if n_vis[g]:
            aviso += f"  (VIS saturado en {n_vis[g]} lecturas validas)"
        print(f"\n{gan_x(g):g}x  canal mas alto (con VIS) {min(frac, default=0):.0f}-"
              f"{max(frac, default=0):.0f} % del techo{aviso}")
        if g not in validas:
            continue
        for n in NOMBRES:
            vals = [normalizar(d, osc)[0][n] for d in luz[g]]
            ida = [normalizar(d, osc)[0][n] for d in pasadas[g]["ida"]]
            vue = [normalizar(d, osc)[0][n] for d in pasadas[g]["vuelta"]]
            desv = (s[g][n] / s[ref][n] - 1) * 100 if s[ref][n] else float("nan")
            der = (st.mean(vue) / st.mean(ida) - 1) * 100 if ida and vue and st.mean(ida) else float("nan")
            fila = {"modulo": a.modulo, "ganancia_x": gan_x(g), "canal": n,
                    "cuentas_media": round(st.mean(d[n] for d in luz[g]), 1),
                    "oscuridad": round(osc[g][n], 1), "s_norm": round(s[g][n], 6),
                    "cv_pct": round(cv(vals), 2), "desv_vs_ref_pct": round(desv, 2),
                    "deriva_ida_vuelta_pct": round(der, 2), "lecturas": len(vals),
                    "saturadas": n_sat[g], "vis_saturado": n_vis[g]}
            filas.append(fila)
            print(f"  {n:10s} cuentas {fila['cuentas_media']:8.0f}  osc {fila['oscuridad']:6.1f}  "
                  f"CV {fila['cv_pct']:5.2f} %  desv {fila['desv_vs_ref_pct']:+6.2f} %  "
                  f"deriva {fila['deriva_ida_vuelta_pct']:+6.2f} %")
    reg.resumen(filas, list(filas[0].keys()))

    # --- pasos consecutivos: robusto a que la luz cambie lentamente durante la prueba ---
    # Compara cada bloque con el bloque medido justo antes. Si la ganancia es lineal, el
    # cociente de senales normalizadas es 1 en los cambios de ganancia; en el paso que
    # repite la ganancia mas alta (fin de la ida, inicio de la vuelta) solo mide la deriva.
    bloques = [("ida", g) for g in gans] + [("vuelta", g) for g in gans[::-1]]
    bloques = [(p, g) for p, g in bloques if pasadas[g][p]]
    media = {(p, g): {n: st.mean(normalizar(d, osc)[0][n] for d in pasadas[g][p]) for n in NOMBRES}
             for p, g in bloques}
    pasos = []
    print("\nPasos consecutivos (cociente de senal normalizada - 1, en %):")
    for (p1, g1), (p2, g2) in zip(bloques, bloques[1:]):
        dif = {n: (media[(p2, g2)][n] / media[(p1, g1)][n] - 1) * 100
               for n in NOMBRES if media[(p1, g1)][n]}
        tipo = "deriva (misma ganancia)" if g1 == g2 else "cambio de ganancia"
        absd = sorted(abs(x) for x in dif.values())
        print(f"  {p1} {gan_x(g1):g}x -> {p2} {gan_x(g2):g}x  [{tipo}]  mediana |dif| "
              f"{st.median(absd):.2f} %  maxima {absd[-1]:.2f} %")
        fila = {"de": f"{p1} {gan_x(g1):g}x", "a": f"{p2} {gan_x(g2):g}x", "tipo": tipo}
        fila.update({n: round(dif.get(n, float("nan")), 2) for n in NOMBRES})
        pasos.append(fila)
    if pasos:
        with open(reg.base + "_pasos.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(pasos[0].keys()))
            w.writeheader()
            w.writerows(pasos)
        print(f"Pasos:   {reg.base}_pasos.csv")


def modo_oscuridad(a):
    """Lectura oscura con la lampara APAGADA y el sensor tapado, a ganancias fijas.
    Con --modulo ambos mide los dos sensores (uno despues del otro)."""
    if not a.ganancias:
        raise SystemExit("Indica las ganancias, por ejemplo --ganancias 0.5,1,2,4,8,16,32,64")
    gans = sorted(idx_de_x(x) for x in a.ganancias.split(","))
    mods = ["nadir", "zenit"] if a.modulo == "ambos" else [a.modulo]
    sen = {m: abrir(m) for m in mods}
    reg = Registro("oscuridad", a.etiqueta, mods)
    osc = {m: {} for m in mods}
    try:
        input("\nOSCURIDAD: lampara APAGADA y sensor(es) tapado(s) con la caja negra, sin "
              "moverlos. Enter para empezar...")
        for m in mods:
            for g in gans:
                if m == "zenit":
                    if not sen[m].fijar(g):
                        raise SystemExit("El zenit no confirmo la ganancia: revisa la conexion.")
                    desde = time.time()
                    sen[m].leer(g, desde)                  # descarta el primer paquete
                    desde = time.time()
                else:
                    sen[m].leer(g)                         # descarta la primera lectura
                buf = []
                for i in range(a.n):
                    if m == "zenit":
                        d = sen[m].leer(g, desde)
                        if d is None:
                            raise SystemExit("Se dejaron de recibir paquetes del zenit.")
                        desde = d["t"]
                    else:
                        d = sen[m].leer(g)
                    reg.fila(fase="oscuridad", rep=i, **{m: d})
                    buf.append(d)
                osc[m][g] = {n: st.mean(d[n] for d in buf) for n in NOMBRES}
                print(f"  {m} ({SENSORES[m] or '?'}) {gan_x(g):g}x: canal espectral oscuro mas alto "
                      f"{max(osc[m][g].values()):.1f} cuentas (media de {a.n})")
            guardar_osc(m, osc[m])
            print(f"Lectura oscura guardada en {_archivo_osc(m)}")
    finally:
        if "zenit" in mods:
            sen["zenit"].adaptativa()
        reg.cerrar()
    filas = [{"modulo": m, "sensor": SENSORES[m], "ganancia_x": gan_x(g),
              **{n: round(v, 2) for n, v in osc[m][g].items()}} for m in mods for g in osc[m]]
    if filas:
        reg.resumen(filas, list(filas[0].keys()))


def modo_ganancias_par(a):
    """Prueba de ganancias en los DOS sensores a la vez (misma ganancia fija en ambos, lecturas
    simultaneas). Da los factores de ganancia de cada sensor y k = zenit/nadir a cada ganancia;
    si k no cambia con la ganancia, los dos sensores tienen los mismos factores."""
    if not a.ganancias:
        raise SystemExit("Indica las ganancias, por ejemplo --ganancias 1,2,4,8")
    gans = sorted(idx_de_x(x) for x in a.ganancias.split(","))
    nadir, zenit = abrir("nadir"), abrir("zenit")
    osc = {m: cargar_osc(m) for m in ("nadir", "zenit")}
    for m in ("nadir", "zenit"):
        falta = [gan_x(g) for g in gans if g not in osc[m]]
        print(f"Oscuridad {m} ({SENSORES[m] or '?'}): {_archivo_osc(m)}"
              + (f"  FALTA para {falta} (no se resta)" if falta else ""))
    reg = Registro("ganancias", a.etiqueta, ["nadir", "zenit"])
    bloques = [("ida", g) for g in gans] + [("vuelta", g) for g in gans[::-1]]
    datos = {}                               # (pasada, g) -> lista de (dn, dz) validos
    excl = {g: 0 for g in gans}
    try:
        input("\nLUZ: los dos sensores bajo la lampara (encendida y estable). Enter para empezar...")
        for pasada, g in bloques:
            if not zenit.fijar(g):
                raise SystemExit("El zenit no confirmo la ganancia: revisa la conexion.")
            leer_par(nadir, zenit, g)                  # descarta el primer par tras el cambio
            buf, i = [], 0
            while i < a.n:
                dn, dz = leer_par(nadir, zenit, g)
                if dz is None:
                    print("  sin paquete del zenit, se repite")
                    continue
                reg.fila(fase="luz", pasada=pasada, rep=i, nadir=dn, zenit=dz)
                i += 1
                ok = (dz.get("ganancia_idx") == g and not dn["saturado"] and not dz["saturado"]
                      and abs(dz.get("desfase_s", 9)) <= DESFASE_MAX)
                if ok:
                    buf.append((dn, dz))
                else:
                    excl[g] += 1
                print(f"  {pasada} {gan_x(g):g}x [{i}/{a.n}] {linea(dn, 'nadir')} | {linea(dz, 'zenit')}"
                      f"{'' if ok else '  (excluida)'}")
            datos[(pasada, g)] = buf
    finally:
        zenit.adaptativa()
        reg.cerrar()

    def media(m, bloque, n):
        v = [normalizar(par[0 if m == "nadir" else 1], osc[m])[0][n] for par in datos[bloque]]
        return st.mean(v) if v else float("nan")

    validas = [g for g in gans if datos.get(("ida", g)) and datos.get(("vuelta", g))]
    if len(validas) < 2:
        raise SystemExit("Muy pocos bloques validos: revisa saturacion, distancia o el enlace.")
    ref = validas[len(validas) // 2]
    canales = [n for n in NOMBRES if n != "f1_405nm"]   # F1 suele tener muy pocas cuentas
    filas = []
    print(f"\nFactores de ganancia (promedio ida y vuelta, que cancela la deriva lineal), "
          f"referencia {gan_x(ref):g}x; mediana de 11 canales (sin F1):")
    for m in ("nadir", "zenit"):
        prom = {g: {n: (media(m, ("ida", g), n) + media(m, ("vuelta", g), n)) / 2 for n in NOMBRES}
                for g in validas}
        for g in validas:
            d = {n: (prom[g][n] / prom[ref][n] - 1) * 100 for n in NOMBRES if prom[ref][n]}
            v = sorted(d[n] for n in canales if n in d)
            print(f"  {m} ({SENSORES[m] or '?'}) {gan_x(g):>4g}x: {st.median(v):+6.2f} %   "
                  f"[{v[0]:+.2f} a {v[-1]:+.2f}]")
            filas.append({"tipo": "factor_ganancia", "modulo": m, "sensor": SENSORES[m],
                          "ganancia_x": gan_x(g), **{n: round(d.get(n, float('nan')), 3) for n in NOMBRES}})
    print("\nk = zenit / nadir a cada ganancia (mediana de 11 canales; deberia ser igual en todas):")
    for g in validas:
        kk = {}
        for n in NOMBRES:
            r = [normalizar(z, osc["zenit"])[0][n] / normalizar(nn, osc["nadir"])[0][n]
                 for b in (("ida", g), ("vuelta", g)) for nn, z in datos[b]
                 if normalizar(nn, osc["nadir"])[0][n] > 0]
            kk[n] = (st.mean(r), cv(r)) if r else (float("nan"), float("nan"))
        km = st.median(kk[n][0] for n in canales)
        cvm = st.median(kk[n][1] for n in canales)
        print(f"  {gan_x(g):>4g}x: k mediana {km:.4f}  CV mediana {cvm:.2f} %   "
              f"NIR {kk['nir_855nm'][0]:.4f}  F8 {kk['f8_745nm'][0]:.4f}  F7 {kk['f7_690nm'][0]:.4f}  "
              f"F6 {kk['f6_640nm'][0]:.4f}   excluidas {excl[g]}")
        filas.append({"tipo": "k", "modulo": "zenit/nadir", "sensor": etiqueta_sensores(["nadir", "zenit"]),
                      "ganancia_x": gan_x(g), **{n: round(kk[n][0], 5) for n in NOMBRES}})
    deriva = []
    for m in ("nadir", "zenit"):
        g = validas[-1]
        v = [(media(m, ("vuelta", g), n) / media(m, ("ida", g), n) - 1) * 100 for n in canales]
        deriva.append(f"{m} {st.median(v):+.2f} %")
    print(f"\nDeriva de la luz en el bloque de {gan_x(validas[-1]):g}x (vuelta/ida): " + ", ".join(deriva))
    reg.resumen(filas, list(filas[0].keys()))


def modo_saturacion(a):
    """Barrido de ganancia de menor a mayor en cada modulo hasta que satura (canal mas alto de
    los 18 >= 90 %). Da la ganancia mas alta que no satura con la luz de ese momento y la senal
    normalizada s = cuentas / (G * t_int) del NIR, F8, F7 y F6 como medida relativa de la luz.
    Repetido en varias condiciones (sol pleno, nubes, sombra, lampara a varias distancias),
    caracteriza la saturacion del sensor con su difusor frente al nivel de irradiancia."""
    gans = sorted(idx_de_x(x) for x in (a.ganancias or "0.5,1,2,4,8,16,32,64,128,256,512,1024,2048").split(","))
    mods = ["zenit", "nadir"] if a.modulo == "ambos" else [a.modulo]
    sen = {m: abrir(m) for m in mods}
    osc = {m: cargar_osc(m) for m in mods}
    reg = Registro("saturacion", a.etiqueta, mods)
    filas = []
    try:
        for m in mods:
            print(f"\n== {m} ({SENSORES[m] or '?'}): barrido {', '.join(f'{gan_x(g):g}x' for g in gans)}")
            for g in gans:
                if m == "zenit" and not sen[m].fijar(g):
                    raise SystemExit("El zenit no confirmo la ganancia: revisa la conexion.")
                sen[m].leer(g)                       # descarta la primera lectura tras el cambio
                ds = []
                while len(ds) < a.n:
                    d = sen[m].leer(g)
                    if d is None:
                        print("  sin paquete del zenit, se repite")
                        continue
                    reg.fila(fase=f"{gan_x(g):g}x", rep=len(ds), **{m: d})
                    ds.append(d)
                pct = [max_tot(d) / TECHO * 100 for d in ds]
                sat = [bool(d["saturado"]) or max_tot(d) >= LIM_SAT for d in ds]
                nsat = sum(sat)
                ok = [d for d, x in zip(ds, sat) if not x]
                sv = {n: st.mean(normalizar(d, osc[m])[0][n] for d in ok) if ok else float("nan")
                      for n in ("nir_855nm", "f8_745nm", "f7_690nm", "f6_640nm")}
                temps = [d["temp_c"] for d in ds if d.get("temp_c") is not None]
                fila = {"modulo": m, "sensor": SENSORES[m], "ganancia_x": gan_x(g),
                        "max_pct_media": round(st.mean(pct), 1), "max_pct_max": round(max(pct), 1),
                        "saturadas": nsat, "lecturas": len(ds),
                        "vis_saturado": sum(bool(d.get("vis_saturado")) for d in ds),
                        **{"s_" + n.split("_")[0]: float(f"{v:.5g}") for n, v in sv.items()},
                        "temp_c": round(st.mean(temps), 2) if temps else ""}
                filas.append(fila)
                print(f"  {gan_x(g):>6g}x  max {fila['max_pct_media']:5.1f} % (hasta {fila['max_pct_max']:5.1f} %)"
                      f"  saturadas {nsat}/{len(ds)}  s_NIR {fila['s_nir']}")
                if nsat:
                    break                            # las ganancias mayores tambien saturan
    except KeyboardInterrupt:
        print("\nDetenido.")
    finally:
        if "zenit" in sen:
            sen["zenit"].adaptativa()
        reg.cerrar()
    print("\nResumen (ganancia segura = la mas alta sin ninguna lectura saturada):")
    for m in mods:
        fm = [f for f in filas if f["modulo"] == m]
        seg = [f for f in fm if not f["saturadas"]]
        if not seg:
            print(f"  {m}: satura incluso a {gan_x(gans[0]):g}x (hay que acortar el tiempo de integracion)")
            continue
        f = seg[-1]
        margen = 90 / f["max_pct_max"] if f["max_pct_max"] else float("nan")
        fin = "" if len(seg) < len(fm) else " (no llego a saturar en el barrido)"
        print(f"  {m}: ganancia segura {f['ganancia_x']:g}x, max {f['max_pct_max']:.1f} %; la luz puede subir "
              f"x{margen:.2f} antes de saturar a esa ganancia; s_NIR {f['s_nir']}{fin}")
    if filas:
        reg.resumen(filas, list(filas[0].keys()))


DESFASE_MAX = 0.3   # s; pares con mas desfase entre el fin de las dos lecturas se excluyen


def leer_par(nadir, zenit, idx=None):
    """Lectura simultanea de los dos modulos. Espera un paquete del zenit y arranca la
    lectura del nadir para que termine cuando llegue el siguiente paquete; asi los dos
    sensores integran durante el mismo intervalo."""
    p0 = zenit.siguiente(time.time())
    if p0 is not None:
        with zenit.lock:
            ts = [t for t, _ in zenit.paq][-6:]
        dif = [b - a for a, b in zip(ts, ts[1:]) if 0.5 < b - a < 3]
        periodo = st.median(dif) if dif else 1.0
        espera = p0["t"] + periodo - nadir.dur - time.time()
        if espera > 0:
            time.sleep(espera)
    dn = nadir.leer(idx)
    dz = zenit.emparejar(dn["t_fin"])
    return dn, dz


def modo_intercomparacion(a):
    nadir, zenit = abrir("nadir"), abrir("zenit")
    idx = idx_de_x(a.ganancia) if a.ganancia else None
    if idx is None:
        zenit.adaptativa()
    elif not zenit.fijar(idx):
        raise SystemExit("El zenit no confirmo la ganancia: revisa la conexion.")
    else:
        print(f"Ganancia fija {gan_x(idx):g}x en los dos sensores")
    osc_n, osc_z = cargar_osc("nadir"), cargar_osc("zenit")
    reg = Registro("intercomparacion", a.etiqueta, ["nadir", "zenit"])
    k = {"A": {n: [] for n in NOMBRES}, "B": {n: [] for n in NOMBRES}}
    sin_osc = 0
    try:
        for pos, texto in (("A", "Coloca los dos sensores uno al lado del otro (posicion A)"),
                           ("B", "Intercambia las posiciones de los dos sensores (posicion B)")):
            input(f"\n{texto}. Enter para empezar...")
            i = 0
            while i < a.n:
                dn, dz = leer_par(nadir, zenit, idx)
                if dz is None:
                    print("  sin paquete del zenit, se repite")
                    continue
                reg.fila(fase="luz", pasada=pos, rep=i, nadir=dn, zenit=dz)
                ok = not (dn["saturado"] or dz["saturado"]) and (dz.get("desfase_s") is not None
                                                                 and abs(dz["desfase_s"]) <= DESFASE_MAX)
                if idx is not None and dz.get("ganancia_idx") != idx:
                    ok = False
                if ok:
                    sn, on = normalizar(dn, osc_n)
                    sz, oz = normalizar(dz, osc_z)
                    sin_osc += (not on) + (not oz)
                    for n in NOMBRES:
                        if sn[n] > 0:
                            k[pos][n].append(sz[n] / sn[n])
                print(f"  {pos} [{i + 1}/{a.n}] {linea(dn, 'nadir')} | {linea(dz, 'zenit')}"
                      f"  desfase {dz['desfase_s']:+.2f} s{'' if ok else '  (excluida)'}")
                i += 1
    finally:
        if idx is not None:
            zenit.adaptativa()
        reg.cerrar()
    if sin_osc:
        print(f"\nAviso: {sin_osc} lecturas sin oscuridad guardada para su ganancia (no se resto).")
    filas = []
    print("\nk = s_zenit / s_nadir   (k = media geometrica de las posiciones A y B)")
    for n in NOMBRES:
        A, B = k["A"][n], k["B"][n]
        if not A or not B:
            continue
        kA, kB = st.mean(A), st.mean(B)
        kk = math.sqrt(kA * kB) if kA > 0 and kB > 0 else float("nan")
        fila = {"canal": n, "k_A": round(kA, 5), "cv_A_pct": round(cv(A), 2),
                "k_B": round(kB, 5), "cv_B_pct": round(cv(B), 2), "k": round(kk, 5),
                "dif_A_B_pct": round((kB / kA - 1) * 100, 2), "lecturas_A": len(A), "lecturas_B": len(B)}
        filas.append(fila)
        print(f"  {n:10s} k {kk:7.4f}   A {kA:7.4f} (CV {fila['cv_A_pct']:4.2f} %)   "
              f"B {kB:7.4f} (CV {fila['cv_B_pct']:4.2f} %)   A-B {fila['dif_A_B_pct']:+5.2f} %"
              f"{'' if max(fila['cv_A_pct'], fila['cv_B_pct']) < 5 else '   CV >= 5 %'}")
    if filas:
        reg.resumen(filas, list(filas[0].keys()))


def modo_ptfe(a):
    prueba = a.modulo if a.modulo in ("nadir", "zenit") else "zenit"
    otro = "nadir" if prueba == "zenit" else "zenit"
    sen = {prueba: abrir(prueba)}
    sen[otro] = None if a.sin_referencia else abrir(otro, obligatorio=False)
    idx = idx_de_x(a.ganancia) if a.ganancia else None
    if sen.get("zenit"):
        if idx is None:
            sen["zenit"].adaptativa()
        elif not sen["zenit"].fijar(idx):
            raise SystemExit("El zenit no confirmo la ganancia: revisa la conexion.")
    if idx is not None:
        print(f"Ganancia fija {gan_x(idx):g}x (la misma con y sin PTFE)")
    osc = {m: cargar_osc(m) for m in ("nadir", "zenit")}
    mods = [m for m in ("nadir", "zenit") if sen.get(m)]
    reg = Registro("ptfe", a.etiqueta, mods)
    # por repeticion y condicion: senal normalizada del sensor de prueba y cociente contra la referencia
    datos = {r: {"sin": [], "con": []} for r in range(a.repeticiones)}
    try:
        for r in range(a.repeticiones):
            for cond, texto in (("sin", f"Deja el sensor {prueba} SIN PTFE"),
                                ("con", f"Coloca la pieza de PTFE sobre el sensor {prueba}")):
                input(f"\nRepeticion {r + 1}/{a.repeticiones}: {texto}. Enter para empezar...")
                i = 0
                while i < a.n:
                    if sen.get("nadir"):
                        if sen.get("zenit"):
                            dn, dz = leer_par(sen["nadir"], sen["zenit"], idx)
                        else:
                            dn, dz = sen["nadir"].leer(idx), None
                    else:
                        dn, dz = None, sen["zenit"].leer(idx)
                    d = {"nadir": dn, "zenit": dz}
                    if d[prueba] is None:
                        print("  sin dato del sensor de prueba, se repite")
                        continue
                    reg.fila(fase=cond, rep=r, pasada=i, nadir=dn, zenit=dz)
                    i += 1
                    if d[prueba]["saturado"]:
                        print("  saturada, excluida")
                        continue
                    sp = normalizar(d[prueba], osc[prueba])[0]
                    ref = None
                    if sen.get(otro) and d[otro] is not None and not d[otro]["saturado"] and \
                            (dz is None or abs(dz.get("desfase_s", 0)) <= DESFASE_MAX):
                        ref = normalizar(d[otro], osc[otro])[0]
                    datos[r][cond].append((sp, ref))
                    print(f"  {cond} [{i}/{a.n}] {linea(d[prueba], prueba)}")
    finally:
        if sen.get("zenit") and idx is not None:
            sen["zenit"].adaptativa()
        reg.cerrar()

    filas = []
    print("\nT_d = s_con / s_sin por repeticion; 'ref' divide antes por el otro sensor")
    for n in NOMBRES:
        td, tdr = [], []
        for r in datos:
            sin, con = datos[r]["sin"], datos[r]["con"]
            if sin and con:
                td.append(st.mean(x[0][n] for x in con) / st.mean(x[0][n] for x in sin))
                cs = [x[0][n] / x[1][n] for x in con if x[1] and x[1][n] > 0]
                ss = [x[0][n] / x[1][n] for x in sin if x[1] and x[1][n] > 0]
                if cs and ss:
                    tdr.append(st.mean(cs) / st.mean(ss))
        if not td:
            continue
        fila = {"canal": n, "T_d": round(st.mean(td), 5), "cv_rep_pct": round(cv(td), 2),
                "T_d_ref": round(st.mean(tdr), 5) if tdr else "",
                "cv_rep_ref_pct": round(cv(tdr), 2) if len(tdr) > 1 else "", "repeticiones": len(td)}
        filas.append(fila)
        print(f"  {n:10s} T_d {fila['T_d']:.4f} (CV {fila['cv_rep_pct']} %)"
              + (f"   con ref {fila['T_d_ref']:.4f} (CV {fila['cv_rep_ref_pct']} %)" if tdr else ""))
    if filas:
        reg.resumen(filas, list(filas[0].keys()))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("modo", choices=["registro", "ganancias", "oscuridad", "intercomparacion", "ptfe", "saturacion"])
    p.add_argument("--sensor", default="", help="sensor fisico del modulo indicado (A, B...)")
    p.add_argument("--sensor-nadir", default="", help="sensor fisico conectado a la Raspberry")
    p.add_argument("--sensor-zenit", default="", help="sensor fisico del ESP32 (si no, lo toma del firmware)")
    p.add_argument("--config", default="", help="montaje: desnudo, capsula_ptfe, ...")
    p.add_argument("--modulo", default=None, help="nadir, zenit o ambos (segun el modo)")
    p.add_argument("--ganancias", default="", help="multiplicadores separados por coma, p. ej. 2,4,8")
    p.add_argument("--ganancia", default="", help="ganancia fija (registro, ptfe, intercomparacion), p. ej. 4")
    p.add_argument("--sin-oscuridad", action="store_true",
                   help="ganancias: no apaga la lampara; usa la oscuridad guardada (modo oscuridad)")
    p.add_argument("--n", type=int, default=None, help="lecturas por ganancia/pasada/posicion/condicion")
    p.add_argument("--n-osc", type=int, default=10, help="lecturas oscuras por ganancia (modo ganancias)")
    p.add_argument("--repeticiones", type=int, default=3, help="ciclos sin/con PTFE (modo ptfe)")
    p.add_argument("--sin-referencia", action="store_true", help="ptfe: no usar el otro sensor")
    p.add_argument("--etiqueta", default="", help="texto libre para el nombre del archivo (p. ej. sol, lampara)")
    a = p.parse_args()
    print(f"Hora de la Raspberry: {datetime.now():%Y-%m-%d %H:%M}  (si no es la real, ajustala con:"
          f"  sudo date -s \"AAAA-MM-DD HH:MM\")")
    defecto_n = {"registro": 30, "ganancias": 15 if a.modulo == "ambos" else 10, "oscuridad": 10,
                 "intercomparacion": 20, "ptfe": 10, "saturacion": 5}
    a.n = a.n or defecto_n[a.modo]
    global CONFIG
    CONFIG = a.config.strip()
    SENSORES["nadir"] = a.sensor_nadir.strip()
    SENSORES["zenit"] = a.sensor_zenit.strip()
    if a.sensor.strip():
        if a.modulo not in ("nadir", "zenit") and a.modo != "ptfe":
            p.error("--sensor es para un solo modulo; con dos usa --sensor-nadir y --sensor-zenit")
        SENSORES[a.modulo or "zenit"] = a.sensor.strip()
    if a.modo == "registro":
        a.modulo = a.modulo or "ambos"
        if a.modulo not in ("nadir", "zenit", "ambos"):
            p.error("--modulo debe ser nadir, zenit o ambos")
        modo_registro(a)
    elif a.modo == "ganancias":
        if a.modulo == "ambos":
            modo_ganancias_par(a)
        elif a.modulo in ("nadir", "zenit"):
            modo_ganancias(a)
        else:
            p.error("en modo ganancias indica --modulo nadir, zenit o ambos")
    elif a.modo == "oscuridad":
        if a.modulo not in ("nadir", "zenit", "ambos"):
            p.error("en modo oscuridad indica --modulo nadir, zenit o ambos")
        modo_oscuridad(a)
    elif a.modo == "intercomparacion":
        modo_intercomparacion(a)
    elif a.modo == "saturacion":
        a.modulo = a.modulo or "zenit"
        if a.modulo not in ("nadir", "zenit", "ambos"):
            p.error("--modulo debe ser nadir, zenit o ambos")
        modo_saturacion(a)
    else:
        a.modulo = a.modulo or "zenit"
        modo_ptfe(a)


if __name__ == "__main__":
    main()
