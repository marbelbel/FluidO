# Estado de FluidOS 0.1.0-alpha

## Comprobaciones realizadas en el entorno de desarrollo

- Sintaxis de los scripts de shell (`sh -n`).
- Sintaxis de los módulos Python del escritorio, utilidades .fapp y pruebas unitarias (`py_compile`).
- Comprobaciones del inventario, marca, rutas y protecciones del instalador (`tests/check-source.sh`).
- Formato, CRC y dimensiones de las imágenes de arranque: BMP paletizado de 8 bits y PNG RGBA, ambos de 320 × 200.
- Prueba del parcheador de mfsBSD con los bloques de Makefile previstos y comprobación de que no aplica el parche dos veces.
- Cinco pruebas unitarias para validar paquetes .fapp y la aplicación repetida del integrador de las nueve rondas.

## Comprobaciones que faltan

- Recompilación de la ISO después de integrar la ampliación de las nueve rondas. La revisión anterior sí generó una ISO en GitHub Actions con FreeBSD 14.5 amd64 el 20-11-2026.
- Arranque BIOS y UEFI desde la ISO.
- Prueba del escritorio Wayfire en hardware gráfico compatible.
- Instalación en un VDI vacío y primer arranque desde el disco instalado.
- Pruebas de dispositivos físicos, red, audio, suspensión y recuperación.

La versión continúa siendo **alpha experimental**. Que el código pase las comprobaciones estáticas no significa que la ISO se haya construido o arrancado.
