#!/usr/local/bin/python3.12
"""Panel de ajustes FluidOS con preferencias visuales aplicables."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk

LIBDIR = "/usr/local/lib/fluidos"
if LIBDIR not in sys.path:
    sys.path.insert(0, LIBDIR)
from fluidos_personalization import load_settings, save_settings, apply_wayfire, PreferencesError

CSS = b"""
window { background: #071827; color: #f2f9ff; }
.header { background: #0c2940; padding: 18px; border-bottom: 1px solid #28516b; }
.title { font-size: 22px; font-weight: bold; color: #ffffff; }
.subtitle { color: #b6d5e7; }
.section { background: #102b41; border: 1px solid #31546b; border-radius: 12px; padding: 14px; }
button { border-radius: 9px; padding: 8px 14px; }
"""


class ControlPanel:
    def __init__(self):
        self.data = load_settings()
        self.window = Gtk.Window(title="Ajustes de FluidOS")
        self.window.set_default_size(650, 760)
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.window.add(root)
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        header.get_style_context().add_class("header")
        title = Gtk.Label(label="Ajustes de FluidOS", xalign=0)
        title.get_style_context().add_class("title")
        subtitle = Gtk.Label(label="Personaliza el aspecto y los escritorios de FluidOS.", xalign=0)
        subtitle.get_style_context().add_class("subtitle")
        header.pack_start(title, False, False, 0); header.pack_start(subtitle, False, False, 0)
        root.pack_start(header, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); body.set_border_width(16)
        scroll.add(body); root.pack_start(scroll, True, True, 0)

        app = self.data["appearance"]
        visual = self.section(body, "Apariencia")
        self.theme = self.combo(visual, "Tema", [("glass", "Liquid Glass"), ("dark", "Oscuro"), ("light", "Claro")], app["theme"])
        self.accent = self.entry(visual, "Color de acento (#RRGGBB)", app["accent"])
        self.wallpaper = self.combo(visual, "Fondo", [("ocean", "Océano"), ("aurora", "Aurora"), ("graphite", "Grafito")], app["wallpaper"])
        self.dock_size = self.combo(visual, "Tamaño del Dock", [("small", "Pequeño"), ("normal", "Normal"), ("large", "Grande")], app["dock_size"])
        self.mode = self.combo(visual, "Adaptación", [("automatic", "Automática"), ("desktop", "Escritorio"), ("tablet", "Tableta")], app["desktop_mode"])
        self.animations = self.switch(visual, "Animaciones de ventanas", app["animations"])

        desktops = self.section(body, "Escritorios virtuales")
        self.virtual_desktops = self.combo(desktops, "Distribución", [("1x1", "1 escritorio"), ("2x2", "4 escritorios (2 × 2)"), ("3x2", "6 escritorios (3 × 2)"), ("4x2", "8 escritorios (4 × 2)")], app["virtual_desktops"])
        note = Gtk.Label(label="El número de escritorios y las animaciones se configuran en Wayfire. Los cambios visuales del shell se aplican al reiniciar la sesión.", xalign=0, line_wrap=True)
        note.get_style_context().add_class("subtitle"); desktops.pack_start(note, False, False, 4)

        privacy = self.section(body, "Privacidad y asistente")
        privacy_data = self.data["privacy"]
        self.telemetry = self.switch(privacy, "Telemetría opcional", privacy_data["telemetry"])
        self.previews = self.switch(privacy, "Vistas previas de notificaciones", privacy_data["notification_previews"])
        # These toggles remain visible but disabled until real system services enforce them.
        self.telemetry.set_sensitive(False)
        self.previews.set_sensitive(False)
        local_note = Gtk.Label(label="El asistente funciona localmente con órdenes permitidas. Todavía no incluye un modelo generativo, voz ni sincronización. Los controles de telemetría y notificaciones están desactivados porque aún no hay servicios que apliquen esas políticas.", xalign=0, line_wrap=True)
        local_note.get_style_context().add_class("subtitle"); privacy.pack_start(local_note, False, False, 4)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10); footer.set_border_width(14)
        footer.pack_end(self.button("Guardar y aplicar", self.save), False, False, 0)
        footer.pack_end(self.button("Cerrar", self.window.destroy), False, False, 0)
        root.pack_end(footer, False, False, 0)
        self.window.connect("destroy", lambda *_: Gtk.main_quit())

    @staticmethod
    def section(parent, title):
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10); frame.get_style_context().add_class("section")
        label = Gtk.Label(label=title, xalign=0); label.set_markup(f"<b>{title}</b>")
        frame.pack_start(label, False, False, 0); parent.pack_start(frame, False, False, 0)
        return frame

    @staticmethod
    def row(parent, title):
        line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        line.pack_start(Gtk.Label(label=title, xalign=0), True, True, 0)
        parent.pack_start(line, False, False, 0)
        return line

    def combo(self, parent, title, options, selected):
        line = self.row(parent, title); widget = Gtk.ComboBoxText()
        for key, label in options: widget.append(key, label)
        widget.set_active_id(selected if selected in {key for key, _ in options} else options[0][0])
        line.pack_end(widget, False, False, 0); return widget

    def entry(self, parent, title, value):
        line = self.row(parent, title); widget = Gtk.Entry(); widget.set_text(str(value)); widget.set_width_chars(12)
        line.pack_end(widget, False, False, 0); return widget

    def switch(self, parent, title, active):
        line = self.row(parent, title); widget = Gtk.Switch(); widget.set_active(bool(active))
        line.pack_end(widget, False, False, 0); return widget

    @staticmethod
    def button(label, callback):
        item = Gtk.Button(label=label); item.connect("clicked", lambda *_: callback()); return item

    def message(self, kind, text):
        dialog = Gtk.MessageDialog(transient_for=self.window, flags=Gtk.DialogFlags.MODAL,
            message_type=kind, buttons=Gtk.ButtonsType.OK, text=text)
        dialog.run(); dialog.destroy()

    def save(self):
        accent = self.accent.get_text().strip()
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
            self.message(Gtk.MessageType.ERROR, "El color debe tener formato #RRGGBB, por ejemplo #69D9FF.")
            return
        self.data["schema"] = 2
        self.data["appearance"] = {
            "theme": self.theme.get_active_id(), "accent": accent.lower(),
            "wallpaper": self.wallpaper.get_active_id(), "dock_size": self.dock_size.get_active_id(),
            "desktop_mode": self.mode.get_active_id(), "animations": self.animations.get_active(),
            "virtual_desktops": self.virtual_desktops.get_active_id(),
        }
        self.data["privacy"] = {"telemetry": self.telemetry.get_active(),
            "notification_previews": self.previews.get_active(), "assistant_mode": "offline"}
        try:
            save_settings(self.data)
            wayfire_updated = apply_wayfire(self.data)
            if wayfire_updated:
                message = "Ajustes guardados. La configuración de Wayfire se ha actualizado. Cierra la sesión y vuelve a entrar para aplicar el fondo, tema, Dock y distribución de escritorios."
            else:
                message = "Ajustes guardados, pero no se encontró wayfire.ini. No se han podido actualizar los escritorios virtuales."
            self.message(Gtk.MessageType.INFO, message)
        except (OSError, PreferencesError) as exc:
            self.message(Gtk.MessageType.ERROR, f"No se pudieron aplicar los ajustes: {exc}")

    def run(self):
        self.window.show_all(); Gtk.main()


if __name__ == "__main__":
    try: ControlPanel().run()
    except Exception as exc:
        print(f"FluidOS Ajustes: {exc}", file=sys.stderr); raise SystemExit(1)
