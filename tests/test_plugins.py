import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/fork-and-flush"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


packager = load("packager", ROOT / "scripts/package_plugins.py")
acceptance = load("claude_acceptance", ROOT / "tests/claude_acceptance.py")
grok = load("grok_acceptance", ROOT / "tests/grok_acceptance.py")


class PluginTests(unittest.TestCase):
    def test_catalog_build_keeps_two_plugins_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "catalog"
            (root / "plugins").mkdir(parents=True)
            (root / ".claude-plugin").mkdir()
            for name in ("fork-and-flush", "second-skill"):
                plugin = root / "plugins" / name
                shutil.copytree(PLUGIN, plugin)
                if name != "fork-and-flush":
                    (plugin / "skills/fork-and-flush").rename(plugin / "skills" / name)
                    skill = plugin / "skills" / name / "SKILL.md"
                    skill.write_text(skill.read_text().replace("name: fork-and-flush", f"name: {name}"))
                for relative in ("plugin.json", ".claude-plugin/plugin.json"):
                    path = plugin / relative
                    metadata = json.loads(path.read_text())
                    metadata["name"] = name
                    path.write_text(json.dumps(metadata))
            for name in ("LICENSE", "PRIVACY.md", "SUPPORT.md"):
                shutil.copyfile(ROOT / name, root / name)
            catalog = {"plugins": [{"name": name, "source": f"./plugins/{name}"}
                                   for name in ("fork-and-flush", "second-skill")]}
            (root / ".claude-plugin/marketplace.json").write_text(json.dumps(catalog))
            output = Path(directory) / "packages"
            report = packager.build_catalog(output, root=root)
            self.assertEqual(set(report["plugins"]), {"fork-and-flush", "second-skill"})
            for name, plugin in report["plugins"].items():
                for package in plugin["packages"].values():
                    with zipfile.ZipFile(output / package["file"]) as archive:
                        skills = [n for n in archive.namelist() if n.endswith("/SKILL.md")]
                        self.assertEqual(skills, [f"skills/{name}/SKILL.md"])
                        self.assertIn("README.md", archive.namelist())
            selected = Path(directory) / "selected"
            report = packager.build_catalog(selected, ["second-skill"], root)
            self.assertEqual(set(report["plugins"]), {"second-skill"})
            self.assertFalse(list(selected.glob("fork-and-flush-*.zip")))

    def test_both_archives_preserve_one_skill_and_are_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            first = packager.build(output)
            self.assertEqual(first, packager.build(output))
            contents = {}
            for target, package in first["packages"].items():
                with zipfile.ZipFile(output / package["file"]) as archive:
                    contents[target] = {n: archive.read(n) for n in archive.namelist()}
            core = {p.relative_to(PLUGIN).as_posix(): p.read_bytes()
                    for p in (PLUGIN / "skills").rglob("*") if p.is_file()
                    and "__pycache__" not in p.parts}
            for files in contents.values():
                self.assertEqual({n: b for n, b in files.items() if n.startswith("skills/")}, core)
                self.assertIn("LICENSE", files)
                self.assertIn("NOTICE.md", files)
            self.assertIn("plugin.json", contents["openai"])
            self.assertNotIn(".claude-plugin/plugin.json", contents["openai"])
            self.assertIn(".claude-plugin/plugin.json", contents["claude"])
            self.assertNotIn("plugin.json", contents["claude"])
            interface = json.loads(contents["openai"]["plugin.json"])["extensions"]["com.openai"]["interface"]
            for field in ("logo", "composerIcon"):
                path = interface[field].removeprefix("./")
                self.assertEqual(contents["openai"][path], (PLUGIN / path).read_bytes())
            for files in contents.values():
                for name in ("PRIVACY.md", "SUPPORT.md"):
                    self.assertEqual(files[name], (ROOT / name).read_bytes())

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

    def test_grok_resume_requires_valid_completed_session(self):
        valid = {"valid": True}
        good = {"session_id": "worker-a", "returncode": 0, "is_error": False,
                "result_subtype": "end_turn", "permission_denials": []}
        self.assertTrue(grok.resumable(good, valid))
        for change in ({"session_id": None}, {"returncode": -9}, {"is_error": True},
                       {"result_subtype": "max_turns"}, {"permission_denials": ["Edit"]}):
            self.assertFalse(grok.resumable(good | change, valid))
        self.assertFalse(grok.resumable(good, {"valid": False}))
