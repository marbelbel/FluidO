# FluidOS

**FluidOS 0.1.0-alpha** es un sistema experimental de escritorio x86-64 basado en FreeBSD 14.5. Utiliza Wayland, Wayfire, GTK 3, GTK Layer Shell y una interfaz propia en Python.

## Qué contiene esta versión

- Una ISO híbrida para iniciar en BIOS o UEFI.
- Modo **Live** para probar el escritorio sin instalarlo en el disco.
- Instalador incluido en el lanzador de Aplicaciones para instalar en un disco virtual nuevo y vacío.
- Arranque automático hacia el escritorio cuando Wayfire y el controlador gráfico son compatibles.
- Splash de arranque Liquid Glass: fondo negro, gota azul de cristal y línea horizontal. La línea es decorativa y no mide el progreso real. Se incluye PNG para el cargador UEFI `vt(4)` y BMP como compatibilidad con consolas `syscons`; mostrarlo depende del firmware y del controlador de consola.
- Foot se conserva para el proceso técnico de instalación y recuperación, pero no aparece en el dock, el lanzador ni en los atajos normales.

**Estado: alpha experimental.** La sintaxis y las comprobaciones estáticas se pueden validar en Linux, pero la ISO requiere una compilación real en FreeBSD y pruebas de arranque BIOS/UEFI. No se afirma que esté lista para instalar en un ordenador con datos importantes.

## Crear la ISO

La compilación está preparada para FreeBSD 14.5 amd64 con conexión a Internet y permisos de `root`:

```sh
su -
cd /ruta/al/repositorio
sh ./build-fluidos.sh
```

Descarga `base.txz` y `kernel.txz` desde el repositorio oficial de FreeBSD, fija una revisión concreta de mfsBSD, instala los paquetes y genera una ISO Live + Installer. El directorio de descarga de FreeBSD es independiente del directorio de trabajo de mfsBSD para evitar que `cp` intente copiar un archivo sobre sí mismo.

También se puede lanzar la compilación desde GitHub Actions: abre **Actions**, selecciona **Build FluidOS Live + Installer ISO** y pulsa **Run workflow**. Descarga el artefacto `FluidOS-0.1.0-alpha-amd64` cuando el trabajo termine correctamente.

## Probar en Oracle VirtualBox

Crea una máquina nueva:

| Ajuste | Valor recomendado |
|---|---|
| Tipo | BSD |
| Versión | FreeBSD (64-bit) |
| RAM | 6 GB mínimo, 8 GB recomendado |
| CPU | 2 |
| Vídeo | VBoxSVGA, 128 MB |
| Aceleración 3D | Desactivada |
| EFI | Primero desactivado; después prueba otra VM con EFI activado |
| Disco | No hace falta para el modo Live |

Monta la ISO como unidad óptica. Para probar la instalación, añade un **VDI nuevo y vacío** de al menos 32 GB y abre **Aplicaciones > Instalar FluidOS**. Nunca selecciones un disco del ordenador anfitrión.

**Compatibilidad gráfica:** VirtualBox puede iniciar el kernel y el entorno Live, pero Wayfire necesita DRM/KMS. El controlador gráfico virtual de VirtualBox puede no proporcionar ese soporte. Un fallo al abrir el escritorio no demuestra por sí solo que el cargador haya fallado. Registra el mensaje y consulta el plan de pruebas.

## Funciones y límites

El panel de sistema muestra datos reales del equipo. Wi-Fi, Bluetooth, brillo, volumen, suspensión, actualizaciones y recuperación gráfica no deben darse por implementados hasta contar con servicios y pruebas reales. Esta edición no es todavía estable.

## Estructura

- `.github/workflows/build-fluidos.yml`: validación y compilación.
- `build-fluidos.sh`: generación de la ISO.
- `desktop/fluidos-shell.py`: escritorio GTK.
- `mfsbsd/`: configuración del constructor Live.
- `customfiles/` y `customscripts/`: archivos añadidos al sistema.
- `artwork/fluidos-splash-master.png`: diseño original de la gota Liquid Glass.
- `tools_check_splash.py`: valida los formatos BMP y PNG de arranque.
- `tools_patch_mfsbsd.py`: integración controlada del splash.
- `tests/` y `docs/`: comprobaciones y plan de pruebas.
- `licenses/`: atribuciones y avisos.

## Licencias

FluidOS conserva los avisos de FreeBSD, mfsBSD y los paquetes que integra. No se elimina la procedencia ni las licencias de terceros. Consulta `licenses/THIRD-PARTY.md`.

## Ampliación de las nueve rondas

La integración añade el panel **Ajustes**, preferencias personales guardadas en `~/.config/fluidos/settings.json`, primera versión del formato de paquetes nativos `.fapp`, comprobación de integridad, utilidades manuales de copia de seguridad y LibreOffice con idioma español en la instalación prevista.

Para abrir Ajustes desde el escritorio, utiliza **Ajustes** en la barra superior, el dock o el lanzador. Para crear una copia de seguridad de la carpeta personal en una unidad externa ya montada:

```sh
fluidos-backup backup /ruta/de/la/unidad
fluidos-backup verify /ruta/de/la/unidad/FluidOS-backup-FECHA.tar.gz
```

Para comprobar un paquete nativo sin instalarlo:

```sh
doas /usr/local/sbin/fluidos-app verify ejemplo.fapp
```

El documento `docs/FORMATO-FAPP.md` describe el formato y sus límites. `docs/PLAN-NUEVE-RONDAS.md` separa lo existente de lo que sigue pendiente.

**Fases 4 y 5 (integración incremental):** se incorpora un asistente local de órdenes permitidas, búsqueda de nombres de archivos y confirmación antes de abrir archivos/aplicaciones o solicitar apagado/reinicio. También se aplican temas, acento, fondos, tamaño del Dock, adaptación por ancho de pantalla y distribución de escritorios Wayfire. El asistente no es aún un modelo generativo y no incluye voz, sincronización ni transferencia entre dispositivos. Las preferencias del shell requieren reiniciar la sesión.

**Importante:** el gestor `.fapp` no tiene todavía tienda firmada ni aislamiento de procesos; las solicitudes de permisos de paquetes no constituyen una barrera de seguridad. La copia de seguridad es manual. La IA generativa, voz, sincronización, navegador propio, recuperación avanzada, cifrado integral, widgets, gestos y soporte ARM64 siguen pendientes.
