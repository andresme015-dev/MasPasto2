"""AS7343 del modulo nadir (I2C 0x39) con ganancia adaptativa.

Lee los 12 canales espectrales en el modo automatico de 18 canales (3 ciclos de
integracion; F7 y F8 solo se leen en el tercer ciclo). Antes de aceptar una lectura
ajusta la ganancia para que NINGUNO de los 18 canales sature, incluidos los VIS, y la
senal no quede demasiado baja.

Por que se incluyen los VIS: en la prueba del 2026-10-21 (halogena, 32x/64x/128x), con el
VIS muy saturado los 12 canales espectrales recibieron un exceso casi constante de
~850-1400 cuentas a 64x, que crece con la ganancia. Un VIS saturado contamina al resto.
Los indicadores de saturacion del sensor se guardan pero no se usan para decidir: en
las pruebas no se activaron ni con 65535 cuentas. La saturacion se decide por cuentas.

Devuelve las cuentas crudas, la ganancia y el tiempo de integracion usados, los
valores normalizados (cuentas / (ganancia * t_int)) y el VIS de cada ciclo.

Uso:  python3 test_as7343.py            (lectura continua cada 2 s, Ctrl+C para salir)
      python3 test_as7343.py --una      (una sola lectura)
      python3 test_as7343.py --ganancia 4   (ganancia fija, sin ajuste; ver GAN_X)
"""
import sys
import time

from adafruit_as7343 import AS7343, Channel, Gain, SmuxMode

# --- Integracion -------------------------------------------------------------------
# t_int = (ATIME+1)(ASTEP+1) * 2,78 us = 100 * 656 * 2,78 us = 182,4 ms por ciclo.
# Es el tiempo mas corto que conserva el techo de 65535 cuentas, porque el maximo del
# conversor es (ATIME+1)(ASTEP+1) = 65 600. Con 3 ciclos, una lectura toma ~0,55 s.
ATIME, ASTEP = 99, 655
T_INT_MS = (ATIME + 1) * (ASTEP + 1) * 0.00278
TECHO = min(65535, (ATIME + 1) * (ASTEP + 1))

# --- Ganancia adaptativa -----------------------------------------------------------
# Intervalo permitido: 0,5x a 64x (se amplia solo si la Etapa 1 verifica mas ganancias).
GAN_MIN, GAN_MAX = Gain.X0_5, Gain.X64
# Se aplican al canal mas alto de los 18 (los VIS suelen ser los mas altos).
LIM_SAT = int(0.90 * TECHO)    # por encima: baja un paso
LIM_BAJO = int(0.40 * TECHO)   # por debajo: sube un paso (al duplicar queda < 90 %)


def gan_x(indice):
    """Ganancia nominal: indice 0 -> 0,5x, 1 -> 1x, ..., 7 -> 64x, 12 -> 2048x."""
    return 2.0 ** (indice - 1)


# Canales espectrales en orden de longitud de onda (pico de la hoja de datos)
CANALES = [
    ("f1_405nm", Channel.F1), ("f2_425nm", Channel.F2), ("fz_450nm", Channel.FZ),
    ("f3_475nm", Channel.F3), ("f4_515nm", Channel.F4), ("f5_550nm", Channel.F5),
    ("fy_555nm", Channel.FY), ("fxl_600nm", Channel.FXL), ("f6_640nm", Channel.F6),
    ("f7_690nm", Channel.F7), ("f8_745nm", Channel.F8), ("nir_855nm", Channel.NIR),
]
NOMBRES = [n for n, _ in CANALES]
IDX_ESP = [c for _, c in CANALES]                 # posiciones de los 12 espectrales
# Canal VIS (claro) de cada ciclo: suma de los fotodiodos TL y BR
VIS = {
    "vis_c1": (Channel.VIS_TL_0, Channel.VIS_BR_0),   # ciclo 1: FZ, FY, FXL, NIR
    "vis_c2": (Channel.VIS_TL_1, Channel.VIS_BR_1),   # ciclo 2: F2, F3, F4, F6
    "vis_c3": (Channel.VIS_TL_2, Channel.VIS_BR_2),   # ciclo 3: F1, F7, F8, F5
}

sensor = None
_gan = Gain.X4


def iniciar():
    global sensor
    if sensor is None:
        import board                      # solo existe en la Raspberry (adafruit-blinka)
        sensor = AS7343(board.I2C())
        sensor.atime = ATIME
        sensor.astep = ASTEP
        sensor.smux_mode = SmuxMode.CH18
        sensor.read_timeout = 3000        # ms; la libreria trae 1000 ms por defecto
        sensor.gain = _gan
    return sensor


