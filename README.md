# MasPasto2

Dispositivo portátil de bajo costo para medir pasturas: dos espectrómetros AS7343 (uno mira el pasto y otro el cielo) entregan NDVI y NDRE corregidos por la luz del momento; un LiDAR mide la altura del dosel y un modelo estima la masa de forraje. Se opera desde el celular.

Proyecto de grado en Ingeniería Electrónica, Universidad de los Andes (2026-20).
Autor: Andrés Felipe Méndez Martínez. Asesor: Fredy Enrique Segura Quijano. Coasesora: Diana Marcela Valencia (AGROSAVIA).

> **Estado.** Prototipo validado en laboratorio y en campo (ver el documento final, Sección 8 y Apéndice B). El modelo de biomasa es **demostrativo**: está entrenado con datos públicos de Australia y no está calibrado para pasturas colombianas.

---

## Contenido

| Carpeta | Qué hay |
|---|---|
| [`raspberry_pi/`](raspberry_pi/) | Programas del módulo nadir (Raspberry Pi 4), **copia exacta** de los que corren en el equipo (verificados con su huella MD5, ver [`VERSIONES.md`](VERSIONES.md)). |
| [`firmware_cenit/`](firmware_cenit/) | Firmware del ESP32 del módulo cenit (Arduino IDE). |
| [`modelo/`](modelo/) | Cuaderno con el que se entrenó el modelo de biomasa que está instalado en el equipo. |
| [`datos/MasPasto2_resultados/`](datos/MasPasto2_resultados/) | Datos crudos de las 13 sesiones de prueba, tablas derivadas y programas de análisis que producen las cifras y figuras del documento final. |
| [`datos/conjunto_de_prueba/`](datos/conjunto_de_prueba/) | Las mediciones reales del dispositivo exportadas por USB, depuradas: 31 válidas sobre superficies reales, con su registro completo y fotos. |
| [`docs/`](docs/) | Instalación y uso. |

## Cómo funciona

```
 Módulo cenit (mira al cielo)                Módulo nadir (mira al pasto)
 AS7343 bajo difusor de PTFE                 AS7343 · LiDAR TF-Nova · BMP280 · cámara OV5647
 ESP32 ──── UDP por Wi-Fi (1 paquete/s) ───► Raspberry Pi 4 (punto de acceso "PasturaMetrics")
                                                     │
                                                     └── HTTP ──► celular: http://192.168.4.1:8000
```

Cada medición toma cinco pares de lecturas simultáneas nadir/cenit. El cociente nadir/cenit, dividido por el mismo cociente sobre una lámina de referencia, da la reflectancia relativa de cada canal; con ella se calculan:

- **NDVI** = (NIR 855 − F6 640) / (NIR 855 + F6 640)
- **NDRE₂** = (F8 745 − F7 690) / (F8 745 + F7 690) — el NDRE que usa el dispositivo
- **NDRE₁** = (NIR 855 − F8 745) / (NIR 855 + F8 745) — se guarda, pero no ordenó las superficies en campo

La altura es la distancia al suelo (medida una vez por sesión) menos la distancia al pasto, con la calibración del LiDAR `d = 1,0275·d_L − 0,80 cm`. La biomasa sale de un Random Forest con NDVI, altura y su producto como entradas.

## Inicio rápido

1. **Hardware y conexiones:** [`docs/instalacion.md`](docs/instalacion.md).
2. **Copiar los programas** de `raspberry_pi/` a `~/maspasto2/` en la Raspberry Pi (los programas buscan el modelo y los datos en esa ruta).
3. **Instalar las librerías** de [`requirements.txt`](requirements.txt).
4. **Cargar el firmware** del cenit con el Arduino IDE, poniendo la clave de la red del dispositivo (ver [`firmware_cenit/`](firmware_cenit/)).
5. **Medir:** `cd ~/maspasto2 && python3 servidor.py` y abrir `http://192.168.4.1:8000` en el celular conectado a la red *PasturaMetrics*. Protocolo completo en [`docs/uso.md`](docs/uso.md).

Para probar la interfaz sin sensores: `python3 servidor.py --simulado`.

## Resultados principales (documento final, Sección 8)

| Prueba | Criterio de la propuesta | Resultado |
|---|---|---|
| E1 Repetibilidad | CV < 5 % | CV < 1 % en todos los canales; NDVI 0,7563 ± 0,0003 |
| E2 Exactitud relativa | Mismo orden que la fracción verde | Spearman 0,952 (NDRE₂) y 0,905 (NDVI) en 8 superficies |
| E3 Temperatura | Cambio < 5 % | < 0,1 % entre 25,2 y 28,6 °C (≤ 0,03 %/°C) |
| E4 Compensación de luz | Corregido más estable | NDVI cambia 0,004 con la luz al 51 % (0,033 sin corregir) |
| Modelo en el equipo | < 200 ms | 27,3 ms por inferencia; R² = 0,48 en validación cruzada (datos públicos) |
| Conjunto de prueba | ≥ 20 mediciones reales exportables por USB | 31 mediciones válidas |

## Reglas de operación que evitan daños y datos malos

- **Nunca conectar ni desconectar sensores I²C con el equipo encendido.** Primero `sudo shutdown now`, luego desconectar la batería.
- Cerrar los programas con **Ctrl+C**, nunca con Ctrl+Z.
- **No correr a la vez** `servidor.py` y `caracterizacion_espectro.py`: los dos leen el mismo cenit y quedan lecturas sin pareja. Antes de medir, `pgrep -af python3` debe estar vacío.
- La referencia se mide **siempre a la misma distancia** (10 cm bajo el nadir) y debe **llenar el campo de visión**; con sol directo se usa la cartulina gris, porque el cartón blanco satura el nadir.
- La superficie medida debe cubrir unos **70 cm** alrededor del punto (el 90 % de la señal viene de un círculo de ~71 cm con el chip a 55 cm).
- La batería del cenit debe ser de un tipo que **no se apague por bajo consumo**.

## Limitaciones conocidas

- El modelo de biomasa no está calibrado para Colombia; sobre tierra o grava estima valores falsos por el desfase de la altura. Se necesita calibrarlo con cortes y pesaje.
- La altura en campo no se comparó contra una regla; se vio un desfase de ~4 cm cuando la distancia al suelo se escribe a mano.
- El inclinómetro (MPU-6050) y el reloj (DS3231) tienen programa de prueba pero no quedaron integrados; la hora de cada medición la pone el celular.
- La ganancia adaptativa del nadir llega hasta 64×; con poca luz el rojo queda con pocas cuentas.

## Documento y citación

Méndez Martínez, A. F. (2026). *MasPasto2: diseño, implementación y validación de un dispositivo portátil de campo para la estimación proximal de masa de forraje en pasturas tropicales mediante teledetección espectral con corrección de irradiancia y aprendizaje automático*. Proyecto de grado, Ingeniería Electrónica, Universidad de los Andes.

## Licencia

Por definir por el autor antes de publicar el repositorio.
