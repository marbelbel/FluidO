#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

for file in \
    README.md \
    build-fluidos.sh \
    desktop/fluidos-shell.py \
    tools_check_splash.py \
    artwork/fluidos-splash-master.png \
    tools_patch_mfsbsd.py \
    mfsbsd/conf/loader.conf \
    mfsbsd/conf/rc.conf \
    mfsbsd/conf/ttys \
    mfsbsd/tools/packages \
    mfsbsd/tools/motd \
    mfsbsd/tools/motd.se \
    customscripts/10-fluid-user.sh \
    customfiles/etc/os-release \
    customfiles/boot/fluidos-splash.bmp \
    customfiles/boot/fluidos-splash.png \
    customfiles/etc/fluidos-version \
    customfiles/usr/local/bin/fluidos-session \
    customfiles/usr/local/bin/fluidos-shell \
    customfiles/usr/local/sbin/fluidos-install \
    customfiles/usr/local/share/licenses/FluidOS/MFSBSD-BSD-2-Clause.txt \
    customfiles/usr/local/share/doc/FluidOS/LEEME.txt \
    customfiles/home/fluid/.profile \
    customfiles/home/fluid/.config/wayfire/wayfire.ini; do
    [ -s "$file" ] || { echo "Missing or empty: $file" >&2; exit 1; }
done

grep -q 'mfs_type="mfs_root"' mfsbsd/conf/loader.conf
grep -q 'splash="/boot/fluidos-splash.png"' mfsbsd/conf/loader.conf
grep -q 'fluidos-splash.png' tools_patch_mfsbsd.py
grep -q 'fluidos-splash.png' customfiles/usr/local/sbin/fluidos-install
grep -q 'vfs.root.mountfrom="ufs:/dev/ufs/mfsroot"' mfsbsd/conf/loader.conf
grep -q 'PERMIT_ROOT_LOGIN=no' build-fluidos.sh
grep -q "ROOTPW_HASH='\*'" build-fluidos.sh
grep -q 'BASE="$DIST_DIR"' build-fluidos.sh
grep -q 'fluidos-splash.png' build-fluidos.sh
grep -q 'MFSBSD_COMMIT="6e48fa48ebbb25953a7764a8f3cfda443fb9a768"' build-fluidos.sh
grep -q 'INSTALL FluidOS ON DISK' customfiles/usr/local/sbin/fluidos-install
grep -q 'BOOT_CHOICE' customfiles/usr/local/sbin/fluidos-install
grep -q 'Instalar FluidOS' desktop/fluidos-shell.py
grep -q 'FluidOS' customfiles/etc/os-release
if grep -q 'vmwgfx' mfsbsd/conf/rc.conf customfiles/usr/local/sbin/fluidos-install; then
    echo "vmwgfx is not a drm-kmod module and must not be in kld_list." >&2
    exit 1
fi
if grep -q 'Terminal' desktop/fluidos-shell.py; then
    echo "The terminal must not appear in the normal dock or launcher." >&2
    exit 1
fi
if grep -R -n -E 'fluidos"[[:space:]]*\|[[:space:]]*chroot|password.*fluidos' customscripts customfiles; then
    echo "A hardcoded user password was detected." >&2
    exit 1
fi

for file in \
    desktop/fluidos-control.py \
    tools/fluidos-app.py \
    customfiles/usr/local/bin/fluidos-control \
    customfiles/usr/local/bin/fluidos-backup \
    docs/FORMATO-FAPP.md \
    docs/PLAN-NUEVE-RONDAS.md \
    tests/test_fluidos_app.py     tests/test_apply_patch.py     apply-nine-rounds.py; do
    [ -s "$file" ] || { echo "Missing or empty: $file" >&2; exit 1; }
done
grep -q 'fluidos-control.py' build-fluidos.sh
grep -q 'libreoffice es-libreoffice' customfiles/usr/local/sbin/fluidos-install
grep -q 'fluidos-app.py' .github/workflows/build-fluidos.yml
grep -q 'Ajustes' desktop/fluidos-shell.py
echo "FluidOS source checks passed."