def _leer_crudo():
    """Una medicion completa (3 ciclos). Devuelve (lista de 18 cuentas, t_inicio, sat_analog, sat_digital)."""
    t0 = time.time()
    r = sensor.all_channels
    # Los indicadores de saturacion se leen de STATUS2 al terminar la medicion; ademas se
    # compara contra el techo de cuentas, por si el indicador ya se hubiera borrado.
    return r, t0, bool(sensor.analog_saturated), bool(sensor.digital_saturated)


def leer_as7343(ganancia=None, max_ajustes=6):
    """Lectura con ganancia adaptativa (ganancia=None) o fija (indice de Gain).

    Devuelve un diccionario con cuentas por canal, ganancia_x, t_int_ms, saturacion,
    valores normalizados en 'norm' y el VIS de cada ciclo.
    """
    global _gan
    iniciar()
    if ganancia is not None:
        sensor.gain = ganancia
        r, t0, sat_a, sat_d = _leer_crudo()
        g = ganancia
    else:
        sensor.gain = _gan                # por si la lectura anterior fue con ganancia fija
        for _ in range(max_ajustes):
            g = _gan
            r, t0, sat_a, sat_d = _leer_crudo()
            m = max(r)                                    # 18 canales, VIS incluido
            if m >= LIM_SAT and _gan > GAN_MIN:
                _gan -= 1
                sensor.gain = _gan
                continue
            if m < LIM_BAJO and _gan < GAN_MAX:
                _gan += 1
                sensor.gain = _gan
                continue
            break

    G = gan_x(g)
    d = {n: r[c] for n, c in CANALES}
    for n, (a, b) in VIS.items():
        d[n] = r[a] + r[b]
    d["t_lectura"] = round(t0, 3)
    d["ganancia_idx"] = int(g)
    d["ganancia_x"] = G
    d["t_int_ms"] = round(T_INT_MS, 2)
    d["sat_analogica"] = sat_a
    d["sat_digital"] = sat_d
    d["max_cuentas"] = max(r)                             # 18 canales: criterio
    d["max_espectral"] = max(r[i] for i in IDX_ESP)       # informativo
    d["saturado"] = d["max_cuentas"] >= LIM_SAT
    d["vis_saturado"] = max(r[i] for par in VIS.values() for i in par) >= LIM_SAT
    d["norm"] = {n: d[n] / (G * T_INT_MS) for n in NOMBRES}
    vis = [d["vis_c1"], d["vis_c2"], d["vis_c3"]]
    if d["vis_saturado"] or min(vis) <= 0:
        d["var_luz_ciclos"] = None                        # no se puede verificar
    else:
        d["var_luz_ciclos"] = max(vis) / min(vis) - 1
    return d


def _nd(a, b):
    return (a - b) / (a + b) if (a + b) > 0 else None


def indices_sin_corregir(d):
    """NDVI y NDRE con solo el nadir (sin corregir por irradiancia), para pruebas."""
    n = d["norm"]
    return {"ndvi": _nd(n["nir_855nm"], n["f6_640nm"]),
            "ndre1": _nd(n["nir_855nm"], n["f8_745nm"]),
            "ndre2": _nd(n["f8_745nm"], n["f7_690nm"])}


def _imprimir(d):
    for k in NOMBRES + list(VIS):
        print(f"  {k:10s} {d[k]:6d}")
    print(f"  ganancia {d['ganancia_x']:g}x | t_int {d['t_int_ms']} ms")
    print(f"  canal mas alto (18, con VIS): {d['max_cuentas']} cuentas "
          f"({d['max_cuentas'] / TECHO * 100:.1f} % del techo) | saturado {d['saturado']}")
    print(f"  canal espectral mas alto: {d['max_espectral']} cuentas "
          f"({d['max_espectral'] / TECHO * 100:.1f} %)")
    v = d["var_luz_ciclos"]
    if v is not None:
        print(f"  variacion de VIS entre ciclos: {v * 100:.2f} %")
    else:
        print("  variacion de VIS entre ciclos: no disponible (VIS saturado)")
    print("  indices sin corregir:", {k: (round(x, 3) if x is not None else None)
                                     for k, x in indices_sin_corregir(d).items()})


if __name__ == "__main__":
    s = iniciar()
    print(f"AS7343 detectado | t_int {T_INT_MS:.1f} ms por ciclo | techo {TECHO} cuentas")
    gan = None
    if "--ganancia" in sys.argv:
        x = float(sys.argv[sys.argv.index("--ganancia") + 1])
        gan = {gan_x(i): i for i in range(13)}[x]
    if "--una" in sys.argv:
        _imprimir(leer_as7343(gan))
    else:
        try:
            while True:
                t = time.time()
                _imprimir(leer_as7343(gan))
                print(f"  (lectura en {time.time() - t:.2f} s)\n")
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nDetenido.")
