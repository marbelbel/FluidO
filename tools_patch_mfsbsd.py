#!/usr/bin/env python3
"""Apply small, checked changes to the pinned mfsBSD Makefile."""

from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: tools_patch_mfsbsd.py path/to/mfsbsd/Makefile")

path = Path(sys.argv[1])
text = path.read_text()
if ('CUSTOMFILESDIR}/boot/fluidos-splash.bmp' in text
        and 'CUSTOMFILESDIR}/boot/fluidos-splash.png' in text
        and 'splash_bmp.ko' in text):
    print("Pinned mfsBSD Makefile already contains the FluidOS splash integration.")
    raise SystemExit(0)

# mfsBSD compresses and clears its staging root before the final mfsroot step.
# Therefore copy the splash from CUSTOMFILESDIR directly into the ISO boot tree.
loader_pattern = re.compile(
    r"(\t\t\$\{INSTALL\} -m 0644 \$\{CFGDIR\}/loader\.conf\.sample "
    r"\$\{WRKDIR\}/disk/boot/loader\.conf; \\\n\tfi\n)"
)
loader_match = loader_pattern.search(text)
if not loader_match:
    raise SystemExit("Pinned mfsBSD Makefile did not contain the expected loader.conf install block; no changes made.")
loader_addition = "\n".join([
    '\t${_v}if [ -f "${CUSTOMFILESDIR}/boot/fluidos-splash.bmp" ]; then \\',
    '\t\t${INSTALL} -m 0644 ${CUSTOMFILESDIR}/boot/fluidos-splash.bmp ${WRKDIR}/disk/boot/fluidos-splash.bmp; \\',
    '\tfi',
    '\t${_v}if [ -f "${CUSTOMFILESDIR}/boot/fluidos-splash.png" ]; then \\',
    '\t\t${INSTALL} -m 0644 ${CUSTOMFILESDIR}/boot/fluidos-splash.png ${WRKDIR}/disk/boot/fluidos-splash.png; \\',
    '\tfi',
]) + "\n"
text = text[:loader_match.end()] + loader_addition + text[loader_match.end():]

# Copy the legacy BMP decoder into the ISO boot kernel directory when the
# selected FreeBSD kernel provides it. UEFI vt(4) uses the PNG image directly.
module_pattern = re.compile(
    r"(\t\$\{_v\}\$\{FIND\} \$\{_BOOTDIR\}/\$\{KERNDIR\} "
    r"-name 'acpi\*\.ko' -exec \$\{INSTALL\} -m 0555 \{\} "
    r"\$\{WRKDIR\}/disk/boot/kernel [^\n]*\n)"
)
module_match = module_pattern.search(text)
if not module_match:
    raise SystemExit("Pinned mfsBSD Makefile did not contain the expected acpi module-copy line; no changes made.")
module_addition = (
    '\t${_v}if [ -f "${_BOOTDIR}/${KERNDIR}/splash_bmp.ko" ]; then '
    '${INSTALL} -m 0555 ${_BOOTDIR}/${KERNDIR}/splash_bmp.ko '
    '${WRKDIR}/disk/boot/kernel; fi\n'
)
text = text[:module_match.end()] + module_addition + text[module_match.end():]

path.write_text(text)
print("Patched the pinned mfsBSD Makefile: vt PNG splash, syscons BMP fallback, and BMP decoder module.")
