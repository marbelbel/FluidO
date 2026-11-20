# Avisos de terceros

FluidOS no sustituye ni elimina las licencias de las piezas que integra.

## FreeBSD

El sistema base y el kernel proceden de FreeBSD 14.5-RELEASE. El aviso de copyright y las condiciones de licencia del sistema base se encuentran en el archivo `COPYRIGHT` de la distribución incluida en el medio. Deben conservarse en las imágenes instaladas y redistribuidas.

Proyecto: https://www.freebsd.org/

## mfsBSD

mfsBSD se utiliza como constructor de la imagen Live. Su licencia BSD de dos cláusulas se incluye en `MFSBSD-BSD-2-Clause.txt`. El script de compilación fija la revisión `6e48fa48ebbb25953a7764a8f3cfda443fb9a768` para que la construcción sea reproducible.

Proyecto: https://github.com/mmatuska/mfsbsd

## Paquetes

Wayfire, Wayland, GTK 3, GTK Layer Shell, Python, Firefox, Foot, DBus, seatd, drm-kmod y sus dependencias conservan las licencias y avisos suministrados por sus respectivos proyectos y paquetes. Consulta los manifiestos de paquetes y sus directorios `share/licenses` en la instalación.
