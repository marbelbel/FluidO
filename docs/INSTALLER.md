# Instalador de FluidOS

La ISO Live incluye el instalador en el lanzador, dentro de **Aplicaciones > Instalar FluidOS**. La misma ISO sirve para probar el escritorio sin instalar o para instalar en un disco.

## Antes de empezar

- Prueba primero en una máquina virtual nueva.
- Crea un disco virtual VDI/VHD nuevo y vacío. El instalador se detiene si detecta una tabla de particiones.
- Haz copia de seguridad de cualquier dato importante.
- Arranca la ISO en el mismo modo de firmware que quieras instalar (BIOS o UEFI).
- Comprueba dos veces el disco de destino. En FreeBSD puede llamarse `ada0`, `da0`, `nvd0`, `nda0` o `vtbd0`.

## Qué hace

El instalador localiza `base.txz` y `kernel.txz` en la sección de distribución de la ISO especial mfsBSD. Usa `zfsinstall` para crear GPT y ZFS en el disco vacío, extraer FreeBSD 14.5 y configurar el cargador para BIOS o UEFI. Después instala los paquetes de FluidOS, copia el escritorio y los avisos legales, crea el usuario `fluid` y solicita una contraseña.

## Límites

- La instalación destruye el contenido del disco elegido. Solo debe usarse un disco nuevo y vacío.
- Si el disco contiene una tabla de particiones, el instalador se detiene y no la borra.
- La instalación de paquetes necesita conexión a Internet.
- No hay aún un desinstalador ni recuperación gráfica.
- No se ha validado todavía el instalador en una VM arrancada de principio a fin ni en hardware real.

No continúes si aparece un error. Guarda el mensaje completo y apaga la VM sin tocar el disco del ordenador anfitrión.
