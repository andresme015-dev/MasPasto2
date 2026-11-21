# Firmware del módulo cenit (ESP32)

`firmware_zenit_as7343/firmware_zenit_as7343.ino` es el firmware que tuvo el ESP32 del cenit desde el 26 de octubre de 2026 (ver cómo se identificó en [`../VERSIONES.md`](../VERSIONES.md)).

## Qué hace
- Lee el AS7343 por I²C (SDA = GPIO21, SCL = GPIO22) en el modo de 18 canales, con integración de 182,4 ms (ATIME = 99, ASTEP = 655).
- Ganancia adaptativa de 0,5× a 64×: baja la ganancia si el canal más alto de los 18 (VIS incluido) llega al 90 % de la escala y la sube si queda por debajo del 40 %.
- Envía cada segundo un paquete JSON por UDP al puerto 5005 de la Raspberry Pi (192.168.4.1) con número de secuencia, cuentas de los 12 canales espectrales y del canal sin filtro, ganancia, tiempo de integración, banderas de saturación e intensidad de la señal de radio.
- Escucha órdenes en el puerto 5006: `G<n>` fija la ganancia en el índice n; `GA` vuelve a la adaptativa.
- Conecta el Wi-Fi aunque el sensor no responda, reintenta el sensor cada segundo y envía un paquete de aviso (`"sensor":"AS7343_error"`). Desactiva el ahorro de energía del Wi-Fi para que la batería externa no se apague por bajo consumo.

## Cómo cargarlo
1. Arduino IDE con el soporte de placas ESP32 instalado; placa **ESP32 Dev Module**.
2. Librería **Adafruit AS7343** (instala también Adafruit BusIO) desde el gestor de librerías.
3. Abrir `firmware_zenit_as7343/firmware_zenit_as7343.ino` y escribir en `PASS_AP` la clave de la red *PasturaMetrics* de la Raspberry Pi. Dejar `USAR_RED_CASA = false` (con `true` se conecta a otra red Wi-Fi, para pruebas, y hay que llenar `SSID_CASA`, `PASS_CASA` e `IP_RPI_CASA`).
4. Si se cambia el sensor físico, ajustar `ID_SENSOR` (queda en cada fila de datos).
5. Cargar. En el monitor serie (115200 baudios) aparece la conexión y cada paquete.

`PIN_CARGA` permite activar una carga periódica para baterías que se apagan con bajo consumo; está desactivada (`-1`) y no se usó.

## Versiones anteriores
- `firmware_zenit_as7343_21oct/` y `firmware_zenit_as7343_capsula_ptfe/`: misma lógica; si el sensor no responde al arrancar, el ESP32 se detiene sin conectar el Wi-Fi. La segunda, con la etiqueta `capsula_ptfe`, es la que el autor indicó como última carga; ningún dato del proyecto se tomó con ella. Para saber cuál tiene el ESP32, encenderlo y correr `python3 receptor_zenit.py` en la Raspberry Pi: el campo `config` de los paquetes dice `cenit_3mm` (versión principal) o `capsula_ptfe`.
- `firmware_zenit/`: versión con el AS7341, el espectrómetro que se reemplazó.
