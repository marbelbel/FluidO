#!/usr/bin/env python3
"""FluidOS native application package manager (.fapp), first secure format draft.

Packages are ZIP files containing manifest.json and payload/<relative-path> files.
Install hooks and executable post-install scripts are deliberately unsupported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

SCHEMA = "fluidos.app/v1"
APP_ID = re.compile(r"^[a-z0-9][a-z0-9.-]{1,62}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")
DEFAULT_ROOT = Path(os.environ.get("FLUIDOS_APP_ROOT", "/usr/local/share/fluidos/apps"))
DEFAULT_DB = Path(os.environ.get("FLUIDOS_APP_DB", "/var/db/fluidos/apps.json"))
MAX_FILES = 5000
MAX_BYTES = 512 * 1024 * 1024
ALLOWED_MODES = {0o644, 0o755}


class PackageError(Exception):
    pass


def safe_relative(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise PackageError(f"Ruta no válida: {value!r}")
    raw_parts = value.split("/")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in raw_parts):
        raise PackageError(f"Ruta insegura: {value!r}")
    if path.parts and ":" in path.parts[0]:
        raise PackageError(f"Ruta no permitida: {value!r}")
    return path


def read_package(package: Path):
    if not package.is_file() or package.suffix.lower() != ".fapp":
        raise PackageError("El archivo debe existir y terminar en .fapp")
    try:
        archive = zipfile.ZipFile(package, "r")
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise PackageError(f"Paquete ZIP ilegible: {exc}") from exc
    with archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        if len(names) != len(set(names)):
            raise PackageError("El paquete contiene nombres de archivo duplicados")
        if len(infos) > MAX_FILES + 1:
            raise PackageError("El paquete supera el máximo de archivos permitido")
        total = sum(item.file_size for item in infos)
        if total > MAX_BYTES:
            raise PackageError("El paquete supera el límite de tamaño de 512 MiB")
        if "manifest.json" not in names:
            raise PackageError("Falta manifest.json")
        for item in infos:
            name = item.filename
            directory_name = name[:-1] if item.is_dir() and name.endswith("/") else name
            if item.is_dir():
                if directory_name != "payload" and not directory_name.startswith("payload/"):
                    raise PackageError(f"Directorio fuera de payload/: {name}")
                if directory_name != "payload":
                    safe_relative(directory_name[len("payload/"):])
                continue
            if directory_name != "manifest.json":
                if not directory_name.startswith("payload/"):
                    raise PackageError(f"Archivo fuera de payload/: {name}")
                safe_relative(directory_name[len("payload/"):])
            mode = (item.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise PackageError(f"No se permiten enlaces simbólicos: {name}")
        try:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PackageError(f"manifest.json no es JSON UTF-8 válido: {exc}") from exc
        validate_manifest(manifest)
        expected = {}
        for entry in manifest["files"]:
            rel = safe_relative(entry["path"]).as_posix()
            if rel == "manifest.json":
                raise PackageError("manifest.json está reservado y no puede ser un archivo de payload")
            if rel in expected:
                raise PackageError(f"Archivo duplicado en el manifiesto: {rel}")
            digest = entry.get("sha256", "")
            if not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
                raise PackageError(f"SHA-256 no válido para {rel}")
            mode = entry.get("mode", 0o644)
            if isinstance(mode, str):
                try:
                    mode = int(mode, 8)
                except ValueError as exc:
                    raise PackageError(f"Permisos no válidos para {rel}") from exc
            if mode not in ALLOWED_MODES:
                raise PackageError(f"Solo se permiten permisos 0644 o 0755: {rel}")
            expected[rel] = (digest.lower(), mode)
        paths = sorted(expected)
        for index, path in enumerate(paths):
            if any(other.startswith(path + "/") for other in paths[index + 1:]):
                raise PackageError(f"Una ruta de archivo también se utiliza como carpeta: {path}")
        if manifest.get("entrypoint") and expected.get(manifest["entrypoint"], (None, None))[1] != 0o755:
            raise PackageError("entrypoint debe tener permisos 0755")
        payload_names = {
            n[len("payload/"):] for n in names
            if n.startswith("payload/") and not n.endswith("/")
        }
        if payload_names != set(expected):
            raise PackageError("Los archivos de payload no coinciden con manifest.json")
        contents = {}
        for rel, (digest, mode) in expected.items():
            data = archive.read("payload/" + rel)
            if hashlib.sha256(data).hexdigest() != digest:
                raise PackageError(f"Hash SHA-256 incorrecto: {rel}")
            contents[rel] = (data, mode)
        if manifest.get("entrypoint") and manifest["entrypoint"] not in expected:
            raise PackageError("El punto de entrada no está incluido en files")
        return manifest, contents


def validate_manifest(data):
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise PackageError(f"El esquema debe ser {SCHEMA}")
    app_id = data.get("id")
    if not isinstance(app_id, str) or not APP_ID.fullmatch(app_id):
        raise PackageError("id debe usar letras minúsculas, números, punto o guion")
    if not isinstance(data.get("name"), str) or not data["name"].strip() or len(data["name"]) > 80:
        raise PackageError("name debe tener entre 1 y 80 caracteres")
    if not isinstance(data.get("version"), str) or not VERSION.fullmatch(data["version"]):
        raise PackageError("version debe tener formato X.Y.Z")
    if not isinstance(data.get("publisher"), str) or not data["publisher"].strip():
        raise PackageError("publisher es obligatorio")
    if not isinstance(data.get("files"), list) or not data["files"]:
        raise PackageError("files debe contener al menos un archivo")
    if any(not isinstance(item, dict) or not isinstance(item.get("path"), str) for item in data["files"]):
        raise PackageError("Cada elemento de files debe ser un objeto con path")
    entrypoint = data.get("entrypoint", "")
    if entrypoint:
        safe_relative(entrypoint)
    permissions = data.get("permissions", [])
    allowed = {"network", "camera", "microphone", "location", "user-files"}
    if not isinstance(permissions, list) or any(p not in allowed for p in permissions):
        raise PackageError("permissions contiene un permiso no reconocido")


def load_db(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema": 1, "apps": {}}
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageError(f"No se puede leer la base de aplicaciones: {exc}") from exc
    if data.get("schema") != 1 or not isinstance(data.get("apps"), dict):
        raise PackageError("La base de aplicaciones está dañada o usa otro esquema")
    return data


def save_db(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".apps-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def require_root():
    if os.geteuid() != 0:
        raise PackageError("Para instalar o eliminar aplicaciones usa doas con permisos de administrador")


def install_package(package: Path, root: Path, db_path: Path):
    require_root()
    manifest, contents = read_package(package)
    app_id = manifest["id"]
    root.mkdir(parents=True, exist_ok=True)
    root_resolved = root.resolve()
    destination = root_resolved / app_id
    if destination.exists():
        raise PackageError(f"La aplicación {app_id} ya está instalada; no se sobrescribirá")
    stage = Path(tempfile.mkdtemp(prefix=f".{app_id}-", dir=str(root_resolved)))
    try:
        for rel, (data, mode) in contents.items():
            target = stage.joinpath(*safe_relative(rel).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(data)
            os.chmod(target, mode)
        (stage / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(stage, destination)
        db = load_db(db_path)
        db["apps"][app_id] = {
            "name": manifest["name"], "version": manifest["version"],
            "publisher": manifest["publisher"], "path": str(destination),
            "entrypoint": manifest.get("entrypoint", ""),
            "requested_permissions": manifest.get("permissions", []),
        }
        try:
            save_db(db_path, db)
        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
    print(f"Instalada: {manifest['name']} {manifest['version']} ({app_id})")
    print("Aviso: el aislamiento y la aplicación efectiva de permisos por aplicación aún no están implementados.")


def list_apps(db_path: Path):
    db = load_db(db_path)
    if not db["apps"]:
        print("No hay aplicaciones .fapp instaladas.")
        return
    for app_id, item in sorted(db["apps"].items()):
        print(f"{app_id:24} {item['version']:12} {item['name']}")


def remove_app(app_id: str, root: Path, db_path: Path):
    require_root()
    if not APP_ID.fullmatch(app_id):
        raise PackageError("Identificador de aplicación no válido")
    db = load_db(db_path)
    item = db["apps"].get(app_id)
    if not item:
        raise PackageError(f"No está instalada: {app_id}")
    root_resolved = root.resolve()
    destination = Path(item.get("path", "")).resolve()
    if destination.parent != root_resolved or destination.name != app_id:
        raise PackageError("La ruta registrada no está dentro de la carpeta protegida de aplicaciones")
    if destination.exists():
        shutil.rmtree(destination)
    del db["apps"][app_id]
    save_db(db_path, db)
    print(f"Eliminada: {app_id}")


def main():
    parser = argparse.ArgumentParser(description="Gestor de aplicaciones nativas FluidOS (.fapp)")
    sub = parser.add_subparsers(dest="action", required=True)
    check = sub.add_parser("verify", help="Verifica estructura y hashes sin instalar")
    check.add_argument("package", type=Path)
    install = sub.add_parser("install", help="Instala un paquete validado")
    install.add_argument("package", type=Path)
    remove = sub.add_parser("remove", help="Elimina una aplicación gestionada")
    remove.add_argument("app_id")
    sub.add_parser("list", help="Muestra aplicaciones instaladas")
    args = parser.parse_args()
    try:
        if args.action == "verify":
            manifest, files = read_package(args.package)
            print(f"Paquete válido: {manifest['name']} {manifest['version']} ({manifest['id']})")
            print(f"Archivos comprobados: {len(files)}")
            print("La verificación comprueba integridad, no la identidad del editor ni una firma digital.")
        elif args.action == "install":
            install_package(args.package, DEFAULT_ROOT, DEFAULT_DB)
        elif args.action == "remove":
            remove_app(args.app_id, DEFAULT_ROOT, DEFAULT_DB)
        else:
            list_apps(DEFAULT_DB)
    except PackageError as exc:
        print(f"FluidOS App: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
