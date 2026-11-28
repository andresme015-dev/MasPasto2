# Instalación

## Hardware

| Módulo | Componente | Conexión |
|---|---|---|
| Nadir | Raspberry Pi 4 con Ubuntu (el prototipo usa Ubuntu 26.04 LTS) | — |
| Nadir | Espectrómetro AS7343 en tarjeta Adafruit (con cambio de nivel) | I²C, dirección 0x39 |
| Nadir | LiDAR Benewake TF-Nova | Adaptador USB-serie, aparece como `/dev/ttyUSB0`, 115200 baudios |
| Nadir | BMP280 (temperatura de la caja) | I²C, dirección 0x76 (CSB a 3,3 V y SDO a tierra) |
| Nadir | Cámara OV5647 | Conector CSI |
| Nadir | Batería externa USB de 5 V | Debe entregar la corriente de la Pi y del LiDAR juntos; con una de menos corriente aparecen avisos de bajo voltaje y errores del LiDAR |
| Cenit | ESP32 Dev Module | — |
| Cenit | Espectrómetro AS7343 en tarjeta Adafruit | I²C del ESP32: SDA = GPIO21, SCL = GPIO22 |
| Cenit | Caja de paredes internas negras con techo de PTFE de 2 mm al ras y bordes sellados; sensor a unos 3 mm bajo el techo; atenuador de la misma lámina de PTFE de 2 mm encima | — |
| Cenit | Batería externa USB | Que no se apague por bajo consumo |
| Opcional | MPU-6050 (0x69, AD0 a 3,3 V) y DS3231 (0x68) | Tienen programa de prueba; no quedaron integrados en el montaje final |

Los sensores I²C del nadir van al bus 1 de la Raspberry Pi. El nadir mira al suelo por una ventana de la caja, sin óptica adicional; en campo el chip quedó a unos 55 cm del suelo.

**Nunca conectar ni desconectar un sensor con el equipo encendido**: bloqueó el bus I²C durante el desarrollo.

## Red

La Raspberry Pi crea un punto de acceso Wi-Fi llamado **PasturaMetrics** (WPA2, 2,4 GHz) y queda en **192.168.4.1**. El ESP32 se asocia a esa red con el identificador y el canal del punto de acceso fijos, y el celular se conecta a la misma red para usar la interfaz.

El punto de acceso se configuró en el sistema operativo de la Pi, aparte de estos programas, que no cambian ninguna configuración de red. Si se usa otra Raspberry Pi hay que crear un punto de acceso con ese nombre, WPA2 en 2,4 GHz y la dirección 192.168.4.1, y poner la misma clave en el firmware (`PASS_AP`). Con WPA (sin el 2) el ESP32 no se asociaba de forma confiable.

## Programas de la Raspberry Pi

1. Copiar el contenido de `raspberry_pi/` (sin `versiones_anteriores/`) a `~/maspasto2/`. Los programas usan esa ruta para el modelo, la tabla de factores y los datos.
2. Habilitar I²C y la cámara en la Raspberry Pi.
3. Instalar las librerías de `requirements.txt` (por ejemplo `python3 -m pip install -r requirements.txt`; según el sistema, `picamera2` puede venir de los paquetes del sistema operativo). En campo la Pi no tiene internet: todo se instala antes.
4. Probar cada sensor por separado, con el resto de programas cerrados:
   ```
   cd ~/maspasto2
   python3 test_as7343.py --una      # una lectura del espectrómetro del nadir
   python3 test_bmp280.py            # temperatura
   python3 test_tfnova.py            # distancia del LiDAR
   python3 test_camara.py            # foto en ~/maspasto2/fotos
   python3 receptor_zenit.py         # paquetes del cenit (con el ESP32 encendido)
   ```
5. Probar la interfaz sin sensores: `python3 servidor.py --simulado` y abrir `http://192.168.4.1:8000` (o la dirección de la Pi en la red donde esté).

## Firmware del cenit

Ver [`../firmware_cenit/LEEME.md`](../firmware_cenit/LEEME.md).

## Calibraciones que trae el equipo

- **Factores de ganancia** (`factores_ganancia.json`): son propios de los dos sensores del prototipo (A en el nadir y B en el cenit). Si se cambia un sensor hay que medirlos de nuevo con `caracterizacion_espectro.py ganancias` (documento final, Apéndice B.8) o borrar la tabla para usar las ganancias nominales (error de hasta 0,003 de NDVI).
- **Oscuridad**: la guarda `caracterizacion_espectro.py` en `~/maspasto2/datos_espectro/oscuridad_A.json` y `oscuridad_B.json`; es de 0 cuentas hasta 16× y de pocas cuentas a ganancias altas.
- **LiDAR**: `d = 1,0275·d_L − 0,80 cm`, en `CONFIG_DEFECTO` de `medir.py` (`lidar_cal_a`, `lidar_cal_b`). Calibrado entre 15 y 150 cm.
- El factor entre los dos espectrómetros y la transmitancia del difusor **no** se guardan: los cancela la referencia que se mide en cada sesión.
