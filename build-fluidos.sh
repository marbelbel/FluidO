#!/bin/sh
# Build a dual-purpose FluidOS Live + Installer ISO with pinned mfsBSD.
set -eu

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
FLUIDOS_VERSION="${FLUIDOS_VERSION:-0.1.0-alpha}"
RELEASE="14.5-RELEASE"
ARCH="amd64"
BASE_URL="https://download.freebsd.org/releases/${ARCH}/${ARCH}/${RELEASE}"
BUILD_ROOT="/usr/obj/fluidos-build"
DIST_DIR="${BUILD_ROOT}/dist-source"
MFSBSD_DIR="${BUILD_ROOT}/mfsbsd"
MFSBSD_COMMIT="6e48fa48ebbb25953a7764a8f3cfda443fb9a768"
OUTPUT_DIR="${PROJECT_DIR}/out"
EXPECTED_ISO="mfsbsd-se-${RELEASE}-${ARCH}.iso"

log() { printf '\n[FluidOS] %s\n' "$*"; }
die() { printf '\n[ERROR] %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Ejecuta este script como root dentro de FreeBSD 14.5 amd64."
[ "$(uname -m)" = "$ARCH" ] || die "Se requiere amd64; arquitectura detectada: $(uname -m)."
command -v fetch >/dev/null 2>&1 || die "Falta fetch. Ejecuta este script dentro de FreeBSD."
command -v make >/dev/null 2>&1 || die "No se encuentra make."
command -v sha256 >/dev/null 2>&1 || die "No se encuentra sha256."

log "Instalando herramientas del constructor..."
if ! command -v git >/dev/null 2>&1 || ! command -v python3.12 >/dev/null 2>&1; then
    pkg bootstrap -f -y
    pkg install -y git-lite python312
fi
command -v git >/dev/null 2>&1 || die "No se pudo instalar git-lite."
command -v python3.12 >/dev/null 2>&1 || die "No se pudo instalar python312."

log "Preparando un directorio limpio..."
rm -rf "$BUILD_ROOT"
mkdir -p "$DIST_DIR" "$OUTPUT_DIR"

log "Descargando FreeBSD ${RELEASE}..."
for archive in base.txz kernel.txz; do
    fetch -o "${DIST_DIR}/${archive}" "${BASE_URL}/${archive}" || die "No se pudo descargar ${archive}."
    [ -s "${DIST_DIR}/${archive}" ] || die "${archive} esta vacio."
done

log "Descargando mfsBSD y fijando la revision ${MFSBSD_COMMIT}..."
git clone --quiet https://github.com/mmatuska/mfsbsd.git "$MFSBSD_DIR"
git -C "$MFSBSD_DIR" fetch --quiet --depth 1 origin "$MFSBSD_COMMIT"
git -C "$MFSBSD_DIR" checkout --quiet --detach "$MFSBSD_COMMIT"

log "Integrando escritorio, arranque, instalador y avisos legales..."
cp -Rp "$PROJECT_DIR/mfsbsd/conf/." "$MFSBSD_DIR/conf/"
cp -Rp "$PROJECT_DIR/mfsbsd/tools/." "$MFSBSD_DIR/tools/"
cp -Rp "$PROJECT_DIR/customfiles/." "$MFSBSD_DIR/customfiles/"
cp -Rp "$PROJECT_DIR/customscripts/." "$MFSBSD_DIR/customscripts/"
mkdir -p "$MFSBSD_DIR/customfiles/usr/local/lib/fluidos"
install -m 0755 "$PROJECT_DIR/desktop/fluidos-shell.py" \
    "$MFSBSD_DIR/customfiles/usr/local/lib/fluidos/fluidos-shell.py"
install -m 0755 "$PROJECT_DIR/customfiles/usr/local/bin/fluidos-session" \
    "$MFSBSD_DIR/customfiles/usr/local/bin/fluidos-session"
install -m 0755 "$PROJECT_DIR/customfiles/usr/local/bin/fluidos-shell" \
    "$MFSBSD_DIR/customfiles/usr/local/bin/fluidos-shell"
install -m 0755 "$PROJECT_DIR/customfiles/usr/local/sbin/fluidos-install" \
    "$MFSBSD_DIR/customfiles/usr/local/sbin/fluidos-install"
install -m 0644 "$PROJECT_DIR/customfiles/home/fluid/.profile" \
    "$MFSBSD_DIR/customfiles/home/fluid/.profile"
install -m 0644 "$PROJECT_DIR/customfiles/home/fluid/.config/wayfire/wayfire.ini" \
    "$MFSBSD_DIR/customfiles/home/fluid/.config/wayfire/wayfire.ini"

log "Aplicando integracion del splash sobre el Makefile upstream..."
python3.12 "$PROJECT_DIR/tools_patch_mfsbsd.py" "$MFSBSD_DIR/Makefile"

log "Verificando las imagenes Liquid Glass incluidas..."
python3.12 "$PROJECT_DIR/tools_check_splash.py"
install -m 0644 "$PROJECT_DIR/customfiles/boot/fluidos-splash.bmp" \
    "$MFSBSD_DIR/customfiles/boot/fluidos-splash.bmp"
install -m 0644 "$PROJECT_DIR/customfiles/boot/fluidos-splash.png" \
    "$MFSBSD_DIR/customfiles/boot/fluidos-splash.png"

[ -x /usr/local/sbin/pkg-static ] || die "No se encuentra pkg-static en el constructor."

log "Compilando la ISO hibrida Live + Installer para BIOS y UEFI..."
cd "$MFSBSD_DIR"
make clean-all
# IMPORTANT: BASE must point to the downloaded source directory. mfsBSD copies
# it into WRKDIR/dist/<release>-<target>; using that destination as BASE makes
# cp attempt to copy each file onto itself and breaks the build.
make iso \
    SE=1 \
    BASE="$DIST_DIR" \
    RELEASE="$RELEASE" \
    TARGET="$ARCH" \
    TARGET_ARCH="$ARCH" \
    PKG_ABI="FreeBSD:14:amd64" \
    MFSROOT_MAXSIZE=3000m \
    MFSROOT_FREE_BLOCKS=3% \
    MFSROOT_FREE_INODES=3% \
    ROOTPW_HASH='*' \
    PERMIT_ROOT_LOGIN=no \
    MFSMODULES="aesni crypto cryptodev ext2fs geom_eli geom_mirror geom_nop ipmi ntfs nullfs opensolaris smbus snp tmpfs zfs splash_bmp"

ISO_PATH="${MFSBSD_DIR}/${EXPECTED_ISO}"
[ -s "$ISO_PATH" ] || die "mfsBSD no genero la ISO esperada: ${EXPECTED_ISO}."

FINAL_ISO="${OUTPUT_DIR}/FluidOS-${FLUIDOS_VERSION}-${RELEASE}-${ARCH}-Live-Installer.iso"
cp "$ISO_PATH" "$FINAL_ISO"
sha256 "$FINAL_ISO" > "${FINAL_ISO}.sha256"
[ -s "$FINAL_ISO" ] || die "La ISO final esta vacia."

printf '\n[OK] ISO creada: %s\n' "$FINAL_ISO"
ls -lh "$FINAL_ISO" "${FINAL_ISO}.sha256"
printf '\nEsta misma ISO permite probar FluidOS en modo Live o iniciar el instalador.\n'
printf 'La compilacion no sustituye las pruebas reales de arranque e instalacion.\n'
