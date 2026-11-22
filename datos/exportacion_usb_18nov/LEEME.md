# Exportación a memoria USB (18 nov 2026)

Archivos CSV tal como los copió la interfaz (botón *Copiar a USB*) en la prueba con una memoria real. `mediciones_maspasto2_20260415_1356.csv` es el consolidado de las 57 mediciones guardadas; los demás son los archivos diarios (mediciones, pares crudos y referencias). El nombre lleva la fecha de la Raspberry Pi, que arranca con una fecha errada; la hora válida de cada fila es `hora_celular`.

De las 32 fotos que también se copiaron solo se incluye aquí la de la prueba en casa del 11 de noviembre (`fotos/`); las demás están en las carpetas de cada sesión de `MasPasto2_resultados/` y, renombradas, en `conjunto_de_prueba/fotos/`.

El conjunto de prueba (`../conjunto_de_prueba/`) se arma desde estos archivos con `MasPasto2_resultados/analisis/armar_entregable.py`.
