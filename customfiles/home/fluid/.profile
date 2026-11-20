# FluidOS: iniciar la sesion grafica al entrar en la consola principal.
PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
export PATH

if [ -t 0 ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    TTY_NAME="$(tty 2>/dev/null || true)"
    if [ "$TTY_NAME" = "/dev/ttyv0" ]; then
        /usr/local/bin/fluidos-session
    fi
fi
