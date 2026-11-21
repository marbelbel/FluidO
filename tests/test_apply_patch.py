import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PATCH = Path(__file__).resolve().parents[1] / "apply-nine-rounds.py"


class PatchIntegrationTests(unittest.TestCase):
    def build_fixture(self, root):
        files = {
            "build-fluidos.sh": 'install -m 0755 "$PROJECT_DIR/desktop/fluidos-shell.py" \\\n    "$MFSBSD_DIR/customfiles/usr/local/lib/fluidos/fluidos-shell.py"\n',
            "desktop/fluidos-shell.py": '''import os
import shutil

class FluidShell:
    def __init__(self):
        self.windows = []
        self._install_css()

    def _install_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)

    def _create_topbar(self):
        bar.pack_start(self.top_button("Sistema", self.show_system), False, False, 0)

    def _create_dock(self):
        items = [
            ("⚙", "Sistema", self.show_system),
        ]

    def show_launcher(self):
        apps = [
            ("⚙\\nInformación del sistema", self.show_system),
            ("⏻\\nApagar o reiniciar", self.show_power),
        ]
''',
            "customfiles/usr/local/sbin/fluidos-install": '''if ! pkg -r /mnt install -y dbus dejavu doas firefox foot drm-kmod gtk3 gtk-layer-shell py312-pycairo py312-pygobject python312 seatd wayfire wayland xwayland; then
cp /usr/local/lib/fluidos/fluidos-shell.py /mnt/usr/local/lib/fluidos/fluidos-shell.py
''',
            "mfsbsd/tools/packages": "firefox\nwayfire\n",
            ".github/workflows/build-fluidos.yml": "          python3 -m py_compile desktop/fluidos-shell.py tools_check_splash.py tools_patch_mfsbsd.py\n          bash tests/check-source.sh",
            "tests/check-source.sh": 'echo "FluidOS source checks passed."',
            "README.md": "# FluidOS\n\n## Licencias\n",
            "docs/ESTADO-ALPHA.md": "- Sintaxis de los tres archivos Python (`py_compile`).\n- Prueba del parcheador de mfsBSD con los bloques de Makefile previstos y comprobación de que no aplica el parche dos veces.\n- Construcción real con FreeBSD 14.5 amd64.\n",
        }
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        for new in [
            "desktop/fluidos-control.py", "tools/fluidos-app.py",
            "customfiles/usr/local/bin/fluidos-control", "customfiles/usr/local/bin/fluidos-backup",
            "docs/FORMATO-FAPP.md", "docs/PLAN-NUEVE-RONDAS.md", "tests/test_fluidos_app.py",
            "tests/test_apply_patch.py"
        ]:
            path = root / new
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture", encoding="utf-8")
        (root / "apply-nine-rounds.py").write_text(PATCH.read_text(encoding="utf-8"), encoding="utf-8")

    def test_patch_dry_run_and_apply_are_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_fixture(root)
            dry = subprocess.run([sys.executable, "apply-nine-rounds.py", "--dry-run"], cwd=root, text=True, capture_output=True)
            self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
            applied = subprocess.run([sys.executable, "apply-nine-rounds.py"], cwd=root, text=True, capture_output=True)
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            second = subprocess.run([sys.executable, "apply-nine-rounds.py"], cwd=root, text=True, capture_output=True)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            desktop = (root / "desktop/fluidos-shell.py").read_text(encoding="utf-8")
            self.assertIn("fluidos-control", desktop)
            self.assertIn("libreoffice", desktop)


if __name__ == "__main__":
    unittest.main()
