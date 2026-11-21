"""Recibe los paquetes JSON que el modulo zenit envia por UDP al puerto 5005
y le envia ordenes de ganancia por el puerto 5006 (firmware_zenit_as7343.ino)."""
import json
import socket

PUERTO = 5005
PUERTO_CMD = 5006
_sock = None


def _socket():
    global _sock
    if _sock is None:
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _sock.bind(("0.0.0.0", PUERTO))
    return _sock


def recibir_zenit(timeout=2.0):
    """Devuelve el siguiente paquete como diccionario, o None si no llega nada a tiempo."""
    s = _socket()
    s.settimeout(timeout)
    try:
        datos, origen = s.recvfrom(4096)
    except socket.timeout:
        return None
    try:
        p = json.loads(datos.decode())
    except ValueError:
        return None
    p["ip_origen"] = origen[0]
    return p


def recibir_zenit_reciente(timeout=2.0):
    """Descarta los paquetes acumulados y espera uno nuevo.
    Sirve para emparejar una lectura del nadir con la irradiancia de ese mismo instante."""
    s = _socket()
    s.setblocking(False)
    try:
        while True:
            s.recvfrom(4096)
    except BlockingIOError:
        pass
    s.setblocking(True)
    return recibir_zenit(timeout)


def enviar_orden_zenit(orden, ip):
    """Envia una orden al ESP32 del zenit: 'G<n>' fija la ganancia en el indice n
    (0 = 0,5x ... 7 = 64x ... 12 = 2048x); 'GA' vuelve a la ganancia adaptativa.
    La IP es la que trae cada paquete en 'ip_origen'."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(orden.encode(), (ip, PUERTO_CMD))
    s.close()


if __name__ == "__main__":
    print(f"Esperando paquetes del zenit en el puerto {PUERTO}. Ctrl+C para detener.")
    try:
        while True:
            print(recibir_zenit())
    except KeyboardInterrupt:
        print("\nDetenido.")
