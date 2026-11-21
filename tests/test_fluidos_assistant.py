import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "fluidos_assistant.py"
spec = importlib.util.spec_from_file_location("fluidos_assistant", MODULE)
assistant = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assistant)


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        (self.home / "Documentos").mkdir()
        (self.home / "Documentos" / "informe-anual.txt").write_text("prueba", encoding="utf-8")
        (self.home / ".oculto").mkdir()
        (self.home / ".oculto" / "secreto.txt").write_text("no indexar", encoding="utf-8")
        self.engine = assistant.AssistantEngine(self.home)

    def tearDown(self):
        self.temp.cleanup()

    def test_search_finds_visible_files_only(self):
        result = self.engine.handle("buscar archivo informe")
        self.assertEqual(len(result["files"]), 1)
        self.assertIn("informe-anual.txt", result["files"][0])

    def test_search_requires_two_characters(self):
        with self.assertRaises(assistant.AssistantError):
            self.engine.search_files("a")

    def test_file_result_must_be_from_recent_search(self):
        found = self.engine.search_files("informe")
        self.assertEqual(self.engine.resolve_result(str(found[0])), found[0])
        outside = self.home.parent / "outside-file.tmp"
        outside.write_text("x", encoding="utf-8")
        try:
            with self.assertRaises((assistant.AssistantError, ValueError)):
                self.engine.resolve_result(str(outside))
        finally:
            outside.unlink(missing_ok=True)

    def test_only_allowlisted_app_actions_are_returned(self):
        result = self.engine.handle("abre navegador")
        self.assertEqual(result["action"], {"type": "app", "target": "navegador"})
        denied = self.engine.handle("ejecuta rm -rf /")
        self.assertNotIn("action", denied)

    def test_unknown_prompts_do_not_become_shell_commands(self):
        result = self.engine.handle("haz algo peligroso")
        self.assertNotIn("action", result)
        self.assertIn("modelo de lenguaje generativo", result["message"])

    def test_power_actions_require_explicit_positive_request(self):
        self.assertEqual(self.engine.handle("reinicia el equipo")["action"], {"type": "power", "target": "restart"})
        self.assertEqual(self.engine.handle("apaga el equipo")["action"], {"type": "power", "target": "poweroff"})
        self.assertNotIn("action", self.engine.handle("no reinicies el equipo"))

    def test_accents_are_normalised_for_app_commands(self):
        self.assertEqual(self.engine.handle("abre ofimática")["action"], {"type": "app", "target": "ofimatica"})

    def test_symlink_results_are_rejected(self):
        outside = self.home.parent / "outside-link-target.tmp"
        outside.write_text("outside", encoding="utf-8")
        link = self.home / "linked.txt"
        try:
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"El sistema no permite crear enlaces simb?licos aqu?: {exc}")
            self.engine.last_results = [outside.resolve()]
            with self.assertRaises(assistant.AssistantError):
                self.engine.resolve_result(str(link))
        finally:
            link.unlink(missing_ok=True)
            outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
