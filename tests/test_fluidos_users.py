import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace

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

    def test_personal_account_guard(self):
        self.assertTrue(module.is_managed_account(SimpleNamespace(pw_name="ana", pw_uid=1001, pw_dir="/home/ana")))
        self.assertFalse(module.is_managed_account(SimpleNamespace(pw_name="fluid", pw_uid=1000, pw_dir="/home/fluid")))
        self.assertFalse(module.is_managed_account(SimpleNamespace(pw_name="_pkg", pw_uid=999, pw_dir="/nonexistent")))
        self.assertFalse(module.is_managed_account(SimpleNamespace(pw_name="svc", pw_uid=1002, pw_dir="/var/empty")))

if __name__ == "__main__":
    unittest.main()
