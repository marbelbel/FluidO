#!/usr/local/bin/python3.12
"""FluidOS desktop shell: GTK 3 + GTK Layer Shell on Wayfire.

This is an early desktop shell. System status is read from the host; it does
not pretend that Wi-Fi, Bluetooth, brightness, or volume controls work when
there is no backend connected to them.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, Gio, GLib, Gtk, GtkLayerShell

APP = "FluidOS"
HOME = os.path.expanduser("~")

CSS = b"""
* { font-family: "DejaVu Sans", sans-serif; }
window { background: transparent; color: #f5fbff; }
.topbar { background: rgba(5, 13, 25, .88); border-bottom: 1px solid rgba(160,220,255,.25); padding: 5px 15px; }
.brand { color: #f8fdff; font-size: 16px; font-weight: 700; }
.brand-mark { color: #a7eaff; font-size: 22px; }
.top-button { color: #f5fbff; background: transparent; border: 0; border-radius: 10px; padding: 7px 11px; }
.top-button:hover { background: rgba(255,255,255,.13); }
.clock { color: #d9f1ff; font-size: 12px; padding: 0 8px; }
.dock { background: rgba(9, 30, 53, .82); border: 1px solid rgba(176,229,255,.36); border-radius: 20px; padding: 8px 11px; }
.dock button { color: white; background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.12); border-radius: 14px; min-width: 52px; min-height: 52px; font-size: 22px; }
.dock button:hover { background: rgba(110,190,240,.30); }
.panel { background: rgba(8, 24, 43, .97); border: 1px solid rgba(160,220,255,.35); border-radius: 20px; padding: 17px; }
.panel-title { color: #ffffff; font-size: 17px; font-weight: 700; }
.muted { color: #b9d3e6; font-size: 12px; }
.app-button { color: white; background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.12); border-radius: 14px; padding: 13px; min-width: 110px; min-height: 85px; }
.app-button:hover { background: rgba(90,170,230,.28); }
.status-row { background: rgba(255,255,255,.07); border-radius: 10px; padding: 9px; }
"""


def run_output(argv, fallback="No disponible"):
    try:
        result = subprocess.run(argv, check=False, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=3)
        value = result.stdout.strip()
        return value if result.returncode == 0 and value else fallback
    except (OSError, subprocess.SubprocessError):
        return fallback


def launch(command):
    executable = command[0]
    if not shutil.which(executable):
        show_message(f"No se encuentra la aplicación: {executable}")
        return
    try:
        subprocess.Popen(command, close_fds=True, start_new_session=True)
    except OSError as exc:
        show_message(f"No se pudo abrir {executable}: {exc}")


def show_message(message):
    dialog = Gtk.MessageDialog(
        transient_for=None, flags=Gtk.DialogFlags.MODAL,
        message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
        text=message,
    )
    dialog.set_title(APP)
    dialog.run()
    dialog.destroy()


class FluidShell:
    def __init__(self):
        if not GtkLayerShell.is_supported():
            raise RuntimeError("La sesión actual no ofrece GTK Layer Shell. Inicia FluidOS con Wayfire.")
        self.windows = []
        self.settings = self._load_preferences()
        self._install_css()
        self._create_wallpaper()
        self._create_topbar()
        self._create_dock()
        self.update_clock()
        GLib.timeout_add_seconds(20, self.update_clock)

    def _load_preferences(self):
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
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def layer_window(self, namespace, layer, size, anchors, margins=None, keyboard=False):
        win = Gtk.Window(title=f"{APP} {namespace}")
        win.set_decorated(False)
        win.set_resizable(False)
        win.set_app_paintable(True)
        win.set_default_size(*size)
        GtkLayerShell.init_for_window(win)
        GtkLayerShell.set_namespace(win, f"fluido-{namespace}")
        GtkLayerShell.set_layer(win, layer)
        for edge, enabled in anchors.items():
            GtkLayerShell.set_anchor(win, edge, enabled)
        for edge, amount in (margins or {}).items():
            GtkLayerShell.set_margin(win, edge, amount)
        GtkLayerShell.set_keyboard_mode(
            win,
            GtkLayerShell.KeyboardMode.ON_DEMAND if keyboard
            else GtkLayerShell.KeyboardMode.NONE,
        )
        self.windows.append(win)
        win.connect("destroy", lambda *_: Gtk.main_quit())
        return win

    def _create_wallpaper(self):
        self.wallpaper = self.layer_window(
            "background", GtkLayerShell.Layer.BACKGROUND, (1280, 720),
            {GtkLayerShell.Edge.TOP: True, GtkLayerShell.Edge.BOTTOM: True,
             GtkLayerShell.Edge.LEFT: True, GtkLayerShell.Edge.RIGHT: True},
        )
        area = Gtk.DrawingArea()
        area.connect("draw", self.draw_wallpaper)
        self.wallpaper.add(area)
        self.wallpaper.show_all()

    @staticmethod
    def draw_wallpaper(widget, cr):
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        gradient = __import__("cairo").LinearGradient(0, 0, width, height)
        gradient.add_color_stop_rgb(0.0, 0.012, 0.035, 0.075)
        gradient.add_color_stop_rgb(0.52, 0.015, 0.12, 0.22)
        gradient.add_color_stop_rgb(1.0, 0.015, 0.25, 0.34)
        cr.set_source(gradient)
        cr.paint()
        cr.set_source_rgba(.27, .76, .94, .13)
        cr.arc(width * .78, height * .28, min(width, height) * .36, 0, 6.283)
        cr.fill()
        cr.set_source_rgba(.63, .91, 1, .16)
        cr.set_line_width(max(13, width * .009))
        cr.move_to(-width * .08, height * .79)
        cr.curve_to(width * .22, height * .39, width * .48, height * 1.02,
                    width * .72, height * .68)
        cr.curve_to(width * .89, height * .45, width * .98, height * .61,
                    width * 1.08, height * .73)
        cr.stroke()
        return False

    def _create_topbar(self):
        self.topbar = self.layer_window(
            "topbar", GtkLayerShell.Layer.TOP, (1280, 44),
            {GtkLayerShell.Edge.TOP: True, GtkLayerShell.Edge.LEFT: True,
             GtkLayerShell.Edge.RIGHT: True},
        )
        GtkLayerShell.set_exclusive_zone(self.topbar, 44)
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.get_style_context().add_class("topbar")
        self.topbar.add(bar)
        mark = Gtk.Label(label="◈")
        mark.get_style_context().add_class("brand-mark")
        bar.pack_start(mark, False, False, 0)
        brand = Gtk.Label(label=APP)
        brand.get_style_context().add_class("brand")
        bar.pack_start(brand, False, False, 4)
        bar.pack_start(self.top_button("Aplicaciones", self.show_launcher), False, False, 5)
        bar.pack_start(self.top_button("Archivos", self.open_files), False, False, 0)
        bar.pack_start(self.top_button("Sistema", self.show_system), False, False, 0)
        bar.pack_start(self.top_button("Ajustes", lambda: launch(["fluidos-control"])), False, False, 0)
        bar.pack_start(Gtk.Box(), True, True, 0)
        self.clock = Gtk.Label(label="")
        self.clock.get_style_context().add_class("clock")
        bar.pack_start(self.clock, False, False, 5)
        bar.pack_start(self.top_button("Salir", self.show_power), False, False, 0)
        self.topbar.show_all()

    @staticmethod
    def top_button(text, callback):
        btn = Gtk.Button(label=text)
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.get_style_context().add_class("top-button")
        btn.connect("clicked", lambda *_: callback())
        return btn

    def _create_dock(self):
        self.dock_window = self.layer_window(
            "dock", GtkLayerShell.Layer.TOP, (440, 72),
            {GtkLayerShell.Edge.BOTTOM: True}, {GtkLayerShell.Edge.BOTTOM: 16},
        )
        GtkLayerShell.set_exclusive_zone(self.dock_window, -1)
        dock = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dock.get_style_context().add_class("dock")
        self.dock_window.add(dock)
        items = [
            ("◈", "Aplicaciones", self.show_launcher),
            ("▤", "Archivos", self.open_files),
            ("◎", "Navegador", lambda: launch(["firefox"])),
            ("⚙", "Sistema", self.show_system),
            ("✧", "Ajustes", lambda: launch(["fluidos-control"])),
        ]
        for glyph, title, callback in items:
            btn = Gtk.Button(label=glyph)
            btn.set_tooltip_text(title)
            btn.connect("clicked", lambda *_args, cb=callback: cb())
            dock.pack_start(btn, False, False, 0)
        self.dock_window.show_all()

    def update_clock(self):
        self.clock.set_text(datetime.now().strftime("%a %d %b   %H:%M"))
        return True

    def show_panel(self, title, width=440, height=330):
        win = self.layer_window(
            title.lower().replace(" ", "-"), GtkLayerShell.Layer.OVERLAY,
            (width, height), {GtkLayerShell.Edge.TOP: True, GtkLayerShell.Edge.RIGHT: True},
            {GtkLayerShell.Edge.TOP: 58, GtkLayerShell.Edge.RIGHT: 20}, True,
        )
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.get_style_context().add_class("panel")
        win.add(root)
        heading = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_label = Gtk.Label(label=title, xalign=0)
        title_label.get_style_context().add_class("panel-title")
        heading.pack_start(title_label, True, True, 0)
        close = Gtk.Button(label="×")
        close.get_style_context().add_class("top-button")
        close.connect("clicked", lambda *_: win.hide())
        heading.pack_end(close, False, False, 0)
        root.pack_start(heading, False, False, 0)
        return win, root

    def show_launcher(self):
        win, root = self.show_panel("Aplicaciones", 430, 300)
        search = Gtk.Entry()
        search.set_placeholder_text("Buscar una aplicación")
        root.pack_start(search, False, False, 0)
        grid = Gtk.Grid(row_spacing=9, column_spacing=9)
        root.pack_start(grid, True, True, 0)
        apps = [
            ("▤\nArchivos", self.open_files),
            ("◎\nNavegador", lambda: launch(["firefox"])),
            ("⚙\nInformación del sistema", self.show_system),
            ("✧\nAjustes", lambda: launch(["fluidos-control"])),
            ("▦\nOfimática", lambda: launch(["libreoffice"])),
            ("⏻\nApagar o reiniciar", self.show_power),
        ]
        if os.path.exists("/etc/fluidos-live"):
            apps.insert(0, ("⬇\nInstalar FluidOS", self.start_installer))
        for index, (name, callback) in enumerate(apps):
            btn = Gtk.Button(label=name)
            btn.get_style_context().add_class("app-button")
            btn.connect("clicked", lambda *_args, cb=callback, panel=win: (panel.hide(), cb()))
            grid.attach(btn, index % 3, index // 3, 1, 1)

        def filter_apps(entry):
            query = entry.get_text().strip().lower()
            for child in grid.get_children():
                label = child.get_label().replace("\n", " ").lower()
                child.set_visible(not query or query in label)

        search.connect("changed", filter_apps)
        win.show_all()

    def start_installer(self):
        # The terminal is hidden from normal use. It opens only for this
        # technical installation flow so the user can see disk warnings.
        if not shutil.which("foot"):
            show_message("No se encuentra el instalador visual de consola. Abre una consola de rescate y ejecuta: doas /usr/local/sbin/fluidos-install")
            return
        launch(["foot", "-T", "Instalar FluidOS", "-e", "doas", "/usr/local/sbin/fluidos-install"])

    def open_files(self):
        dialog = Gtk.FileChooserDialog(
            title="Archivos", parent=None, action=Gtk.FileChooserAction.OPEN,
            buttons=("Cancelar", Gtk.ResponseType.CANCEL,
                     "Abrir", Gtk.ResponseType.ACCEPT),
        )
        dialog.set_current_folder(HOME)
        response = dialog.run()
        filename = dialog.get_filename() if response == Gtk.ResponseType.ACCEPT else None
        dialog.destroy()
        if filename:
            try:
                Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(filename).get_uri(), None)
            except GLib.Error as exc:
                show_message(f"No se pudo abrir el archivo: {exc.message}")

    def show_system(self):
        win, root = self.show_panel("Información del sistema", 460, 330)
        info = [
            ("Sistema", "FluidOS Live" if os.path.exists("/etc/fluidos-live") else "FluidOS instalado"),
            ("Versión del kernel", run_output(["uname", "-r"])),
            ("Arquitectura", run_output(["uname", "-m"])),
            ("Procesadores", run_output(["sysctl", "-n", "hw.ncpu"])),
            ("Interfaces de red", run_output(["ifconfig", "-l"])),
            ("Memoria", run_output(["sysctl", "-n", "hw.physmem"], "No disponible") + " bytes"),
        ]
        for name, value in info:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.get_style_context().add_class("status-row")
            left = Gtk.Label(label=name, xalign=0)
            right = Gtk.Label(label=value, xalign=1)
            right.set_selectable(True)
            row.pack_start(left, True, True, 0)
            row.pack_end(right, False, False, 0)
            root.pack_start(row, False, False, 0)
        note = Gtk.Label(
            label="Modo Live: puedes probarlo sin instalar. El instalador está en Aplicaciones.",
            xalign=0,
        ) if os.path.exists("/etc/fluidos-live") else Gtk.Label(
            label="FluidOS instalado. Algunas funciones dependen del hardware.", xalign=0
        )
        note.get_style_context().add_class("muted")
        root.pack_start(note, False, False, 0)
        win.show_all()

    def show_power(self):
        win, root = self.show_panel("Sesión", 300, 190)
        for title, command in (("Cerrar sesión", ["pkill", "-KILL", "-u", os.environ.get("USER", "fluid")]),
                               ("Reiniciar", ["doas", "/sbin/shutdown", "-r", "now"]),
                               ("Apagar", ["doas", "/sbin/shutdown", "-p", "now"])):
            btn = Gtk.Button(label=title)
            btn.get_style_context().add_class("app-button")
            btn.connect("clicked", lambda *_args, cmd=command: launch(cmd))
            root.pack_start(btn, False, False, 0)
        win.show_all()

    def run(self):
        Gtk.main()


def main():
    try:
        FluidShell().run()
    except Exception as exc:
        print(f"FluidOS: no se pudo iniciar el escritorio: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
