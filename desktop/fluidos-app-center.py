#!/usr/local/bin/python3.12
"""Centro de aplicaciones para instalar y quitar paquetes .fapp locales."""
from __future__ import annotations
import subprocess
import shutil
from pathlib import Path
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

TOOL = "/usr/local/sbin/fluidos-app"

def run_tool(args):
    return subprocess.run([TOOL, *args], text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, check=False, timeout=180)

def parse_installed(text):
    rows = []
    for line in text.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) == 3 and parts[0] != "No":
            rows.append(tuple(parts))
    return rows

def run_privileged(title, args):
    terminal = shutil.which("foot")
    if not terminal:
        raise RuntimeError("No se encuentra foot, necesario para pedir autorización de administrador.")
    return subprocess.run([terminal, "-T", title, "-e", "doas", TOOL, *args],
                          check=False, timeout=300)

class AppCenter:
    def __init__(self):
        self.window = Gtk.Window(title="Centro de aplicaciones de FluidOS")
        self.window.set_default_size(720, 480)
        self.window.set_border_width(18)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.window.add(root)
        title = Gtk.Label(label="Centro de aplicaciones", xalign=0)
        title.set_markup("<big><b>Centro de aplicaciones</b></big>")
        root.pack_start(title, False, False, 0)
        note = Gtk.Label(
            label="Instala paquetes .fapp guardados en tu equipo. Esta edición aún no incluye tienda en línea ni firmas de editor.",
            xalign=0, wrap=True)
        root.pack_start(note, False, False, 0)
        self.store = Gtk.ListStore(str, str, str)
        self.view = Gtk.TreeView(model=self.store)
        for i, label in enumerate(("Identificador", "Versión", "Aplicación")):
            renderer = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(label, renderer, text=i)
            col.set_resizable(True)
            self.view.append_column(col)
        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True); scroll.set_vexpand(True); scroll.add(self.view)
        root.pack_start(scroll, True, True, 0)
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for label, callback in (("Actualizar lista", self.refresh),
                                ("Instalar archivo .fapp", self.install),
                                ("Desinstalar seleccionada", self.remove)):
            button = Gtk.Button(label=label)
            button.connect("clicked", lambda *_args, cb=callback: cb())
            bar.pack_start(button, False, False, 0)
        root.pack_start(bar, False, False, 0)
        self.window.connect("destroy", Gtk.main_quit)
        self.refresh()

    def message(self, title, text, error=False):
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True,
            message_type=Gtk.MessageType.ERROR if error else Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK, text=title)
        dialog.format_secondary_text(text)
        dialog.run(); dialog.destroy()

    def refresh(self):
        result = run_tool(["list"])
        self.store.clear()
        if result.returncode:
            self.message("No se pudo leer la lista", result.stdout, True); return
        for row in parse_installed(result.stdout): self.store.append(row)

    def install(self):
        chooser = Gtk.FileChooserDialog(title="Selecciona un paquete", parent=self.window,
            action=Gtk.FileChooserAction.OPEN,
            buttons=("Cancelar", Gtk.ResponseType.CANCEL, "Seleccionar", Gtk.ResponseType.ACCEPT))
        filt = Gtk.FileFilter(); filt.set_name("Paquetes FluidOS (*.fapp)"); filt.add_pattern("*.fapp")
        chooser.add_filter(filt)
        response = chooser.run(); path = chooser.get_filename() if response == Gtk.ResponseType.ACCEPT else None
        chooser.destroy()
        if not path: return
        verified = run_tool(["verify", path])
        if verified.returncode:
            self.message("Paquete rechazado", verified.stdout, True); return
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True,
            message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK_CANCEL,
            text="¿Instalar esta aplicación?")
        dialog.format_secondary_text(verified.stdout + "\nLos hashes comprueban integridad, no la identidad del editor. Instala solo paquetes de fuentes de confianza.")
        accepted = dialog.run() == Gtk.ResponseType.OK; dialog.destroy()
        if not accepted: return
        try:
            result = run_privileged("Instalar aplicación FluidOS", ["install", path])
        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            self.message("No se pudo iniciar la instalación", str(exc), True); return
        if result.returncode:
            self.message("La instalación no terminó correctamente", f"Código de salida: {result.returncode}", True)
        self.refresh()

    def remove(self):
        model, iterator = self.view.get_selection().get_selected()
        if iterator is None:
            self.message("Selecciona una aplicación", "Elige una fila antes de desinstalar."); return
        app_id = model[iterator][0]
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True,
            message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"¿Desinstalar {app_id}?")
        accepted = dialog.run() == Gtk.ResponseType.OK; dialog.destroy()
        if not accepted: return
        try:
            result = run_privileged("Desinstalar aplicación FluidOS", ["remove", app_id])
        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            self.message("No se pudo iniciar la desinstalación", str(exc), True); return
        if result.returncode:
            self.message("La desinstalación no terminó correctamente", f"Código de salida: {result.returncode}", True)
        self.refresh()

def main():
    if not Path(TOOL).exists():
        print(f"No se encuentra {TOOL}"); return 1
    app = AppCenter(); app.window.show_all(); Gtk.main(); return 0

if __name__ == "__main__":
    raise SystemExit(main())
