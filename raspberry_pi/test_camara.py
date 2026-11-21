"""Camara OV5647 (Camera Module v1.3) por CSI.
La espera de 2 s tras arrancar es obligatoria: sin ella la foto sale negra."""
import os
import time
from datetime import datetime
from picamera2 import Picamera2


def capturar_foto(carpeta="~/maspasto2/fotos"):
    carpeta = os.path.expanduser(carpeta)
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg")
    cam = Picamera2()
    try:
        cam.configure(cam.create_still_configuration())
        cam.start()
        time.sleep(2)
        cam.capture_file(ruta)
        cam.stop()
    finally:
        cam.close()
    return ruta


if __name__ == "__main__":
    print("Foto guardada en:", capturar_foto())
