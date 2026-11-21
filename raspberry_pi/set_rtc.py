"""Escribe la hora actual del sistema en el DS3231.
Usar solo cuando la hora del sistema es correcta (con internet o ajustada a mano)."""
import datetime
import smbus2

DIRECCION = 0x68
bus = smbus2.SMBus(1)


def _a_bcd(v):
    return ((v // 10) << 4) | (v % 10)


def escribir_hora_en_rtc():
    t = datetime.datetime.now()
    datos = [
        _a_bcd(t.second), _a_bcd(t.minute), _a_bcd(t.hour),   # hora en formato 24 h
        _a_bcd(t.isoweekday()),                                # dia de la semana 1-7
        _a_bcd(t.day), _a_bcd(t.month), _a_bcd(t.year - 2000),
    ]
    bus.write_i2c_block_data(DIRECCION, 0x00, datos)
    estado = bus.read_byte_data(DIRECCION, 0x0F)
    bus.write_byte_data(DIRECCION, 0x0F, estado & 0x7F)        # limpia la bandera OSF
    return t.isoformat(timespec="seconds")


if __name__ == "__main__":
    print("Hora escrita en el DS3231:", escribir_hora_en_rtc())
