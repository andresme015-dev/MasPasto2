"""Copia la hora del DS3231 al reloj del sistema (para arrancar sin internet).
Requiere la pila CR2032 en el DS3231 y que la hora se haya fijado antes con set_rtc.py."""
import subprocess
from test_ds3231 import leer_ds3231


def rtc_a_sistema():
    r = leer_ds3231()
    if not r["hora_valida"]:
        raise RuntimeError("El DS3231 perdio la hora (bandera OSF activa). "
                           "Revisa la pila y vuelve a fijarla con set_rtc.py")
    ts = r["timestamp"].replace("T", " ")
    subprocess.run(["sudo", "date", "-s", ts], check=True)
    return ts


if __name__ == "__main__":
    print("Hora del sistema ajustada a:", rtc_a_sistema())
