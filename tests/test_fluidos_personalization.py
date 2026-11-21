import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "fluidos_personalization.py"
spec = importlib.util.spec_from_file_location("fluidos_personalization", MODULE)
personal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(personal)


class PersonalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.settings_path = self.root / "config" / "settings.json"
        self.wayfire = self.root / "wayfire.ini"
        self.wayfire.write_text("[core]\nplugins = alpha animate expo vswitch\nvwidth = 2\nvheight = 2\n\n[expo]\ntoggle = <super> KEY_E\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_defaults_and_atomic_save_roundtrip(self):
        data = personal.load_settings(self.settings_path)
        self.assertEqual(data["schema"], 2)
        personal.save_settings(data, self.settings_path)
        loaded = personal.load_settings(self.settings_path)
        self.assertEqual(loaded["appearance"]["wallpaper"], "ocean")

    def test_migrates_schema_one(self):
        self.settings_path.parent.mkdir(parents=True)
        self.settings_path.write_text(json.dumps({"schema": 1, "appearance": {"theme": "dark", "accent": "#123456"}}), encoding="utf-8")
        data = personal.load_settings(self.settings_path)
        self.assertEqual(data["schema"], 2)
        self.assertEqual(data["appearance"]["theme"], "dark")

    def test_rejects_invalid_color_and_unknown_wallpaper(self):
        data = personal.load_settings(self.settings_path)
        data["appearance"]["accent"] = "red"
        with self.assertRaises(personal.PreferencesError):
            personal.validate_settings(data)
        data = personal.load_settings(self.settings_path)
        data["appearance"]["wallpaper"] = "random-url"
        with self.assertRaises(personal.PreferencesError):
            personal.validate_settings(data)

    def test_applies_virtual_desktop_grid_and_animation_setting(self):
        data = personal.load_settings(self.settings_path)
        data["appearance"]["virtual_desktops"] = "3x2"
        data["appearance"]["animations"] = False
        self.assertTrue(personal.apply_wayfire(data, self.wayfire))
        content = self.wayfire.read_text(encoding="utf-8")
        self.assertIn("vwidth = 3", content)
        self.assertIn("vheight = 2", content)
        self.assertNotIn("animate", content.split("[expo]")[0])
        self.assertIn("toggle = <super> KEY_E", content)

    def test_rejects_non_boolean_animation_setting(self):
        data = personal.load_settings(self.settings_path)
        data["appearance"]["animations"] = "false"
        with self.assertRaises(personal.PreferencesError):
            personal.validate_settings(data)

    def test_missing_wayfire_file_is_not_created(self):
        missing = self.root / "missing.ini"
        self.assertFalse(personal.apply_wayfire(personal.load_settings(self.settings_path), missing))
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
