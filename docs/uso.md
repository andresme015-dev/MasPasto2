# Uso en campo

## Antes de salir
- Baterías cargadas en los dos módulos.
- Lámina de referencia (cartulina gris mate; el cartón blanco satura el nadir con sol directo) y una caja o soporte que la deje **a 10 cm bajo la ventana del nadir**, siempre a esa misma distancia.
- Celular con navegador.

## Encender y conectar
1. Conectar los sensores **con todo apagado** y luego encender los dos módulos.
2. Conectar el celular a la red **PasturaMetrics**.
3. Entrar a la Raspberry Pi (por ejemplo `ssh` desde un portátil en la misma red) y revisar que no haya otro programa leyendo los sensores:
   ```
   pgrep -af python3
   ```
   No debe aparecer nada. Si aparece `caracterizacion_espectro.py` o un `servidor.py` anterior, cerrarlo antes.
4. Iniciar la interfaz:
   ```
   cd ~/maspasto2
   python3 servidor.py
   ```
   La consola muestra el estado de cada sensor. Se cierra con **Ctrl+C** (nunca Ctrl+Z, que lo deja corriendo en segundo plano).
5. En el celular abrir **http://192.168.4.1:8000**.

## Una sesión
1. **Inicio:** revisar que estén en verde el nadir, el cenit, el LiDAR, la temperatura, la cámara, el modelo y los factores de ganancia.
2. **Distancia al suelo:** con el bastón vertical sobre una superficie dura y plana, tocar *Medir suelo* (mediana de 20 lecturas del LiDAR). No medirla sobre el pasto: la altura saldría cercana a cero. Si se escribe a mano, anotar que fue así.
3. **Referencia:** poner la lámina bajo el nadir, a 10 cm, sin sombras distintas de la de la propia caja, y tocar *Blanco* (10 pares nadir–cenit). Repetirla si pasan más de 30 minutos (la interfaz avisa) o si el sol cambia mucho de altura.
4. **Medir:** ubicar el bastón vertical en el punto, escribir el nombre del punto y tocar *Medir*. Toma 5 pares, calcula los índices, la altura, la temperatura, la foto y la biomasa; tarda unos 16 s. Hacer **tres tomas por punto**, la última después de levantar y volver a poner el bastón.
5. **Avisos:** repetir la toma si la interfaz avisa que
   - el CV del cociente pasó del 3 % (algo dio sombra a un solo módulo o la luz cambió durante la toma),
   - la luz del cenit cayó por debajo del 80 % de la que había al medir la referencia (nube),
   - faltó el cenit (los índices quedan sin corrección de luz),
   - la distancia al suelo es de otro día.

   En el análisis se descartaron las tomas con luz menor del 80 % o con CV del cociente mayor de 5 %.

## Qué medir y qué no
- La superficie debe ser homogénea en unos **70 cm** alrededor del punto: con el chip a 55 cm, el 90 % de la señal viene de un círculo de ~71 cm.
- No hacer sombra con el cuerpo sobre el punto ni sobre el cenit. Una sombra que tapa el pasto pero no el cenit sesgó el NDVI hasta en 0,025.
- Los índices son relativos a la referencia de la sesión: sirven para comparar puntos medidos con la misma referencia.

## Datos
Todo queda en `~/maspasto2/datos_espectro/mediciones/`:

| Archivo | Contenido |
|---|---|
| `mediciones_AAAAMMDD.csv` | Una fila por medición: hora del celular, índices, reflectancias de F6 a NIR, CV del cociente, luz frente a la referencia, ganancias, distancia del LiDAR, suelo, altura, temperatura, biomasa, foto y avisos. |
| `crudo_AAAAMMDD.csv` | Cuentas crudas de cada par nadir/cenit. |
| `blancos_AAAAMMDD.csv` | Cada referencia medida. |
| `fotos/` | Una foto por medición, con su número y hora. |

La hora válida es la del celular (`hora_celular`, en UTC). La Raspberry Pi no tiene reloj con pila: arranca con una fecha errada, y esa fecha es la que llevan los nombres de los archivos.

**Exportar:**
- Al celular: pantalla *Datos* → descargar el CSV.
- A memoria USB (FAT32 o exFAT): montarla en `/mnt/usb` (o dejar que el sistema la monte en `/media`) y tocar *Copiar a USB*. Se crea la carpeta `MasPasto2` con un CSV consolidado, los archivos diarios y las fotos; la interfaz dice cuántos archivos copió.
- A un computador: `scp andresmendez@192.168.4.1:~/maspasto2/datos_espectro/mediciones/* .` desde una terminal del computador (no desde dentro de la sesión `ssh`). El usuario es el de la Pi del prototipo; cambiarlo si es otra.

## Apagar
Desde la sesión en la Pi: Ctrl+C para cerrar la interfaz y luego
```
sudo shutdown now
```
Esperar a que se apague antes de desconectar la batería; desconectarla con la Pi encendida puede dejar archivos vacíos (pasó con una foto el 11 de noviembre).

## Programa de caracterización
`caracterizacion_espectro.py` hace las pruebas de laboratorio del Apéndice B del documento (registro, ganancias, oscuridad, intercomparación, PTFE y saturación). `python3 caracterizacion_espectro.py -h` muestra los modos y las opciones. Guarda las lecturas crudas en `~/maspasto2/datos_espectro/`. No se debe correr al mismo tiempo que `servidor.py`.
