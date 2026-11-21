"""LiDAR Benewake TF-Nova por adaptador USB-serie (CH341) en /dev/ttyUSB0, 115200 baudios.
Trama de 9 bytes: 0x59 0x59 dist_L dist_H fuerza_L fuerza_H x x checksum."""
import serial

PUERTO = "/dev/ttyUSB0"
BAUD = 115200
INVALIDO = 65535          # el sensor entrega este valor cuando no logra medir
MIN_CM = 10               # por debajo del rango minimo (0,1 m) la lectura no es confiable

ser = serial.Serial(PUERTO, BAUD, timeout=1)


def leer_tfnova(max_intentos=200):
    ser.reset_input_buffer()
    for _ in range(max_intentos):
        if ser.read(1) != b"\x59" or ser.read(1) != b"\x59":
            continue
        resto = ser.read(7)
        if len(resto) != 7:
            continue
        trama = b"\x59\x59" + resto
        if (sum(trama[:8]) & 0xFF) != trama[8]:
            continue                                    # trama corrupta
        dist = trama[2] | (trama[3] << 8)
        fuerza = trama[4] | (trama[5] << 8)
        return {
            "distancia_cm": dist,
            "fuerza_senal": fuerza,
            "lectura_valida": MIN_CM <= dist < INVALIDO,
        }
    raise RuntimeError("No llego ninguna trama valida del TF-Nova")


if __name__ == "__main__":
    print(leer_tfnova())
