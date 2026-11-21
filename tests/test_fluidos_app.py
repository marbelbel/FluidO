import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "fluidos-app.py"
SPEC = importlib.util.spec_from_file_location("fluidos_app", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class PackageValidationTests(unittest.TestCase):
    def make_package(self, path, payload_path="bin/demo", payload=b"#!/bin/sh\necho hi\n", digest=None, schema="fluidos.app/v1"):
        manifest = {
            "schema": schema, "id": "org.test.demo", "name": "Demo",
            "version": "1.0.0", "publisher": "Test Publisher", "summary": "Test",
            "entrypoint": payload_path, "permissions": [],
            "files": [{"path": payload_path, "sha256": digest or hashlib.sha256(payload).hexdigest(), "mode": "0755"}],
        }
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest))
            zf.writestr("payload/" + payload_path, payload)

    def test_valid_package_passes_hash_check(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo.fapp"
            self.make_package(package)
            manifest, files = module.read_package(package)
            self.assertEqual(manifest["id"], "org.test.demo")
            self.assertIn("bin/demo", files)

    def test_wrong_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "bad.fapp"
            self.make_package(package, digest="0" * 64)
            with self.assertRaises(module.PackageError):
                module.read_package(package)

    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "evil.fapp"
            self.make_package(package, payload_path="../evil")
            with self.assertRaises(module.PackageError):
                module.read_package(package)

    def test_unknown_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "schema.fapp"
            self.make_package(package, schema="unknown")
            with self.assertRaises(module.PackageError):
                module.read_package(package)


if __name__ == "__main__":
    unittest.main()
