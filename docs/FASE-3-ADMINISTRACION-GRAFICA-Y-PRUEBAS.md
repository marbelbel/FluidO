# FluidOS Fase 3: administración gráfica y pruebas portables

Esta ampliación se aplica sobre el repositorio `marbelbel/FluidO` después de la Fase 2.

## Qué incorpora

- Panel GTK para listar, crear y eliminar cuentas personales de FluidOS.
- Acceso al panel desde la barra superior y el lanzador de aplicaciones.
- Copia del panel y su lanzador tanto en la ISO Live como en la instalación al disco.
- Protección adicional: solo se muestran/eliminan cuentas con UID de usuario y carpeta personal bajo `/home` o `/usr/home`; se protegen las cuentas del sistema y `fluid`.
- Pruebas de `tools/fluidos-users.py` que pueden importarse en Windows sin disponer del módulo Unix `pwd`.
- Pruebas del integrador que usan `sys.executable`, por lo que funcionan con `py -3` en Windows y con el intérprete actual en CI.
- GitHub Actions se activa también cuando cambian ficheros de `tools/`.

## Límites

- El panel administra cuentas locales FreeBSD; no es un gestor de identidad en red.
- Para crear usuarios se abre Foot y `doas`, donde se introduce la contraseña de la nueva cuenta.
- Solo el administrador del sistema puede crear o eliminar cuentas.
- Esta fase no implementa IA, tienda remota, firmas de paquetes, sandbox, cifrado integral, actualizaciones transaccionales, sincronización, ARM64 ni compatibilidad universal de GPU.

## Aplicación

Desde PowerShell, en la carpeta que contiene este paquete:

```powershell
py -3 .\integrate-phase3.py --repo "$HOME\Desktop\FluidO" --dry-run
py -3 .\integrate-phase3.py --repo "$HOME\Desktop\FluidO"
```

Después, desde la raíz del repositorio:

```powershell
py -3 -m py_compile desktop\fluidos-users-panel.py tools\fluidos-users.py
py -3 -m unittest discover -s tests -v
```

Publica solo cuando todas las pruebas terminen correctamente:

```powershell
git add -A
git status
git commit -m "Añadir panel gráfico de usuarios y pruebas portables"
git push origin main
```
