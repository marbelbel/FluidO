#!/usr/local/bin/python3.12
"""Gestión básica de cuentas locales FreeBSD; usuarios nuevos no son admins."""
from __future__ import annotations
import argparse, importlib, os, re, subprocess, sys

USERNAME = re.compile(r"^[a-z_][a-z0-9_-]{0,15}$")
PROTECTED = {"root", "toor", "fluid", "daemon", "operator", "bin", "nobody"}
class UserError(Exception): pass

def get_pwd_module():
    try:
        return importlib.import_module("pwd")
    except ImportError as exc:
        raise UserError("La gestión de cuentas locales solo funciona en FreeBSD/Unix.") from exc

def is_managed_account(user):
    home = getattr(user, "pw_dir", "")
    return (user.pw_uid >= 1000 and user.pw_name not in PROTECTED
            and (home.startswith("/home/") or home.startswith("/usr/home/")))

def validate_username(name: str) -> str:
    if not USERNAME.fullmatch(name):
        raise UserError("Usa 1-16 caracteres: minúsculas, números, _ o -; empieza por letra o _.")
    if name in PROTECTED: raise UserError("Esa cuenta está protegida.")
    return name

def require_root():
    if not hasattr(os, "geteuid"):
        raise UserError("La gestión de cuentas locales solo funciona en FreeBSD/Unix.")
    if os.geteuid() != 0: raise UserError("Usa doas para cambiar cuentas: doas fluidos-users add USUARIO")

def run_pw(args):
    result = subprocess.run(["pw", *args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    if result.returncode: raise UserError(result.stdout.strip() or "El comando pw falló")

def add_user(name):
    require_root(); validate_username(name)
    pwd = get_pwd_module()
    try: pwd.getpwnam(name)
    except KeyError: pass
    else: raise UserError("Ese usuario ya existe")
    run_pw(["useradd", name, "-m", "-s", "/bin/sh", "-c", "Usuario de FluidOS"])
    result = subprocess.run(["pw", "passwd", name], check=False)
    if result.returncode:
        subprocess.run(["pw", "userdel", name, "-r"], check=False)
        raise UserError("No se pudo establecer la contraseña; se eliminó la cuenta incompleta")
    print(f"Usuario creado: {name}. No tiene permisos de administrador.")

def remove_user(name, confirmation):
    require_root(); validate_username(name)
    if confirmation != f"ELIMINAR USUARIO {name}":
        raise UserError(f"Confirma con --confirm 'ELIMINAR USUARIO {name}'")
    pwd = get_pwd_module()
    try: account = pwd.getpwnam(name)
    except KeyError as exc: raise UserError("Ese usuario no existe") from exc
    if not is_managed_account(account):
        raise UserError("Solo se pueden eliminar usuarios personales administrables de /home.")
    run_pw(["userdel", name, "-r"])
    print(f"Usuario eliminado: {name}")

def list_users():
    pwd = get_pwd_module()
    for user in sorted(pwd.getpwall(), key=lambda item: item.pw_name):
        if is_managed_account(user):
            print(f"{user.pw_name:16} UID {user.pw_uid:5}  {user.pw_dir}")

def main():
    parser = argparse.ArgumentParser(description="Cuentas locales de FluidOS")
    sub = parser.add_subparsers(dest="action", required=True)
    add = sub.add_parser("add"); add.add_argument("username")
    remove = sub.add_parser("remove"); remove.add_argument("username"); remove.add_argument("--confirm", default="")
    sub.add_parser("list")
    args = parser.parse_args()
    try:
        if args.action == "add": add_user(args.username)
        elif args.action == "remove": remove_user(args.username, args.confirm)
        else: list_users()
    except (UserError, OSError) as exc:
        print(f"fluidos-users: {exc}", file=sys.stderr); return 2
    return 0

if __name__ == "__main__": raise SystemExit(main())
