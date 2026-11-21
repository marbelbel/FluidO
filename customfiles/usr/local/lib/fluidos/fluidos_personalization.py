#!/usr/bin/env python3
"""Preferencias visuales de FluidOS y configuración segura de Wayfire."""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path

DEFAULTS = {
    "schema": 2,
    "appearance": {
        "theme": "glass", "accent": "#69d9ff", "desktop_mode": "automatic",
        "animations": True, "wallpaper": "ocean", "dock_size": "normal",
        "virtual_desktops": "2x2"
    },
    "privacy": {"telemetry": False, "notification_previews": True, "assistant_mode": "offline"},
    "updates": {"automatic_apps": True},
}


class PreferencesError(Exception):
    pass


def config_dir(home: Path | None = None) -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", str((home or Path.home()) / ".config")))
    return base / "fluidos"


def load_settings(path: Path | None = None) -> dict:
    target = path or (config_dir() / "settings.json")
    data = json.loads(json.dumps(DEFAULTS))
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return data
    except (OSError, json.JSONDecodeError) as exc:
        raise PreferencesError(f"No se pueden leer los ajustes: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema") not in (1, 2):
        raise PreferencesError("El archivo de ajustes tiene un esquema no compatible.")
    for section in ("appearance", "privacy", "updates"):
        if isinstance(raw.get(section), dict):
            data[section].update(raw[section])
    data["schema"] = 2
    return validate_settings(data)


def validate_settings(data: dict) -> dict:
    if not isinstance(data, dict):
        raise PreferencesError("El archivo de ajustes debe contener un objeto JSON.")
    appearance = data.get("appearance", {})
    if not isinstance(appearance, dict):
        raise PreferencesError("La sección de apariencia no es válida.")
    if not isinstance(appearance.get("theme"), str) or appearance["theme"] not in {"glass", "dark", "light"}:
        raise PreferencesError("Tema no válido.")
    accent = appearance.get("accent", "#69d9ff")
    if not isinstance(accent, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
        raise PreferencesError("El color de acento debe usar formato #RRGGBB.")
    choices = {
        "desktop_mode": {"automatic", "desktop", "tablet"},
        "wallpaper": {"ocean", "aurora", "graphite"},
        "dock_size": {"small", "normal", "large"},
        "virtual_desktops": {"1x1", "2x2", "3x2", "4x2"},
    }
    messages = {
        "desktop_mode": "Modo de dispositivo no válido.",
        "wallpaper": "Fondo no válido.",
        "dock_size": "Tamaño del Dock no válido.",
        "virtual_desktops": "Número de escritorios virtuales no válido.",
    }
    for key, allowed in choices.items():
        if not isinstance(appearance.get(key), str) or appearance[key] not in allowed:
            raise PreferencesError(messages[key])
    if not isinstance(appearance.get("animations", True), bool):
        raise PreferencesError("El ajuste de animaciones debe ser verdadero o falso.")
    appearance["animations"] = appearance.get("animations", True)
    privacy = data.get("privacy", {})
    if not isinstance(privacy, dict):
        raise PreferencesError("La sección de privacidad no es válida.")
    for key in ("telemetry", "notification_previews"):
        if not isinstance(privacy.get(key, False), bool):
            raise PreferencesError(f"El ajuste {key} debe ser verdadero o falso.")
    return data


def save_settings(data: dict, path: Path | None = None) -> Path:
    target = path or (config_dir() / "settings.json")
    data = validate_settings(data)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".settings-", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return target


def apply_wayfire(settings: dict, path: Path | None = None) -> bool:
    target = path or (Path.home() / ".config/wayfire/wayfire.ini")
    if not target.exists():
        return False
    settings = validate_settings(settings)
    appearance = settings["appearance"]
    dimensions = appearance["virtual_desktops"].split("x", 1)
    width, height = int(dimensions[0]), int(dimensions[1])
    original = target.read_text(encoding="utf-8")
    lines = original.splitlines()
    in_core = False
    seen_width = seen_height = seen_plugins = False
    updated = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_core = stripped.lower() == "[core]"
        if in_core and stripped.startswith("vwidth") and "=" in line:
            updated.append(f"vwidth = {width}"); seen_width = True; continue
        if in_core and stripped.startswith("vheight") and "=" in line:
            updated.append(f"vheight = {height}"); seen_height = True; continue
        if in_core and stripped.startswith("plugins") and "=" in line:
            plugins = stripped.split("=", 1)[1].split()
            plugins = [p for p in plugins if p != "animate"]
            if appearance["animations"]:
                plugins.append("animate")
            updated.append("plugins = " + " ".join(dict.fromkeys(plugins)))
            seen_plugins = True
            continue
        updated.append(line)
    if not any(line.strip().lower() == "[core]" for line in lines):
        raise PreferencesError("El archivo wayfire.ini no contiene la sección [core].")
    if not (seen_width and seen_height and seen_plugins):
        raise PreferencesError("wayfire.ini no contiene vwidth, vheight y plugins en [core].")
    fd, temp_name = tempfile.mkstemp(prefix=".wayfire-", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write("\n".join(updated) + "\n")
            stream.flush(); os.fsync(stream.fileno())
        os.chmod(temp_name, target.stat().st_mode & 0o777)
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Aplicar preferencias visuales de FluidOS")
    parser.add_argument("action", choices=("apply", "show"))
    args = parser.parse_args()
    try:
        data = load_settings()
        if args.action == "apply":
            changed = apply_wayfire(data)
            print("Configuración Wayfire actualizada." if changed else "No hay wayfire.ini; se aplicarán los ajustes al iniciar Wayfire.")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
    except (PreferencesError, OSError) as exc:
        print(f"FluidOS Personalización: {exc}", file=__import__("sys").stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
