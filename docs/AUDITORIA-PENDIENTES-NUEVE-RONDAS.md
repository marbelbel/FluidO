# Auditoría de lo que falta en FluidOS

Auditoría basada en la rama `main` después del commit de Fase 2 `bef53dc38a47a3c4a6f36b9855639fea915714aa`.

## Base que ya existe

- FreeBSD 14.5 amd64 y constructor Live + Installer mediante mfsBSD.
- Escritorio GTK 3/Wayfire con barra superior, Dock, lanzador, fondo, panel del sistema, archivos y accesos a Firefox/LibreOffice.
- Preferencias guardadas, temas claro/oscuro básicos y búsqueda de nombres de archivos del perfil.
- Instalador de consola experimental que detecta un disco vacío, exige confirmación y configura ZFS/UEFI o BIOS.
- Formato `.fapp` con manifiesto, límites de tamaño, comprobación SHA-256 y rechazo de rutas inseguras/enlaces/scripts de instalación.
- Centro de aplicaciones para instalar paquetes `.fapp` locales, no un catálogo remoto.
- Copia manual y restauración validada del perfil; administración de usuarios por CLI y, con esta fase, panel gráfico.
- Suite de pruebas de sintaxis y pruebas unitarias para las utilidades.

## Trabajo pendiente por ronda

| Ronda | Pendientes de desarrollo | Cómo se considerará terminada |
|---|---|---|
| 1. Escritorio | Gestión avanzada de ventanas, mosaico utilizable, cambio/organización de espacios, widgets, gestos táctiles, escalado por pantalla y temas completos | Pruebas de ventanas reales, varios monitores, ratón/táctil y sesiones prolongadas |
| 2. Live e instalación | Instalador gráfico, instalación desatendida con fichero de respuesta, modo persistente USB, recuperación/rollback, notificaciones con historial, catálogo de apps | Instalación y recuperación repetibles en VM y equipos de prueba sin tocar discos ajenos |
| 3. Usuarios y mantenimiento | Actualizador de sistema y aplicaciones, programación/pausa, copias automáticas y restauración guiada, perfiles y políticas de sesión, energía/tapa de portátil | Pruebas de actualización interrumpida, rollback, multiusuario y hardware portátil |
| 4. IA | Motor local seleccionable, proveedor remoto optativo, gestor de credenciales seguro, permisos/consentimientos por acción, búsqueda semántica y transferencia entre dispositivos | Acciones del sistema con permisos comprobados, funcionamiento offline y pruebas de privacidad |
| 5. Personalización | Fondos, iconos, fuentes, sonidos, animaciones, widgets, reglas de adaptación tablet/escritorio y preferencias aplicadas al reiniciar | Cada opción visible cambia realmente el sistema y persiste tras reinicio |
| 6. Voz y búsqueda | Servicio de voz, idioma/modelo, órdenes permitidas, búsqueda de contenido y resultados con permisos | Pruebas de voz sin red, búsqueda indexada y control de acceso a resultados |
| 7. Seguridad | Cifrado de disco por defecto, llaves de recuperación, sandbox de aplicaciones, permisos aplicados por el sistema, firmas y repositorios confiables, registro/alertas de acceso | Auditoría de amenazas, pruebas de aislamiento, recuperación de claves y actualización segura |
| 8. Hardware | Port AArch64 real, selección de kernel/paquetes por arquitectura, soporte comprobado Intel/AMD/NVIDIA según modelo, varias pantallas, audio, Wi-Fi, Bluetooth, suspensión y periféricos | Matriz publicada de equipos probados, no promesas universales |
| 9. Aplicaciones | Tienda con repositorio firmado, llaves de publicación, actualizador transaccional por paquete, navegador propio, SDK, herramientas y documentación para desarrolladores | Crear, firmar, instalar, actualizar, revertir y eliminar una app de extremo a extremo |

## Bloqueos que necesitan decisiones o recursos

- **IA local:** hace falta seleccionar modelos compatibles con el tamaño de RAM/CPU/GPU. Un modelo grande no cabe en todos los equipos.
- **IA remota:** necesita proveedor, conexión y credenciales configuradas por el propietario. Nunca se debe incluir una clave privada en Git.
- **Tienda firmada:** hace falta una clave privada de publicación guardada fuera del repositorio y una clave pública integrada en FluidOS.
- **Cifrado completo:** debe diseñarse junto con el particionado, el arranque y la recuperación de claves. No se activa con un simple cambio de configuración.
- **ARM64 y GPU:** requiere construir y probar imágenes por arquitectura y probar modelos concretos de dispositivo/controlador.
- **Instalación física:** requiere discos de prueba vacíos y pruebas explícitas BIOS/UEFI, red, gráficos, sonido y recuperación.

## Política de estado

Una pantalla, una opción guardada o un archivo de configuración no cuentan como función terminada. Cada función debe tener servicio/backend, integración de escritorio, pruebas automatizadas y una prueba de aceptación en FreeBSD. No instalar la alpha en un disco con datos importantes.
