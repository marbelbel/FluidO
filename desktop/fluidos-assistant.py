#!/usr/local/bin/python3.12
"""Interfaz GTK del asistente local de FluidOS."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk, GLib

LIBDIR = "/usr/local/lib/fluidos"
if LIBDIR not in sys.path:
    sys.path.insert(0, LIBDIR)
from fluidos_assistant import AssistantEngine, AssistantError

APP_COMMANDS = {
    "navegador": ["firefox"], "firefox": ["firefox"],
    "ofimatica": ["libreoffice"], "libreoffice": ["libreoffice"],
    "ajustes": ["fluidos-control"], "aplicaciones": ["fluidos-app-center"],
    "usuarios": ["fluidos-users-panel"],
}


class AssistantWindow:
    def __init__(self):
        self.engine = AssistantEngine()
        self.window = Gtk.Window(title="Asistente de FluidOS")
        self.window.set_default_size(620, 560)
        self.window.set_border_width(14)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(root)
        title = Gtk.Label(label="Asistente local", xalign=0)
        title.set_markup("<span size='x-large' weight='bold'>Asistente local de FluidOS</span>")
        root.pack_start(title, False, False, 0)
        note = Gtk.Label(
            label="Funciona sin conexión. Busca nombres de archivos y ejecuta solo acciones permitidas con confirmación. "
                  "No incluye todavía un modelo generativo ni reconocimiento de voz.",
            xalign=0, line_wrap=True,
        )
        note.get_style_context().add_class("dim-label")
        root.pack_start(note, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.history = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.history.set_border_width(8)
        scroll.add(self.history)
        root.pack_start(scroll, True, True, 0)
        line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Escribe: buscar archivo, información del sistema, abre navegador…")
        self.entry.connect("activate", lambda *_: self.send())
        send = Gtk.Button(label="Enviar")
        send.connect("clicked", lambda *_: self.send())
        line.pack_start(self.entry, True, True, 0)
        line.pack_start(send, False, False, 0)
        root.pack_start(line, False, False, 0)
        self.add_message("FluidOS", self.engine.help_text())
        self.window.connect("destroy", lambda *_: Gtk.main_quit())

    def add_message(self, who: str, message: str):
        label = Gtk.Label(label=f"{who}: {message}", xalign=0, yalign=0)
        label.set_line_wrap(True)
        label.set_selectable(True)
        self.history.pack_start(label, False, False, 0)
        label.show()

    def confirm(self, title: str, message: str) -> bool:
        dialog = Gtk.MessageDialog(
            transient_for=self.window, flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO, text=title,
        )
        dialog.format_secondary_text(message)
        answer = dialog.run() == Gtk.ResponseType.YES
        dialog.destroy()
        return answer

    def open_file(self, value: str):
        try:
            path = self.engine.resolve_result(value)
        except (AssistantError, OSError) as exc:
            self.add_message("FluidOS", str(exc))
            return
        if not self.confirm("Abrir archivo", f"¿Quieres abrir este archivo?\n{path}"):
            self.add_message("FluidOS", "No he abierto el archivo.")
            return
        try:
            Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(str(path)).get_uri(), None)
            self.add_message("FluidOS", "He enviado el archivo a la aplicación asociada.")
        except GLib.Error as exc:
            self.add_message("FluidOS", f"No se pudo abrir: {exc.message}")

    def perform_action(self, action: dict):
        kind, target = action.get("type"), action.get("target")
        if kind == "app" and target in APP_COMMANDS:
            command = APP_COMMANDS[target]
            if not shutil.which(command[0]):
                self.add_message("FluidOS", f"No está instalada la aplicación {command[0]}.")
                return
            if self.confirm("Permiso para abrir una aplicación", f"¿Autorizas abrir {target}?"):
                try:
                    subprocess.Popen(command, close_fds=True, start_new_session=True)
                    self.add_message("FluidOS", f"He abierto {target}.")
                except OSError as exc:
                    self.add_message("FluidOS", f"No se pudo abrir: {exc}")
            else:
                self.add_message("FluidOS", "Acción cancelada.")
        elif kind == "power" and target in {"restart", "poweroff"}:
            label = "reiniciar" if target == "restart" else "apagar"
            if not self.confirm("Confirmar acción del sistema", f"¿Seguro que quieres {label} el equipo? Guarda tus documentos antes."):
                self.add_message("FluidOS", "Acción cancelada.")
                return
            doas = shutil.which("doas")
            shutdown = "/sbin/shutdown"
            if not doas or not os.path.exists(shutdown):
                self.add_message("FluidOS", "No está disponible doas o shutdown; no he cambiado el estado del equipo.")
                return
            mode = "-r" if target == "restart" else "-p"
            try:
                subprocess.Popen([doas, shutdown, mode, "now"], close_fds=True)
            except OSError as exc:
                self.add_message("FluidOS", f"No se pudo completar la acción: {exc}")

    def send(self):
        prompt = self.entry.get_text().strip()
        if not prompt:
            return
        self.entry.set_text("")
        self.add_message("Tú", prompt)
        result = self.engine.handle(prompt)
        self.add_message("FluidOS", result["message"])
        for value in result.get("files", []):
            path = Path(value)
            button = Gtk.Button(label=f"Abrir: {path.relative_to(self.engine.home)}")
            button.set_halign(Gtk.Align.START)
            button.connect("clicked", lambda _btn, filename=value: self.open_file(filename))
            self.history.pack_start(button, False, False, 0)
            button.show()
        if result.get("action"):
            self.perform_action(result["action"])

    def run(self):
        self.window.show_all()
        Gtk.main()


if __name__ == "__main__":
    try:
        AssistantWindow().run()
    except Exception as exc:
        print(f"FluidOS Assistant: {exc}", file=sys.stderr)
        raise SystemExit(1)
