#!/usr/local/bin/python3.12
"""Panel GTK para administrar cuentas personales de FluidOS en FreeBSD."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

TOOL = "/usr/local/bin/fluidos-users"
USERNAME = re.compile(r"^[a-z_][a-z0-9_-]{0,15}$")


class UsersPanel:
    def __init__(self):
        self.window = Gtk.Window(title="Usuarios de FluidOS")
        self.window.set_default_size(620, 420)
        self.window.set_border_width(16)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.window.add(root)

        heading = Gtk.Label(label="Usuarios de FluidOS", xalign=0)
        heading.set_markup("<big><b>Usuarios de FluidOS</b></big>")
        root.pack_start(heading, False, False, 0)
        note = Gtk.Label(
            label="Administra cuentas personales. Las cuentas del sistema y la cuenta principal fluid están protegidas.",
            xalign=0, wrap=True,
        )
        root.pack_start(note, False, False, 0)

        self.store = Gtk.ListStore(str, str, str)
        self.view = Gtk.TreeView(model=self.store)
        for index, label in enumerate(("Usuario", "UID", "Carpeta personal")):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(label, renderer, text=index)
            column.set_resizable(True)
            self.view.append_column(column)
        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        scroll.add(self.view)
        root.pack_start(scroll, True, True, 0)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for label, callback in (("Actualizar", self.refresh),
                                ("Crear usuario", self.add_user),
                                ("Eliminar seleccionado", self.remove_user)):
            button = Gtk.Button(label=label)
            button.connect("clicked", lambda *_args, fn=callback: fn())
            actions.pack_start(button, False, False, 0)
        root.pack_start(actions, False, False, 0)
        self.window.connect("destroy", Gtk.main_quit)
        self.refresh()

    def message(self, title: str, detail: str, error: bool = False):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.ERROR if error else Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(detail)
        dialog.run()
        dialog.destroy()

    def run_privileged(self, title: str, args: list[str]):
        terminal = shutil.which("foot")
        if not terminal:
            self.message("Falta Foot", "No se encuentra foot para mostrar la autorización de doas.", True)
            return
        try:
            result = subprocess.run(
                [terminal, "-T", title, "-e", "doas", TOOL, *args],
                check=False, timeout=300,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            self.message("No se pudo ejecutar la operación", str(exc), True)
            return
        if result.returncode:
            self.message("La operación no terminó", f"Código de salida: {result.returncode}", True)
        self.refresh()

    def refresh(self):
        try:
            result = subprocess.run(
                [TOOL, "list"], text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, check=False, timeout=15,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            self.message("No se pudo consultar a los usuarios", str(exc), True)
            return
        if result.returncode:
            self.message("No se pudo consultar a los usuarios", result.stdout, True)
            return
        self.store.clear()
        for line in result.stdout.splitlines():
            parts = line.split(maxsplit=2)
            if len(parts) == 3 and parts[1].isdigit():
                self.store.append(parts)

    def add_user(self):
        dialog = Gtk.Dialog(
            title="Crear usuario", transient_for=self.window, modal=True,
            buttons=("Cancelar", Gtk.ResponseType.CANCEL,
                    "Continuar", Gtk.ResponseType.OK),
        )
        dialog.set_default_size(360, 120)
        area = dialog.get_content_area()
        area.set_spacing(8)
        area.set_border_width(12)
        area.pack_start(Gtk.Label(label="Nombre (1 a 16 caracteres, minúsculas):", xalign=0), False, False, 0)
        entry = Gtk.Entry()
        entry.set_placeholder_text("por ejemplo, ana")
        area.pack_start(entry, False, False, 0)
        dialog.show_all()
        response = dialog.run()
        username = entry.get_text().strip()
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
            return
        if not USERNAME.fullmatch(username):
            self.message("Nombre no válido", "Usa minúsculas, números, guion o guion bajo. Máximo 16 caracteres.", True)
            return
        self.run_privileged("Crear usuario de FluidOS", ["add", username])

    def remove_user(self):
        model, iterator = self.view.get_selection().get_selected()
        if iterator is None:
            self.message("Selecciona un usuario", "Elige una cuenta de la lista.")
            return
        username = model[iterator][0]
        dialog = Gtk.MessageDialog(
            transient_for=self.window, modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"¿Eliminar el usuario {username}?",
        )
        dialog.format_secondary_text("Se eliminará su cuenta y su carpeta personal. Esta acción no se puede deshacer.")
        accepted = dialog.run() == Gtk.ResponseType.OK
        dialog.destroy()
        if accepted:
            self.run_privileged(
                "Eliminar usuario de FluidOS",
                ["remove", username, "--confirm", f"ELIMINAR USUARIO {username}"],
            )


def main() -> int:
    if not shutil.which(TOOL):
        print(f"No se encuentra la herramienta {TOOL}", file=sys.stderr)
        return 1
    panel = UsersPanel()
    panel.window.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
