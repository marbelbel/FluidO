# FluidOS: integración de las nueve rondas

Este documento distingue funciones presentes, bases añadidas y trabajo que necesita desarrollo y pruebas. No convierte un diseño en una función operativa.

| Ronda | Requisito | Estado verificable en esta base |
|---|---|---|
| 1 | Escritorio Liquid Glass, dock, barra superior, escritorios virtuales, ventanas y adaptación | **Base existente:** GTK/Wayfire, dock, barra superior, fondo propio y plugin de escritorios virtuales. **Añadido:** preferencias persistentes de apariencia y selector de modo. Falta gestor completo de ventanas, temas aplicados de extremo a extremo, widgets y pruebas táctiles. |
| 2 | Live, instalación gráfica/automática, recuperación, IA, tienda, aplicaciones y notificaciones | **Base existente:** arranque Live e instalador experimental. **Añadido:** panel de ajustes y primera herramienta de paquetes `.fapp`. Falta instalador gráfico real, recuperación automatizada, tienda, IA y centro de notificaciones. |
| 3 | Usuarios, actualizaciones, copias, seguridad, hardware y red | **Base existente:** cuenta `fluid`, DHCP y contraseña durante la instalación. **Añadido:** herramienta manual para copias con SHA-256. Falta gestión completa de usuarios, servicio de actualización, restauración guiada, cifrado y control de energía. |
| 4 | IA conversacional, búsqueda, intercambio y sincronización | **Pendiente:** solo se guarda la preferencia de modo de IA. No hay proveedor, motor local, asistente ni sincronización implementados. |
| 5 | Personalización visual y escritorios múltiples | **Base existente:** Wayfire con `expo`, `vswitch`, `grid` y dock. **Añadido:** preferencias guardables. Falta aplicar todas las opciones al gestor gráfico y crear widgets/gestos. |
| 6 | Asistente por voz/texto y búsqueda global | **Pendiente:** no hay reconocimiento de voz, asistente ni buscador global operativo. |
| 7 | Cifrado integral, permisos por aplicación, defensa, llaves físicas y copias | **Añadido:** formato `.fapp` valida hashes y rechaza rutas peligrosas, enlaces y scripts de instalación. **Pendiente:** firmas, sandbox, enforcement de permisos, cifrado de disco por defecto, llaves FIDO y alertas de intrusión. |
| 8 | Intel/AMD/ARM64, gráficas, pantallas y periféricos | **Base actual:** constructor amd64. **Pendiente:** port a AArch64, matriz de GPU, escalado, monitores y pruebas de hardware. No se promete compatibilidad universal. |
| 9 | Aplicaciones nativas, tienda, actualizaciones, ofimática y SDK | **Añadido:** especificación y verificador/instalador inicial `.fapp`; suite LibreOffice y paquete de idioma español previstos en la ISO. **Pendiente:** tienda firmada, actualizador por aplicación, SDK, documentación de desarrollador y navegador propio. |

## Orden de trabajo recomendado

1. Hacer que la ISO de amd64 arranque e instalarla en máquinas virtuales y equipos físicos de prueba.
2. Completar la experiencia básica: ajustes aplicados, gestor de archivos, notificaciones, red, audio, suspensión y recuperación.
3. Firmar el formato `.fapp`, desarrollar la tienda y un actualizador transaccional.
4. Añadir aislamiento obligatorio de aplicaciones y cifrado de disco probado.
5. Crear los servicios de IA local/remota, búsqueda, intercambio y sincronización con controles de privacidad.
6. Construir el SDK y validar arquitecturas y dispositivos adicionales.

FluidOS sigue siendo una **alpha experimental**. Antes de instalarlo en un disco con datos, hay que probar en un disco virtual vacío y conservar copias externas.
