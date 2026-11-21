#!/usr/bin/env python3
"""Safely integrate the FluidOS nine-round foundation into an existing clone.

Run from the repository root after extracting this overlay ZIP over the clone:
    python3 apply-nine-rounds.py
The script checks all expected anchors before writing and creates .bak files.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def replace_once(text: str, old: str, new: str, marker: str, label: str) -> str:
    if marker in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"No se pudo localizar de forma única el punto de integración: {label} (encontrados: {count})")
    return text.replace(old, new, 1)


def transform(path: str, operations):
    file = ROOT / path
    if not file.is_file():
        raise RuntimeError(f"Falta el archivo base: {path}")
    original = file.read_text(encoding="utf-8")
    updated = original
    for old, new, marker, label in operations:
        updated = replace_once(updated, old, new, marker, label)
    return file, original, updated


def write_atomic(file: Path, content: str):
    backup = file.with_name(file.name + ".bak-nine-rounds")
    if not backup.exists():
        shutil.copy2(file, backup)
    fd, temp_name = tempfile.mkstemp(prefix=".fluidos-patch-", dir=str(file.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_name, file.stat().st_mode & 0o777)
        os.replace(temp_name, file)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main():
    parser = argparse.ArgumentParser(description="Integra la base de las nueve rondas de FluidOS")
    parser.add_argument("--dry-run", action="store_true", help="Comprueba los archivos sin modificarlos")
    args = parser.parse_args()

    changes = []
    changes.append(transform("build-fluidos.sh", [(
        '''install -m 0755 "$PROJECT_DIR/desktop/fluidos-shell.py" \\\n    "$MFSBSD_DIR/customfiles/usr/local/lib/fluidos/fluidos-shell.py"\n''',
        '''install -m 0755 "$PROJECT_DIR/desktop/fluidos-shell.py" \\\n    "$MFSBSD_DIR/customfiles/usr/local/lib/fluidos/fluidos-shell.py"\ninstall -m 0755 "$PROJECT_DIR/desktop/fluidos-control.py" \\\n    "$MFSBSD_DIR/customfiles/usr/local/lib/fluidos/fluidos-control.py"\ninstall -m 0755 "$PROJECT_DIR/tools/fluidos-app.py" \\\n    "$MFSBSD_DIR/customfiles/usr/local/sbin/fluidos-app"\n''',
        'customfiles/usr/local/lib/fluidos/fluidos-control.py', 'instalación de ajustes y gestor .fapp'
    )]))

    desktop_ops = [
        ('import os\nimport shutil\n', 'import json\nimport os\nimport re\nimport shutil\n', 'import json\nimport os\nimport re', 'imports del escritorio'),
        ('        self.windows = []\n        self._install_css()\n', '        self.windows = []\n        self.settings = self._load_preferences()\n        self._install_css()\n', 'self.settings = self._load_preferences()', 'carga de preferencias'),
        ('    def _install_css(self):\n        provider = Gtk.CssProvider()\n        provider.load_from_data(CSS)\n', '''    def _load_preferences(self):
        path = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")), "fluidos", "settings.json")
        try:
            with open(path, "r", encoding="utf-8") as stream:
                data = json.load(stream)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _install_css(self):
        provider = Gtk.CssProvider()
        accent = self.settings.get("appearance", {}).get("accent", "#69d9ff")
        if not isinstance(accent, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
            accent = "#69d9ff"
        red, green, blue = (int(accent[i:i + 2], 16) for i in (1, 3, 5))
        overrides = (f".top-button:hover {{ background: rgba({red}, {green}, {blue}, .20); }} "
                     f".dock button:hover {{ background: rgba({red}, {green}, {blue}, .28); }}").encode()
        provider.load_from_data(CSS + overrides)
''', 'def _load_preferences(self):', 'lectura y aplicación del color de acento'),
        ('        bar.pack_start(self.top_button("Sistema", self.show_system), False, False, 0)\n', '        bar.pack_start(self.top_button("Sistema", self.show_system), False, False, 0)\n        bar.pack_start(self.top_button("Ajustes", lambda: launch(["fluidos-control"])), False, False, 0)\n', 'top_button("Ajustes"', 'botón de ajustes en la barra superior'),
        ('            ("⚙", "Sistema", self.show_system),\n', '            ("⚙", "Sistema", self.show_system),\n            ("✧", "Ajustes", lambda: launch(["fluidos-control"])),\n', '("✧", "Ajustes"', 'acceso a ajustes en el dock'),
        ('            ("⚙\\nInformación del sistema", self.show_system),\n            ("⏻\\nApagar o reiniciar", self.show_power),\n        ]\n', '            ("⚙\\nInformación del sistema", self.show_system),\n            ("✧\\nAjustes", lambda: launch(["fluidos-control"])),\n            ("▦\\nOfimática", lambda: launch(["libreoffice"])),\n            ("⏻\\nApagar o reiniciar", self.show_power),\n        ]\n', '("▦\\nOfimática"', 'aplicaciones en el lanzador'),
    ]
    changes.append(transform("desktop/fluidos-shell.py", desktop_ops))

    installer_ops = [
        ('py312-pycairo py312-pygobject python312 seatd wayfire wayland xwayland; then', 'py312-pycairo py312-pygobject python312 seatd wayfire wayland xwayland libreoffice es-libreoffice; then', 'xwayland libreoffice es-libreoffice', 'instalación de ofimática'),
        ('cp /usr/local/lib/fluidos/fluidos-shell.py /mnt/usr/local/lib/fluidos/fluidos-shell.py\n', 'cp /usr/local/lib/fluidos/fluidos-shell.py /mnt/usr/local/lib/fluidos/fluidos-shell.py\ncp /usr/local/lib/fluidos/fluidos-control.py /mnt/usr/local/lib/fluidos/fluidos-control.py\ncp /usr/local/bin/fluidos-control /mnt/usr/local/bin/fluidos-control\ncp /usr/local/bin/fluidos-backup /mnt/usr/local/bin/fluidos-backup\ncp /usr/local/sbin/fluidos-app /mnt/usr/local/sbin/fluidos-app\n', 'cp /usr/local/lib/fluidos/fluidos-control.py', 'copia de utilidades al sistema instalado'),
    ]
    changes.append(transform("customfiles/usr/local/sbin/fluidos-install", installer_ops))

    package_list = ROOT / "mfsbsd/tools/packages"
    if not package_list.is_file():
        raise RuntimeError("Falta mfsbsd/tools/packages")
    packages_old = package_list.read_text(encoding="utf-8")
    packages_new = packages_old
    if "\nlibreoffice\n" not in packages_new:
        if not packages_new.endswith("\n"):
            packages_new += "\n"
        packages_new += "libreoffice\nes-libreoffice\n"
    changes.append((package_list, packages_old, packages_new))

    workflow_ops = [(
        '          python3 -m py_compile desktop/fluidos-shell.py tools_check_splash.py tools_patch_mfsbsd.py\n          bash tests/check-source.sh',
        '          python3 -m py_compile desktop/fluidos-shell.py desktop/fluidos-control.py tools/fluidos-app.py tools_check_splash.py tools_patch_mfsbsd.py tests/test_fluidos_app.py tests/test_apply_patch.py\n          python3 -m unittest discover -s tests -v\n          sh -n customfiles/usr/local/bin/fluidos-backup\n          bash tests/check-source.sh',
        'desktop/fluidos-control.py tools/fluidos-app.py', 'pruebas de módulos nuevos en CI'
    )]
    changes.append(transform(".github/workflows/build-fluidos.yml", workflow_ops))

    test_ops = [(
        'echo "FluidOS source checks passed."',
        '''for file in \\
    desktop/fluidos-control.py \\
    tools/fluidos-app.py \\
    customfiles/usr/local/bin/fluidos-control \\
    customfiles/usr/local/bin/fluidos-backup \\
    docs/FORMATO-FAPP.md \\
    docs/PLAN-NUEVE-RONDAS.md \\
    tests/test_fluidos_app.py \
    tests/test_apply_patch.py \
    apply-nine-rounds.py; do
    [ -s "$file" ] || { echo "Missing or empty: $file" >&2; exit 1; }
done
grep -q 'fluidos-control.py' build-fluidos.sh
grep -q 'libreoffice es-libreoffice' customfiles/usr/local/sbin/fluidos-install
grep -q 'fluidos-app.py' .github/workflows/build-fluidos.yml
grep -q 'Ajustes' desktop/fluidos-shell.py
echo "FluidOS source checks passed."''',
        'docs/PLAN-NUEVE-RONDAS.md', 'comprobaciones de los módulos añadidos'
    )]
    changes.append(transform("tests/check-source.sh", test_ops))

    status_ops = [(
        '- Sintaxis de los tres archivos Python (`py_compile`).',
        '- Sintaxis de los módulos Python del escritorio, utilidades .fapp y pruebas unitarias (`py_compile`).',
        'utilidades .fapp y pruebas unitarias', 'recuento de comprobaciones Python'
    ), (
        '- Prueba del parcheador de mfsBSD con los bloques de Makefile previstos y comprobación de que no aplica el parche dos veces.',
        '- Prueba del parcheador de mfsBSD con los bloques de Makefile previstos y comprobación de que no aplica el parche dos veces.\n- Cinco pruebas unitarias para validar paquetes .fapp y la aplicación repetida del integrador de las nueve rondas.',
        'Cinco pruebas unitarias', 'registro de pruebas unitarias'
    ), (
        '- Construcción real con FreeBSD 14.5 amd64.',
        '- Recompilación de la ISO después de integrar la ampliación de las nueve rondas. La revisión anterior sí generó una ISO en GitHub Actions con FreeBSD 14.5 amd64 el 20-11-2026.',
        'La revisión anterior sí generó una ISO', 'estado de la compilación previa'
    )]
    changes.append(transform("docs/ESTADO-ALPHA.md", status_ops))

    readme = ROOT / "README.md"
    readme_old = readme.read_text(encoding="utf-8")
    marker = "## Ampliación de las nueve rondas"
    appendix = '''

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

**Importante:** el registro de preferencias no significa que cada ajuste ya esté conectado. El gestor `.fapp` no tiene todavía tienda, firma digital ni aislamiento de procesos; las solicitudes de permisos se registran, pero aún no se aplican como barrera de seguridad. La copia de seguridad es manual y todavía no existe un asistente gráfico de restauración. La IA, sincronización, navegador propio, recuperación avanzada, cifrado integral y soporte ARM64 siguen pendientes.
'''
    readme_new = readme_old if marker in readme_old else readme_old.rstrip() + appendix
    changes.append((readme, readme_old, readme_new))

    if args.dry_run:
        for file, original, updated in changes:
            print(f"OK: {file.relative_to(ROOT)} ({'sin cambios' if original == updated else 'cambio preparado'})")
        print("Comprobación terminada. No se ha modificado ningún archivo.")
        return 0

    for file, original, updated in changes:
        if original != updated:
            write_atomic(file, updated)
            print(f"Actualizado: {file.relative_to(ROOT)} (copia .bak-nine-rounds creada)")
        else:
            print(f"Sin cambios: {file.relative_to(ROOT)}")
    print("Integración aplicada. Ejecuta las pruebas indicadas en README.md y no uses discos con datos importantes.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"No se aplicó la integración: {exc}", file=sys.stderr)
        raise SystemExit(1)
