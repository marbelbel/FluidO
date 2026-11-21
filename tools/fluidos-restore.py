#!/usr/local/bin/python3.12
"""Restaura de forma conservadora copias creadas por fluidos-backup."""
from __future__ import annotations
import argparse, hashlib, os, shutil, stat, sys, tarfile, tempfile
from pathlib import Path, PurePosixPath

MAX_TOTAL = 8 * 1024**3
MAX_FILES = 100_000

class RestoreError(Exception): pass

def verify_checksum(archive: Path) -> None:
    sidecar = Path(str(archive) + ".sha256")
    if not archive.is_file() or not sidecar.is_file():
        raise RestoreError("Falta el archivo de copia o su .sha256")
    fields = sidecar.read_text(encoding="ascii").strip().split()
    expected = fields[0].lower() if fields else ""
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise RestoreError("El archivo .sha256 no es válido")
    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""): digest.update(block)
    if digest.hexdigest() != expected:
        raise RestoreError("La copia no supera la comprobación SHA-256")

def validate_members(tf: tarfile.TarFile):
    members = tf.getmembers()
    if len(members) > MAX_FILES: raise RestoreError("Demasiadas entradas en la copia")
    total, seen, accepted = 0, set(), []
    root_seen = False
    for member in members:
        name = member.name
        if name.startswith("/") or "\\" in name or "\x00" in name:
            raise RestoreError(f"Ruta no permitida: {name!r}")
        parts = PurePosixPath(name).parts
        if not parts or any(part in ("", ".", "..") for part in parts):
            raise RestoreError(f"Ruta insegura: {name!r}")
        normalized = PurePosixPath(*parts).as_posix().rstrip("/")
        if normalized in seen: raise RestoreError(f"Entrada duplicada: {normalized}")
        seen.add(normalized)
        is_profile = normalized == "home/fluid" or normalized.startswith("home/fluid/")
        is_container = member.isdir() and normalized in {"home", "etc"}
        is_metadata = normalized in {"etc/fluidos-version", "etc/os-release"}
        if not is_profile and not is_metadata and not is_container:
            raise RestoreError(f"Ruta fuera de home/fluid: {normalized}")
        if not (member.isdir() or member.isfile()):
            raise RestoreError(f"No se permiten enlaces ni archivos especiales: {normalized}")
        if member.isfile():
            total += member.size
            if total > MAX_TOTAL: raise RestoreError("La copia supera 8 GiB")
        if normalized == "home/fluid": root_seen = True
        if is_profile: accepted.append(member)
    if not root_seen: raise RestoreError("La copia no contiene home/fluid")
    return accepted

def restore(archive: Path, confirmation: str) -> None:
    if confirmation != "RESTAURAR PERFIL FLUID":
        raise RestoreError("Falta la confirmación exacta: --confirm 'RESTAURAR PERFIL FLUID'")
    if os.geteuid() != 0: raise RestoreError("Ejecuta la restauración con doas")
    verify_checksum(archive)
    home = Path("/home")
    target = home / "fluid"
    if target.is_symlink(): raise RestoreError("/home/fluid no puede ser un enlace simbólico")
    with tarfile.open(archive, "r:gz") as tf:
        members = validate_members(tf)
        stage = Path(tempfile.mkdtemp(prefix=".fluidos-restore-", dir=str(home)))
        profile = stage / "fluid"
        profile.mkdir(mode=0o700)
        try:
            for member in members:
                rel = PurePosixPath(member.name.rstrip("/"))
                if rel == PurePosixPath("home/fluid"): continue
                output = profile.joinpath(*rel.relative_to("home/fluid").parts)
                if member.isdir():
                    output.mkdir(parents=True, exist_ok=True)
                    os.chmod(output, stat.S_IMODE(member.mode) & 0o755)
                else:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    source = tf.extractfile(member)
                    if source is None: raise RestoreError(f"No se puede leer {member.name}")
                    with source, output.open("xb") as dest:
                        shutil.copyfileobj(source, dest, 1024 * 1024)
                    os.chmod(output, stat.S_IMODE(member.mode) & 0o755)
            old = home / f".fluid-before-restore-{os.getpid()}"
            if old.exists(): raise RestoreError(f"Ya existe {old}; no se sobrescribirá")
            moved = False
            if target.exists(): os.replace(target, old); moved = True
            try:
                os.replace(profile, target)
                shutil.chown(target, user="fluid", group="wheel")
                for current, dirs, files in os.walk(target):
                    for item in dirs + files:
                        shutil.chown(Path(current) / item, user="fluid", group="wheel")
            except Exception:
                if target.exists(): shutil.rmtree(target, ignore_errors=True)
                if moved and old.exists(): os.replace(old, target)
                raise
            if moved: print(f"Perfil anterior conservado en {old}")
        finally: shutil.rmtree(stage, ignore_errors=True)
    print("Perfil restaurado. Cierra sesión y vuelve a entrar.")

def main():
    parser = argparse.ArgumentParser(description="Restaurar una copia de FluidOS")
    parser.add_argument("archive", type=Path)
    parser.add_argument("--confirm", default="", help="Escribe exactamente RESTAURAR PERFIL FLUID")
    args = parser.parse_args()
    try: restore(args.archive, args.confirm)
    except (RestoreError, OSError, tarfile.TarError, UnicodeError, IndexError) as exc:
        print(f"Error: {exc}", file=sys.stderr); return 1
    return 0

if __name__ == "__main__": raise SystemExit(main())
