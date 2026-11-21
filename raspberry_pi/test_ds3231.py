"""DS3231 (I2C 0x68): reloj de tiempo real.
Sin pila CR2032 el reloj pierde la hora al apagarse; la bandera OSF lo indica."""
import smbus2

DIRECCION = 0x68
bus = smbus2.SMBus(1)


def _bcd(v):
    return (v // 16) * 10 + (v % 16)


def leer_ds3231():
    d = bus.read_i2c_block_data(DIRECCION, 0x00, 7)
    estado = bus.read_byte_data(DIRECCION, 0x0F)
    return {
        "timestamp": (
            f"20{_bcd(d[6]):02d}-{_bcd(d[5] & 0x1F):02d}-{_bcd(d[4]):02d}"
            f"T{_bcd(d[2] & 0x3F):02d}:{_bcd(d[1]):02d}:{_bcd(d[0] & 0x7F):02d}"
        ),
        # OSF = 1: el oscilador se detuvo (p. ej., se quedo sin energia) y la hora no es confiable
        "hora_valida": not bool(estado & 0x80),
    }


if __name__ == "__main__":
    r = leer_ds3231()
    print("Hora del DS3231:", r["timestamp"])
    print("Hora valida    :", r["hora_valida"])
