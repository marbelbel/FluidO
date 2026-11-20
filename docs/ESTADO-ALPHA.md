# Estado de FluidOS 0.1.0-alpha

## Comprobaciones realizadas en el entorno de desarrollo

- Sintaxis de los scripts de shell (`sh -n`).
- Sintaxis de los tres archivos Python (`py_compile`).
- Comprobaciones del inventario, marca, rutas y protecciones del instalador (`tests/check-source.sh`).
- Formato, CRC y dimensiones de las imágenes de arranque: BMP paletizado de 8 bits y PNG RGBA, ambos de 320 × 200.
- Prueba del parcheador de mfsBSD con los bloques de Makefile previstos y comprobación de que no aplica el parche dos veces.

## Comprobaciones que faltan

- Construcción real con FreeBSD 14.5 amd64.
- Arranque BIOS y UEFI desde la ISO.
- Prueba del escritorio Wayfire en hardware gráfico compatible.
- Instalación en un VDI vacío y primer arranque desde el disco instalado.
- Pruebas de dispositivos físicos, red, audio, suspensión y recuperación.

La versión continúa siendo **alpha experimental**. Que el código pase las comprobaciones estáticas no significa que la ISO se haya construido o arrancado.
