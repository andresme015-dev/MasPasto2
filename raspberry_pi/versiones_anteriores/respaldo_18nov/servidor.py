"""Interfaz web de MasPasto2 para el celular, en la red PasturaMetrics.

    python3 servidor.py                 # con los sensores
    python3 servidor.py --simulado      # sin sensores, para probar la interfaz

Luego, en el celular conectado a la red PasturaMetrics, abrir http://192.168.4.1:8000
Solo usa la libreria estandar de Python (no hay que instalar nada). Escribe solo en
~/maspasto2/datos_espectro/mediciones/, salvo al exportar a una memoria USB que el usuario pida.
"""
import argparse
import csv
import io
import json
import os
import shutil
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import medir

AQUI = os.path.dirname(os.path.abspath(__file__))
DISP = None


class Trabajo:
    """Un solo trabajo a la vez (blanco, suelo, medicion); la interfaz consulta su progreso."""

    def __init__(self):
        self.lock = threading.Lock()
        self.estado = {"activo": False, "tipo": None, "progreso": 0, "texto": "", "resultado": None,
                       "error": None, "n": 0}

    def iniciar(self, tipo, funcion, **kw):
        with self.lock:
            if self.estado["activo"]:
                return False
            self.estado = {"activo": True, "tipo": tipo, "progreso": 0, "texto": "Iniciando",
                           "resultado": None, "error": None, "n": self.estado["n"] + 1}

        def progreso(f, txt):
            self.estado.update(progreso=round(f, 2), texto=txt)

        def correr():
            try:
                r = funcion(progreso=progreso, **kw)
                self.estado.update(resultado=r, progreso=1, texto="Listo")
            except Exception as e:
                traceback.print_exc()
                self.estado.update(error=str(e) or type(e).__name__)
            finally:
                self.estado["activo"] = False

        threading.Thread(target=correr, daemon=True).start()
        return True


TRABAJO = Trabajo()


def montajes_usb():
    """Memorias montadas en /media o /mnt (vfat, exfat o ntfs)."""
    r = []
    try:
        with open("/proc/mounts") as f:
            for linea in f:
                p = linea.split()
                if len(p) > 2 and p[2] in ("vfat", "exfat", "ntfs", "ntfs3", "fuseblk") and \
                        (p[1].startswith("/media/") or p[1].startswith("/mnt/")):
                    r.append(p[1].replace("\\040", " "))
    except OSError:
        pass
    return r


def csv_todas():
    filas = DISP.mediciones()
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=medir.CAMPOS, extrasaction="ignore")
    w.writeheader()
    w.writerows(filas)
    return buf.getvalue().encode("utf-8")


class Manejador(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass                                  # sin ruido en la terminal

    def _enviar(self, codigo, cuerpo, tipo="application/json; charset=utf-8", extra=None):
        if isinstance(cuerpo, (dict, list)):
            cuerpo = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        elif isinstance(cuerpo, str):
            cuerpo = cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return {}

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            with open(os.path.join(AQUI, "interfaz.html"), "rb") as f:
                return self._enviar(200, f.read(), "text/html; charset=utf-8")
        if u.path == "/api/estado":
            e = DISP.estado()
            e["trabajo"] = TRABAJO.estado
            e["usb"] = montajes_usb()
            return self._enviar(200, e)
        if u.path == "/api/trabajo":
            return self._enviar(200, TRABAJO.estado)
        if u.path == "/api/mediciones":
            return self._enviar(200, DISP.mediciones())
        if u.path == "/api/exportar":
            nombre = f"mediciones_maspasto2_{time.strftime('%Y%m%d_%H%M')}.csv"
            return self._enviar(200, csv_todas(), "text/csv; charset=utf-8",
                                {"Content-Disposition": f'attachment; filename="{nombre}"'})
        if u.path.startswith("/fotos/"):
            ruta = os.path.join(medir.CARPETA, "fotos", os.path.basename(u.path))
            if os.path.isfile(ruta):
                with open(ruta, "rb") as f:
                    return self._enviar(200, f.read(), "image/jpeg")
        return self._enviar(404, {"error": "no encontrado"})

    def do_POST(self):
        u = urlparse(self.path)
        datos = self._json()
        if u.path == "/api/blanco":
            ok = TRABAJO.iniciar("blanco", DISP.tomar_blanco)
        elif u.path == "/api/suelo":
            man = datos.get("manual_cm")
            ok = TRABAJO.iniciar("suelo", DISP.tomar_suelo, manual_cm=float(man) if man not in (None, "") else None)
        elif u.path == "/api/medir":
            ok = TRABAJO.iniciar("medir", DISP.medir, punto=str(datos.get("punto", ""))[:40],
                                 nota=str(datos.get("nota", ""))[:200],
                                 hora_celular=str(datos.get("hora_celular", ""))[:40])
        elif u.path == "/api/reconectar":
            ok = TRABAJO.iniciar("reconectar", lambda progreso: DISP.reconectar())
        elif u.path == "/api/sesion_nueva":
            if TRABAJO.estado["activo"]:
                return self._enviar(409, {"error": "Hay una medicion en curso."})
            DISP.nueva_sesion()
            return self._enviar(200, {"ok": True})
        elif u.path == "/api/usb":
            destinos = montajes_usb()
            if not destinos:
                return self._enviar(404, {"error": "No se encontro una memoria USB montada."})
            dest = os.path.join(destinos[0], "MasPasto2")
            try:
                os.makedirs(dest, exist_ok=True)
                with open(os.path.join(dest, f"mediciones_maspasto2_{time.strftime('%Y%m%d_%H%M')}.csv"), "wb") as f:
                    f.write(csv_todas())
                for a in os.listdir(medir.CARPETA):
                    origen = os.path.join(medir.CARPETA, a)
                    if os.path.isfile(origen):
                        shutil.copy2(origen, dest)
                fotos = os.path.join(medir.CARPETA, "fotos")
                if os.path.isdir(fotos):
                    shutil.copytree(fotos, os.path.join(dest, "fotos"), dirs_exist_ok=True)
                os.sync()
            except OSError as e:
                return self._enviar(500, {"error": f"No se pudo copiar: {e}"})
            return self._enviar(200, {"ok": True, "destino": dest})
        else:
            return self._enviar(404, {"error": "no encontrado"})
        if not ok:
            return self._enviar(409, {"error": "Espera a que termine la operacion en curso."})
        return self._enviar(200, {"ok": True})


def main():
    global DISP
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--simulado", action="store_true", help="sin sensores, con datos sinteticos")
    p.add_argument("--puerto", type=int, default=8000)
    a = p.parse_args()
    print("Abriendo sensores...")
    DISP = medir.Dispositivo(simulado=a.simulado)
    for n, e in DISP.estado_sensores.items():
        print(f"  {n:13s} {'OK ' if e['ok'] else 'NO '} {e['detalle']}")
    srv = ThreadingHTTPServer(("0.0.0.0", a.puerto), Manejador)
    print(f"\nInterfaz lista: http://192.168.4.1:{a.puerto}  (Ctrl+C para cerrar)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrado.")


if __name__ == "__main__":
    main()
