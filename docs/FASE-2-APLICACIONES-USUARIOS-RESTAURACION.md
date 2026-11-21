# Fase 2 de FluidOS: centro de aplicaciones, cuentas y restauración

Esta ampliación añade tres funciones utilizables a la alpha:

## Centro de aplicaciones local

- `fluidos-app-center` abre una interfaz GTK para ver, instalar y desinstalar paquetes `.fapp` locales.
- El buscador del lanzador permite buscar nombres de aplicaciones y nombres de archivos dentro del perfil personal (no busca dentro del contenido de los documentos).
- Antes de instalar ejecuta `fluidos-app verify` y muestra una advertencia sobre la procedencia del paquete.
- No es todavía una tienda en línea: no descarga catálogos y no autentica criptográficamente al editor.
- El formato actual no aplica sandbox ni permisos por aplicación. No instales paquetes de procedencia desconocida.

## Copias y restauración

- `fluidos-restore ARCHIVO.tar.gz` verifica el SHA-256 asociado.
- Solo acepta directorios/archivos regulares bajo `home/fluid` y rechaza enlaces, dispositivos y rutas que salgan del perfil.
- Necesita `doas`; conserva la carpeta personal anterior con el nombre `.fluid-before-restore-*` antes de sustituirla.
- No restaura `/etc/os-release` ni otros archivos del sistema.

Ejemplo:

```sh
 doas fluidos-restore /media/USB/FluidOS-backup-AAAAMMDD-HHMMSS.tar.gz --confirm 'RESTAURAR PERFIL FLUID'
```

## Gestión de usuarios

```sh
 doas fluidos-users add ana
 fluidos-users list
 doas fluidos-users remove ana --confirm 'ELIMINAR USUARIO ana'
```

Los usuarios nuevos no reciben permisos de administrador. Las cuentas `root`, `toor` y `fluid` están protegidas.

## Limitaciones pendientes

Esta fase no completa el cifrado integral, el aislamiento de aplicaciones, las firmas del catálogo, las actualizaciones automáticas ni la IA. Tampoco sustituye las pruebas de instalación y arranque de la ISO. Es una ampliación de la alpha, no una versión estable.
