import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


packager = load("packager", ROOT / "scripts/package_plugins.py")
acceptance = load("claude_acceptance", ROOT / "tests/claude_acceptance.py")


class PluginTests(unittest.TestCase):
    def test_both_archives_preserve_one_skill_and_are_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            first = packager.build(output)
            self.assertEqual(first, packager.build(output))
            contents = {}
            for target, package in first["packages"].items():
                with zipfile.ZipFile(output / package["file"]) as archive:
                    contents[target] = {n: archive.read(n) for n in archive.namelist()}
            core = {p.relative_to(ROOT).as_posix(): p.read_bytes()
                    for p in (ROOT / "skills").rglob("*") if p.is_file()
                    and "__pycache__" not in p.parts}
            for files in contents.values():
                self.assertEqual({n: b for n, b in files.items() if n.startswith("skills/")}, core)
                self.assertIn("LICENSE", files)
                self.assertIn("NOTICE.md", files)
            self.assertIn("plugin.json", contents["openai"])
            self.assertNotIn(".claude-plugin/plugin.json", contents["openai"])
            self.assertIn(".claude-plugin/plugin.json", contents["claude"])
            self.assertNotIn("plugin.json", contents["claude"])

    def test_worker_failure_cannot_pass_or_trigger_continuation(self):
        # Claude can label an authentication error subtype=success, is_error=true.
        failures = [
            {"is_error": True, "returncode": 1, "result_subtype": "success", "permission_denials": []},
            {"is_error": False, "returncode": 0, "result_subtype": "success", "permission_denials": ["Write"]},
        ]
        for failure in failures:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                package = packager.build(root / "packages")["packages"]["claude"]["file"]
                with patch.object(acceptance, "run", return_value=failure) as worker:
                    with self.assertRaisesRegex(RuntimeError, "Fresh worker failure"):
                        acceptance.main(root / "run", root / "packages" / package)
                self.assertEqual(worker.call_count, 2)
                outcome = json.loads((root / "run/outcome.json").read_text())
                self.assertEqual(outcome["status"], "incomplete")
                self.assertFalse((root / "run/decision-result.json").exists())
