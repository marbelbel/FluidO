# Fases 4 y 5: integración verificable

## Fase 4: asistente local

- Incluye una ventana GTK llamada **Asistente local**.
- Busca nombres de archivos dentro del directorio personal, sin seguir enlaces simbólicos ni indexar carpetas ocultas.
- Muestra información básica del sistema y fecha/hora.
- Puede abrir aplicaciones incluidas en una lista cerrada (Firefox, LibreOffice, Ajustes, Centro de aplicaciones y Usuarios).
- Abrir una aplicación o un archivo requiere confirmación explícita. Reiniciar/apagar requiere otra confirmación.
- Nunca pasa el texto del usuario a una shell ni ejecuta órdenes arbitrarias.
- Se ejecuta sin red y no sube ficheros a ningún servidor.

**Límites:** esto es un asistente local de órdenes, no un modelo de IA generativa. No incluye todavía reconocimiento de voz, proveedor remoto, sincronización ni transferencia entre dispositivos. El buscador inicializa una búsqueda por nombre, no una indexación semántica de contenidos.

## Fase 5: personalización

- Preferencias versionadas y migración del antiguo esquema 1 al esquema 2.
- Temas Liquid Glass, oscuro y claro; color de acento validado.
- Tres fondos integrados, tres tamaños de Dock y modo escritorio/tableta/automático.
- Distribución de escritorios virtuales Wayfire 1x1, 2x2, 3x2 o 4x2.
- Preferencia de animaciones aplicada a la lista de plugins de Wayfire.
- Guardado atómico de preferencias con permisos privados del usuario.

**Límites:** las preferencias de shell (tema, fondo y Dock) requieren cerrar y volver a iniciar la sesión. El modo automático usa el ancho de pantalla como heurística, no una detección certificada de hardware táctil. No se incluyen aún paquetes de iconos/fuentes/sonidos, widgets ni gestos multitáctiles.

## Arranque gráfico y VirtualBox

Se elimina la carga incondicional de `i915kms` y `amdgpu` desde `rc.conf`. Un servicio los carga después del arranque de servicios, y solo si `pciconf` identifica un controlador de pantalla Intel o AMD. El adaptador virtual estándar de VirtualBox (vendor `0x80ee`) no activa esos módulos.

Esto evita cargar a ciegas módulos DRM físicos en una VM, pero **no demuestra por sí solo que el reinicio observado esté resuelto**. Hace falta volver a arrancar la ISO en la misma configuración y revisar la pantalla de error si persiste.

## Validación necesaria

La suite incluida comprueba la lógica de búsqueda/allowlist, protección de rutas, migración/validación de preferencias y escritura de la configuración Wayfire. La validación en Linux no sustituye una compilación FreeBSD 14.5 ni el arranque BIOS/UEFI/VirtualBox.
