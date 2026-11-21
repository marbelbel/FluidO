import importlib.util
import io
import tarfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fluidos_restore", ROOT / "tools/fluidos-restore.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class RestoreValidationTests(unittest.TestCase):
    def make_tar(self, entries):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w:gz") as tf:
            for name, kind in entries:
                info = tarfile.TarInfo(name)
                if kind == "dir":
                    info.type = tarfile.DIRTYPE
                    tf.addfile(info)
                elif kind == "file":
                    data = b"x"
                    info.size = len(data)
                    tf.addfile(info, io.BytesIO(data))
                elif kind == "symlink":
                    info.type = tarfile.SYMTYPE
                    info.linkname = "../../etc/passwd"
                    tf.addfile(info)
        stream.seek(0)
        return tarfile.open(fileobj=stream, mode="r:gz")

    def test_accepts_profile_only(self):
        with self.make_tar([("home", "dir"), ("home/fluid", "dir"), ("home/fluid/hello.txt", "file")]) as tf:
            members = module.validate_members(tf)
            self.assertEqual(len(members), 2)

    def test_rejects_escape_path(self):
        with self.make_tar([("home/fluid", "dir"), ("home/fluid/../../etc/pwned", "file")]) as tf:
            with self.assertRaises(module.RestoreError):
                module.validate_members(tf)

    def test_rejects_symlink(self):
        with self.make_tar([("home/fluid", "dir"), ("home/fluid/link", "symlink")]) as tf:
            with self.assertRaises(module.RestoreError):
                module.validate_members(tf)

    def test_requires_profile_root(self):
        with self.make_tar([("etc/os-release", "file")]) as tf:
            with self.assertRaises(module.RestoreError):
                module.validate_members(tf)

if __name__ == "__main__":
    unittest.main()
