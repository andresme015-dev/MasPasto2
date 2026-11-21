"""TF-Nova: medicion continua y caracterizacion.
  python3 lidar_continuo.py               -> medicion continua con estadisticas
  python3 lidar_continuo.py caracterizar  -> toma 200 lecturas por punto y guarda CSV"""
import csv
import glob
import os
import statistics
import sys
import time
from collections import deque
from datetime import datetime

import serial

BAUD = 115200
VALIDAR_CHECKSUM = True
INVALIDO = 65535              # valor que el TF-Nova entrega cuando no logra medir
MIN_CM = 10                   # por debajo del rango minimo (0,1 m) la lectura no es confiable
N_CARACTERIZAR = 200
ARCHIVO_CSV = os.path.expanduser("~/maspasto2/caracterizacion_lidar.csv")

fallos_checksum = 0
desconexiones = 0


def abrir_puerto():
    while True:
        puertos = sorted(glob.glob("/dev/ttyUSB*"))
        if puertos:
            try:
                ser = serial.Serial(puertos[0], BAUD, timeout=1)
                print(f"[puerto] abierto {puertos[0]}")
                return ser
            except serial.SerialException as e:
                print(f"[puerto] no se pudo abrir {puertos[0]}: {e}")
        else:
            print("[puerto] no hay /dev/ttyUSB*, reintentando...")
        time.sleep(1)


def leer_trama(ser):
    global fallos_checksum
    while True:
        if ser.read(1) != b"\x59":
            continue
        if ser.read(1) != b"\x59":
            continue
        resto = ser.read(7)
        if len(resto) != 7:
            continue
        trama = b"\x59\x59" + resto
        if VALIDAR_CHECKSUM and (sum(trama[:8]) & 0xFF) != trama[8]:
            fallos_checksum += 1
            continue
        return trama[2] | (trama[3] << 8), trama[4] | (trama[5] << 8)


def leer_seguro(estado):
    """Lee una trama; si el puerto se cae, lo reabre y sigue."""
    global desconexiones
    while True:
        try:
            return leer_trama(estado["ser"])
        except serial.SerialException:
            desconexiones += 1
            print(f"[aviso] el puerto se desconecto (vez #{desconexiones}). Reabriendo...")
            try:
                estado["ser"].close()
            except Exception:
                pass
            time.sleep(1)
            estado["ser"] = abrir_puerto()


def modo_continuo(estado):
    ventana = deque(maxlen=50)
    n = inval = 0
    t0 = t_print = time.time()
    print("Midiendo de forma continua. Ctrl+C para detener.\n")
    print(" tiempo |  dist |  media |  desv |  min |  max | fuerza | invalidas |  Hz")
    while True:
        d, f = leer_seguro(estado)
        n += 1
        if d == INVALIDO or d < MIN_CM:
            inval += 1
        else:
            ventana.append(d)
        ahora = time.time()
        if ahora - t_print >= 0.5:
            hz = n / (ahora - t_print)
            if ventana:
                print(f"{ahora - t0:6.1f}s | {ventana[-1]:5d} | {statistics.mean(ventana):6.1f} | "
                      f"{statistics.pstdev(ventana):5.2f} | {min(ventana):4d} | {max(ventana):4d} | "
                      f"{f:6d} | {inval:9d} | {hz:3.0f}")
            else:
                print(f"{ahora - t0:6.1f}s |  sin lecturas validas | fuerza {f} | invalidas {inval}")
            n = inval = 0
            t_print = ahora


def modo_caracterizar(estado):
    nuevo = not os.path.exists(ARCHIVO_CSV)
    with open(ARCHIVO_CSV, "a", newline="") as fcsv:
        w = csv.writer(fcsv)
        if nuevo:
            w.writerow(["fecha_hora", "superficie", "dist_real_cm", "n_validas", "n_invalidas",
                        "media_cm", "desv_cm", "min_cm", "max_cm", "error_cm", "fuerza_media"])
        superficie = input("Superficie de prueba (ej: carton_blanco): ").strip() or "sin_nombre"
        while True:
            txt = input("\nDistancia real en cm (Enter para salir, s para cambiar superficie): ").strip()
            if txt == "":
                break
            if txt.lower() == "s":
                superficie = input("Nueva superficie: ").strip() or superficie
                continue
            real = float(txt)
            estado["ser"].reset_input_buffer()
            ds, fs, inval = [], [], 0
            while len(ds) < N_CARACTERIZAR and inval < N_CARACTERIZAR:
                d, f = leer_seguro(estado)
                if d == INVALIDO or d < MIN_CM:
                    inval += 1
                else:
                    ds.append(d)
                    fs.append(f)
            if not ds:
                print("  sin lecturas validas en este punto; revisa el montaje")
                continue
            m, s = statistics.mean(ds), statistics.pstdev(ds)
            err = m - real
            w.writerow([datetime.now().isoformat(timespec="seconds"), superficie, real,
                        len(ds), inval, round(m, 2), round(s, 3), min(ds), max(ds),
                        round(err, 2), round(statistics.mean(fs), 1)])
            fcsv.flush()
            print(f"  real {real:.1f} | media {m:.2f} | desv {s:.2f} | min {min(ds)} | "
                  f"max {max(ds)} | error {err:+.2f} cm | invalidas {inval} | "
                  f"fuerza {statistics.mean(fs):.0f}")
    print(f"\nGuardado en {ARCHIVO_CSV}")


if __name__ == "__main__":
    estado = {"ser": abrir_puerto()}
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "caracterizar":
            modo_caracterizar(estado)
        else:
            modo_continuo(estado)
    except KeyboardInterrupt:
        print(f"\nDetenido. Desconexiones: {desconexiones}. "
              f"Tramas con checksum invalido: {fallos_checksum}.")
    finally:
        try:
            estado["ser"].close()
        except Exception:
            pass
