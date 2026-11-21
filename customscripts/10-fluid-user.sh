#!/bin/sh
# This is executed by mfsBSD while assembling its root filesystem.
set -eu

: "${DESTDIR:?mfsBSD did not set DESTDIR}"

GETTYTAB="$DESTDIR/etc/gettytab"
TTYS="$DESTDIR/etc/ttys"

# gettytab's al capability logs into the FluidOS account on the disposable LIVE image.
if ! grep -q '^fluidautologin:' "$GETTYTAB"; then
    printf '\n# FluidOS disposable live console\nfluidautologin:al=fluid:tc=Pc:\n' >> "$GETTYTAB"
fi

# Create a non-root account. This is only auto-login on the Live image;
# the installed system will ask the owner to set a password.
if ! pw -R "$DESTDIR" groupshow video >/dev/null 2>&1; then
    pw -R "$DESTDIR" groupadd video
fi
if ! pw -R "$DESTDIR" usershow fluid >/dev/null 2>&1; then
    pw -R "$DESTDIR" useradd fluid -d /home/fluid -g wheel -G video -s /bin/sh -c 'FluidOS Live User'
else
    pw -R "$DESTDIR" usermod fluid -G wheel,video
fi

mkdir -p "$DESTDIR/home/fluid/.config/wayfire"
FLUID_UID="$(pw -R "$DESTDIR" usershow fluid | awk -F: '{print $3}')"
WHEEL_GID="$(pw -R "$DESTDIR" groupshow wheel | awk -F: '{print $3}')"
[ -n "$FLUID_UID" ] && [ -n "$WHEEL_GID" ] || {
    echo "[ERROR] No se pudieron obtener UID/GID del usuario fluid." >&2
    exit 1
}
chown -R "${FLUID_UID}:${WHEEL_GID}" "$DESTDIR/home/fluid"
chmod 0755 "$DESTDIR/home/fluid"

# Only the installer can be run as root without a password in this temporary Live session.
mkdir -p "$DESTDIR/usr/local/etc"
cat > "$DESTDIR/usr/local/etc/doas.conf" <<'DOAS_EOF'
permit nopass fluid as root cmd /usr/local/sbin/fluidos-install
permit nopass fluid as root cmd /sbin/shutdown
permit nopass fluid as root cmd /usr/local/sbin/fluidos-app
DOAS_EOF
chmod 0400 "$DESTDIR/usr/local/etc/doas.conf"

# Marker lets the desktop label the running environment accurately.
printf '%s\n' 'live' > "$DESTDIR/etc/fluidos-live"
chmod 0644 "$DESTDIR/etc/fluidos-live"

# Prevent accidental remote access to a disposable test environment.
if [ -f "$DESTDIR/etc/rc.conf" ]; then
    if ! grep -q '^sshd_enable=' "$DESTDIR/etc/rc.conf"; then
        echo 'sshd_enable="NO"' >> "$DESTDIR/etc/rc.conf"
    fi
fi

# Make sure the desktop shell and installer are executable in the generated root.
chmod 0755 "$DESTDIR/usr/local/bin/fluidos-session" \
           "$DESTDIR/usr/local/bin/fluidos-shell" \
           "$DESTDIR/usr/local/sbin/fluidos-install"
chmod 0755 "$DESTDIR/usr/local/bin/fluidos-app-center" "$DESTDIR/usr/local/bin/fluidos-restore" "$DESTDIR/usr/local/bin/fluidos-users"
chmod 0755 "$DESTDIR/usr/local/lib/fluidos/fluidos-shell.py"
