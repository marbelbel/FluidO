# Formato de aplicaciones nativas FluidOS (`.fapp`)

**Versión del formato:** `fluidos.app/v1`.

Un `.fapp` es un ZIP UTF-8 compuesto por `manifest.json` y archivos en `payload/`. El manifiesto declara identificador, nombre, versión, editor, punto de entrada opcional, permisos solicitados y hashes SHA-256 de cada archivo.

Ejemplo mínimo:

```json
{
  "schema": "fluidos.app/v1",
  "id": "org.ejemplo.calculadora",
  "name": "Calculadora",
  "version": "1.0.0",
  "publisher": "Equipo Ejemplo",
  "summary": "Calculadora nativa",
  "entrypoint": "bin/calculadora",
  "permissions": [],
  "files": [
    {
      "path": "bin/calculadora",
      "sha256": "SHA256_HEX_DEL_ARCHIVO",
      "mode": "0755"
    }
  ]
}
```

## Reglas de seguridad de la primera versión

- No hay scripts `preinstall`, `postinstall` ni instrucciones ejecutables del instalador.
- No se admiten rutas absolutas, `..`, enlaces simbólicos, ficheros duplicados ni permisos especiales.
- Se comprueban los hashes antes de escribir archivos.
- Se limita el tamaño descomprimido a 512 MiB y el número de archivos a 5.000.
- La instalación se prepara en un directorio temporal y se publica mediante cambio de nombre atómico.
- El borrado solo actúa sobre aplicaciones registradas dentro del directorio administrado.

## Límites importantes

SHA-256 detecta alteraciones del contenido, pero **no demuestra quién publicó el paquete**. La firma digital, la tienda, la actualización diferencial, el aislamiento real de procesos y la aplicación efectiva de permisos por aplicación todavía no están terminados. Los permisos del manifiesto se registran como solicitudes, no se presentan como una barrera de seguridad activa. No se deben instalar paquetes de procedencia desconocida.
