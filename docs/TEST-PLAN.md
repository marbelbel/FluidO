# Plan de pruebas de FluidOS 0.1.0-alpha

La comprobación sintáctica no demuestra que el sistema arranque. No se debe publicar esta versión como estable hasta completar las pruebas siguientes.

## En Oracle VirtualBox

- [ ] Arranque BIOS hasta el entorno Live.
- [ ] Arranque UEFI en una segunda VM y comprobar el splash PNG.
- [ ] En BIOS, comprobar si el firmware/consola muestra el BMP; no asumir que `vt(4)` lo muestra.
- [ ] Inicio automático de sesión del usuario Live `fluid`.
- [ ] El escritorio Wayfire aparece; si no aparece, registrar el error de DRM/KMS por separado.
- [ ] Dock, barra, lanzador, reloj y paneles responden.
- [ ] La terminal no aparece en dock, lanzador ni atajos normales.
- [ ] Firefox y DHCP funcionan.
- [ ] El instalador rechaza un disco con particiones.
- [ ] Instalación en un VDI vacío en modo BIOS y en otra VM en modo UEFI.
- [ ] Primer arranque desde el VDI instalado.
- [ ] La cuenta `fluid` inicia sesión y Wayfire abre FluidOS automáticamente.
- [ ] Apagado y reinicio.

## En hardware real

- [ ] GPU Intel y AMD.
- [ ] NVIDIA con el controlador adecuado o documentar incompatibilidad.
- [ ] Ethernet y Wi-Fi, reconexión tras suspensión.
- [ ] Audio, USB, Bluetooth, webcam y monitores externos.
- [ ] Suspensión y reanudación.
- [ ] Actualizaciones y recuperación tras errores.

## Registro

Guarda SHA256 de la ISO, modelo de equipo/VM, modo de firmware, memoria asignada, resultado y logs. No marques un punto aprobado por el mero hecho de que la ISO se haya compilado.
