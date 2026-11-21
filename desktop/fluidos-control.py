#!/usr/local/bin/python3.12
"""FluidOS graphical settings. Preferences are stored per user as JSON."""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "fluidos"
CONFIG_FILE = CONFIG_DIR / "settings.json"
DEFAULTS = {
    "schema": 1,
    "appearance": {"theme": "glass", "accent": "#69d9ff", "desktop_mode": "automatic", "animations": True},
    "privacy": {"telemetry": False, "notification_previews": True, "assistant_mode": "offline"},
    "updates": {"automatic_apps": True},
}

CSS = b"""
window { background: #071827; color: #f2f9ff; }
.header { background: #0c2940; padding: 18px; border-bottom: 1px solid #28516b; }
.title { font-size: 22px; font-weight: bold; color: #ffffff; }
.subtitle { color: #b6d5e7; }
.section { background: #102b41; border: 1px solid #31546b; border-radius: 12px; padding: 14px; }
button { border-radius: 9px; padding: 8px 14px; }
"""


def load_settings():
    data = json.loads(json.dumps(DEFAULTS))
    try:
        loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return data
    except (OSError, json.JSONDecodeError):
        return data
    if isinstance(loaded, dict) and loaded.get("schema") == 1:
        for section in ("appearance", "privacy", "updates"):
            if isinstance(loaded.get(section), dict):
                data[section].update(loaded[section])
    return data


def save_settings(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".settings-", dir=str(CONFIG_DIR))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, CONFIG_FILE)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


class ControlPanel:
    def __init__(self):
        self.data = load_settings()
        self.window = Gtk.Window(title="Ajustes de FluidOS")
        self.window.set_default_size(620, 680)
        self.window.set_border_width(0)
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        header.get_style_context().add_class("header")
        title = Gtk.Label(label="Ajustes de FluidOS", xalign=0)
        title.get_style_context().add_class("title")
        subtitle = Gtk.Label(label="Personaliza el escritorio, las actualizaciones y tu privacidad.", xalign=0)
        subtitle.get_style_context().add_class("subtitle")
        header.pack_start(title, False, False, 0)
        header.pack_start(subtitle, False, False, 0)
        root.pack_start(header, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_border_width(16)
        scroll.add(body)
        root.pack_start(scroll, True, True, 0)
        self.window.add(root)

        appearance = self.section(body, "Apariencia")
        self.theme = self.combo(appearance, "Estilo visual", [("glass", "Liquid Glass"), ("dark", "Oscuro"), ("light", "Claro")], self.data["appearance"]["theme"])
        self.accent = self.entry(appearance, "Color de acento (HEX)", self.data["appearance"]["accent"])
        self.mode = self.combo(appearance, "Tipo de dispositivo", [("automatic", "Adaptativo automático"), ("desktop", "Escritorio"), ("tablet", "Tableta")], self.data["appearance"]["desktop_mode"])
        self.animations = self.switch(appearance, "Animaciones", self.data["appearance"]["animations"])

        privacy = self.section(body, "Privacidad e inteligencia artificial")
        self.telemetry = self.switch(privacy, "Telemetría opcional", self.data["privacy"]["telemetry"])
        self.previews = self.switch(privacy, "Mostrar vistas previas de notificaciones", self.data["privacy"]["notification_previews"])
        self.assistant = self.combo(privacy, "Modo preferido del asistente", [("offline", "Local / sin conexión"), ("online", "En línea"), ("ask", "Preguntar cada vez")], self.data["privacy"]["assistant_mode"])
        note = Gtk.Label(label="El selector guarda tu preferencia. El asistente de IA y sus proveedores aún no están conectados en esta versión.", xalign=0, line_wrap=True)
        note.get_style_context().add_class("subtitle")
        privacy.pack_start(note, False, False, 4)

        updates = self.section(body, "Aplicaciones")
        self.auto_updates = self.switch(updates, "Preferir actualizaciones automáticas", self.data["updates"]["automatic_apps"])
        update_note = Gtk.Label(label="La tienda y el servicio de actualizaciones por aplicación están en desarrollo; esta opción se guarda, pero aún no ejecuta actualizaciones.", xalign=0, line_wrap=True)
        update_note.get_style_context().add_class("subtitle")
        updates.pack_start(update_note, False, False, 4)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        footer.set_border_width(14)
        footer.pack_end(self.button("Guardar ajustes", self.save), False, False, 0)
        footer.pack_end(self.button("Cerrar", self.window.destroy), False, False, 0)
        root.pack_end(footer, False, False, 0)
        self.window.connect("destroy", lambda *_: Gtk.main_quit())

    @staticmethod
    def section(parent, title):
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        frame.get_style_context().add_class("section")
        label = Gtk.Label(label=title, xalign=0)
        label.set_markup(f"<b>{title}</b>")
        frame.pack_start(label, False, False, 0)
        parent.pack_start(frame, False, False, 0)
        return frame

    @staticmethod
    def row(parent, title):
        line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        label = Gtk.Label(label=title, xalign=0)
        line.pack_start(label, True, True, 0)
        parent.pack_start(line, False, False, 0)
        return line

    def combo(self, parent, title, options, selected):
        line = self.row(parent, title)
        widget = Gtk.ComboBoxText()
        for key, label in options:
            widget.append(key, label)
        widget.set_active_id(selected if selected in {key for key, _ in options} else options[0][0])
        line.pack_end(widget, False, False, 0)
        return widget

    def entry(self, parent, title, value):
        line = self.row(parent, title)
        widget = Gtk.Entry()
        widget.set_text(str(value))
        widget.set_width_chars(12)
        line.pack_end(widget, False, False, 0)
        return widget

    def switch(self, parent, title, active):
        line = self.row(parent, title)
        widget = Gtk.Switch()
        widget.set_active(bool(active))
        line.pack_end(widget, False, False, 0)
        return widget

    @staticmethod
    def button(label, callback):
        button = Gtk.Button(label=label)
        button.connect("clicked", lambda *_: callback())
        return button

    def save(self):
        accent = self.accent.get_text().strip()
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
            dialog = Gtk.MessageDialog(transient_for=self.window, flags=Gtk.DialogFlags.MODAL, message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK, text="El color debe tener formato #RRGGBB, por ejemplo #69D9FF.")
            dialog.run(); dialog.destroy(); return
        self.data["appearance"] = {"theme": self.theme.get_active_id(), "accent": accent.lower(), "desktop_mode": self.mode.get_active_id(), "animations": self.animations.get_active()}
        self.data["privacy"] = {"telemetry": self.telemetry.get_active(), "notification_previews": self.previews.get_active(), "assistant_mode": self.assistant.get_active_id()}
        self.data["updates"] = {"automatic_apps": self.auto_updates.get_active()}
        try:
            save_settings(self.data)
            dialog = Gtk.MessageDialog(transient_for=self.window, flags=Gtk.DialogFlags.MODAL, message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, text="Ajustes guardados. Algunos ajustes visuales se aplicarán al volver a iniciar sesión.")
            dialog.run(); dialog.destroy()
        except OSError as exc:
            dialog = Gtk.MessageDialog(transient_for=self.window, flags=Gtk.DialogFlags.MODAL, message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK, text=f"No se pudieron guardar los ajustes: {exc}")
            dialog.run(); dialog.destroy()

    def run(self):
        self.window.show_all()
        Gtk.main()


if __name__ == "__main__":
    try:
        ControlPanel().run()
    except Exception as exc:
        print(f"FluidOS Ajustes: {exc}", file=sys.stderr)
        sys.exit(1)
