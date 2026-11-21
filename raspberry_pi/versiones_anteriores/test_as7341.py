"""AS7341 del modulo nadir (I2C 0x39) con ganancia adaptativa.
Antes de cada lectura ajusta la ganancia hasta que ningun canal sature y la senal
no quede demasiado baja. Devuelve las cuentas crudas, la ganancia y el tiempo de
integracion usados, y los valores normalizados (cuentas / (ganancia * t_int)),
que son los que se dividen contra el modulo zenit."""
import board
from adafruit_as7341 import AS7341, Gain

ATIME, ASTEP = 100, 999
T_INT_MS = (ATIME + 1) * (ASTEP + 1) * 0.00278          # 280,78 ms
GANANCIAS = [Gain.GAIN_0_5X, Gain.GAIN_1X, Gain.GAIN_2X, Gain.GAIN_4X,
             Gain.GAIN_8X, Gain.GAIN_16X, Gain.GAIN_32X, Gain.GAIN_64X]
MULT = [0.5, 1, 2, 4, 8, 16, 32, 64]
LIM_SAT = 58000          # ~90 % del techo de 16 bits
LIM_BAJO = 12000         # por debajo de esto se sube un paso
CANALES = ["f1_415nm", "f2_445nm", "f3_480nm", "f4_515nm",
           "f5_555nm", "f6_590nm", "f7_630nm", "f8_680nm", "clear", "nir_910nm"]

sensor = AS7341(board.I2C())
sensor.atime = ATIME
sensor.astep = ASTEP
_idx = 3                 # arranca en 4x (la libreria arranca en 128x)
sensor.gain = GANANCIAS[_idx]


def _leer_crudo():
    f = sensor.all_channels                        # F1-F8
    return tuple(f) + (sensor.channel_clear, sensor.channel_nir)


def leer_as7341(max_ajustes=8):
    global _idx
    for _ in range(max_ajustes):
        ganancia = MULT[_idx]
        c = _leer_crudo()
        m = max(c)
        if m >= LIM_SAT and _idx > 0:
            _idx -= 1
            sensor.gain = GANANCIAS[_idx]
            continue
        if m < LIM_BAJO and _idx < len(GANANCIAS) - 1:
            _idx += 1
            sensor.gain = GANANCIAS[_idx]
            continue
        break
    datos = dict(zip(CANALES, c))
    datos["ganancia_x"] = ganancia
    datos["t_int_ms"] = round(T_INT_MS, 2)
    datos["saturado"] = max(c) >= LIM_SAT
    datos["norm"] = {k: datos[k] / (ganancia * T_INT_MS) for k in CANALES}
    return datos


def ndvi_sin_corregir(d):
    """NDVI con solo el nadir (sin corregir por irradiancia), para pruebas."""
    nir, rojo = d["norm"]["nir_910nm"], d["norm"]["f8_680nm"]
    return (nir - rojo) / (nir + rojo) if (nir + rojo) > 0 else None


if __name__ == "__main__":
    d = leer_as7341()
    for k in CANALES:
        print(f"{k:10s} {d[k]:6d}")
    print("ganancia_x :", d["ganancia_x"], "| t_int_ms:", d["t_int_ms"],
          "| saturado:", d["saturado"])
    print("NDVI sin corregir:", ndvi_sin_corregir(d))
