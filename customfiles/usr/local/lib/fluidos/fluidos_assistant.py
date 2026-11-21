#!/usr/bin/env python3
"""Motor local y seguro del asistente FluidOS. No ejecuta comandos arbitrarios."""
from __future__ import annotations

import os
import platform
import re
import unicodedata
from datetime import datetime
from pathlib import Path

APP_COMMANDS = {
    "navegador": ("firefox",),
    "firefox": ("firefox",),
    "ofimatica": ("libreoffice",),
    "libreoffice": ("libreoffice",),
    "ajustes": ("fluidos-control",),
    "aplicaciones": ("fluidos-app-center",),
    "usuarios": ("fluidos-users-panel",),
}


class AssistantError(Exception):
    """Error controlado del asistente."""


class AssistantEngine:
    """Asistente offline basado en órdenes permitidas y búsqueda local."""

    def __init__(self, home: str | Path | None = None):
        self.home = Path(home or Path.home()).expanduser().resolve()
        self.last_results: list[Path] = []

    @staticmethod
    def _normalise(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        return "".join(char for char in decomposed if not unicodedata.combining(char))

    @staticmethod
    def help_text() -> str:
        return (
            "Puedo buscar archivos por su nombre, mostrar información del equipo y abrir "
            "aplicaciones permitidas. Prueba: «buscar archivo informe», «información del "
            "sistema», «abre navegador» o «abre ajustes». No ejecuto órdenes de terminal."
        )

    def search_files(self, query: str, limit: int = 20) -> list[Path]:
        query = query.strip().casefold()
        if len(query) < 2:
            raise AssistantError("Escribe al menos dos letras para buscar.")
        if not self.home.is_dir():
            return []
        found: list[Path] = []
        visited_dirs = 0
        for current, dirs, files in os.walk(self.home, followlinks=False):
            base = Path(current)
            dirs[:] = [d for d in dirs if not d.startswith(".") and not (base / d).is_symlink()]
            visited_dirs += 1
            if visited_dirs > 1200:
                break
            for name in files:
                candidate = base / name
                if query in name.casefold() and not candidate.is_symlink():
                    try:
                        resolved = candidate.resolve(strict=True)
                        resolved.relative_to(self.home)
                    except (OSError, ValueError):
                        continue
                    if resolved.is_file():
                        found.append(resolved)
                        if len(found) >= max(1, min(limit, 50)):
                            self.last_results = found
                            return found
        self.last_results = found
        return found

    def handle(self, text: str) -> dict:
        raw = text.strip()
        query = self._normalise(raw)
        if not raw:
            return {"message": "Escribe una petición para empezar."}
        if query in {"ayuda", "help", "qué puedes hacer", "que puedes hacer"}:
            return {"message": self.help_text()}
        if any(term in query for term in ("hora", "fecha", "qué día", "que dia")):
            return {"message": "Fecha y hora del equipo: " + datetime.now().astimezone().strftime("%d/%m/%Y %H:%M %Z")}
        if any(term in query for term in ("información del sistema", "informacion del sistema", "estado del sistema", "mi equipo")):
            info = f"FluidOS sobre {platform.system()} {platform.release()} ({platform.machine()}). Python {platform.python_version()}."
            return {"message": info}
        match = re.search(r"(?:buscar|busca|encuentra)\s+(?:el\s+)?(?:archivo|fichero)\s+(.+)$", query)
        if match:
            term = match.group(1).strip().strip('"\' ')
            try:
                results = self.search_files(term)
            except AssistantError as exc:
                return {"message": str(exc)}
            if not results:
                return {"message": f"No he encontrado archivos cuyo nombre contenga «{term}»."}
            return {"message": f"He encontrado {len(results)} archivo(s). Pulsa uno para abrirlo, previa confirmación.", "files": [str(p) for p in results]}
        for phrase in ("abre ", "abrir ", "inicia ", "iniciar ", "ejecuta "):
            if query.startswith(phrase):
                target = query[len(phrase):].strip()
                target = target.replace("el ", "", 1) if target.startswith("el ") else target
                if target in APP_COMMANDS:
                    return {"message": f"Puedo abrir {target}. Confirma la acción en la ventana.", "action": {"type": "app", "target": target}}
                if target in {"asistente", "chat"}:
                    return {"message": "El asistente ya está abierto."}
                return {"message": "Esa aplicación no está en mi lista segura. No ejecutaré comandos de terminal."}
        restart_request = re.fullmatch(
            r"(?:por favor )?(?:reinicia|reiniciar)(?: fluidos| el equipo| equipo| el ordenador| ordenador)?[.!?]*",
            query,
        )
        poweroff_request = re.fullmatch(
            r"(?:por favor )?(?:apaga|apagar)(?: fluidos| el equipo| equipo| el ordenador| ordenador)?[.!?]*",
            query,
        )
        if restart_request or poweroff_request:
            mode = "restart" if restart_request else "poweroff"
            label = "reiniciar" if mode == "restart" else "apagar"
            return {"message": f"¿Confirmas que quieres {label} FluidOS? Guarda antes tus documentos.", "action": {"type": "power", "target": mode}}
        if "buscar" in query or "archivo" in query or "fichero" in query:
            return {"message": "Para buscar escribe «buscar archivo» y después una palabra del nombre."}
        return {"message": "Todavía no tengo un modelo de lenguaje generativo. Puedo atender órdenes locales seguras. Escribe «ayuda» para ver ejemplos."}

    def resolve_result(self, value: str) -> Path:
        original = Path(value).expanduser()
        if original.is_symlink():
            raise AssistantError("No se abrirán enlaces simbólicos desde los resultados de búsqueda.")
        try:
            candidate = original.resolve(strict=True)
            candidate.relative_to(self.home)
        except (OSError, ValueError) as exc:
            raise AssistantError("El archivo no está disponible dentro de tu carpeta personal.") from exc
        if not candidate.is_file():
            raise AssistantError("El archivo ya no está disponible o no es un archivo normal.")
        if candidate not in self.last_results:
            raise AssistantError("Ese archivo no forma parte de los resultados de esta búsqueda.")
        return candidate
