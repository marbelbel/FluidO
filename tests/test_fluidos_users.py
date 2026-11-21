import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fluidos_users", ROOT / "tools/fluidos-users.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class UserValidationTests(unittest.TestCase):
    def test_valid_names(self):
        self.assertEqual(module.validate_username("ana"), "ana")
        self.assertEqual(module.validate_username("user_2"), "user_2")

    def test_rejects_shell_metacharacters(self):
        for name in (";rm", "user name", "../bad", "User", "name;id"):
            with self.subTest(name=name), self.assertRaises(module.UserError):
                module.validate_username(name)

    def test_protected_accounts(self):
        for name in ("root", "toor", "fluid", "daemon"):
            with self.subTest(name=name), self.assertRaises(module.UserError):
                module.validate_username(name)

if __name__ == "__main__":
    unittest.main()
