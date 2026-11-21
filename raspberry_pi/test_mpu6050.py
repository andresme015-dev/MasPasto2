"""MPU-6050 (I2C 0x69, AD0 a 3,3 V): inclinacion del baston.
Montaje con el eje Z apuntando al cielo."""
import math
import time
import smbus2

DIRECCION = 0x69
LIMITE_VERTICAL_DEG = 5.0

bus = smbus2.SMBus(1)
bus.write_byte_data(DIRECCION, 0x6B, 0x00)   # sale del modo de reposo
time.sleep(0.1)


def _palabra(reg):
    h = bus.read_byte_data(DIRECCION, reg)
    l = bus.read_byte_data(DIRECCION, reg + 1)
    v = (h << 8) + l
    return v - 65536 if v >= 0x8000 else v


def leer_mpu6050():
    ax = _palabra(0x3B) / 16384.0
    ay = _palabra(0x3D) / 16384.0
    az = _palabra(0x3F) / 16384.0
    frontal = math.atan2(ax, math.sqrt(ay ** 2 + az ** 2)) * 180 / math.pi
    lateral = math.atan2(ay, math.sqrt(ax ** 2 + az ** 2)) * 180 / math.pi
    total = round(math.sqrt(frontal ** 2 + lateral ** 2), 2)
    return {
        "angulo_frontal_deg": round(frontal, 2),
        "angulo_lateral_deg": round(lateral, 2),
        "angulo_inclinacion_deg": total,
        "baston_vertical": total <= LIMITE_VERTICAL_DEG,
    }


if __name__ == "__main__":
    print("Ctrl+C para detener")
    try:
        while True:
            print(leer_mpu6050())
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nDetenido.")
