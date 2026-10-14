import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("worker", Path(__file__).with_name("codex_worker.py"))
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


@unittest.skipUnless(os.name == "posix", "the opt-in Codex supervisor uses POSIX process groups")
class SupervisorTests(unittest.TestCase):
    def invoke_fake(self, root, body, timeout):
        binary = root / "bin"
        binary.mkdir()
        fake = binary / "codex"
        fake.write_text(f"#!{sys.executable}\n" + body)
        fake.chmod(0o755)
        workspace = root / "workspace"
        workspace.mkdir()
        with patch.dict(os.environ, {"PATH": str(binary) + os.pathsep + os.environ.get("PATH", "")}):
            return worker.run(workspace, root / "logs", "test input", timeout)

    def test_captures_completed_session_and_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.invoke_fake(Path(directory),
                'import sys, json\nassert sys.stdin.read() == "test input"\n'
                'print(json.dumps({"type":"thread.started", "thread_id":"fresh-test"}))\n'
                'print(json.dumps({"type":"turn.completed", "usage":{"input_tokens":5}}))\n', 2)
            self.assertFalse(result["timed_out"])
            self.assertEqual(result["returncode"], 0)
            self.assertTrue(result["turn_completed"])
            self.assertEqual(result["session_ids"], ["fresh-test"])
            self.assertEqual(result["usage"], [{"input_tokens": 5}])

    def test_timeout_stops_descendant_which_ignores_term(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.invoke_fake(root,
                'import os, signal, time\nfrom pathlib import Path\n'
                'if os.fork() == 0:\n'
                ' signal.signal(signal.SIGTERM, signal.SIG_IGN)\n'
                ' time.sleep(0.8)\n'
                ' Path("escaped-write").write_text("should not happen")\n'
                ' os._exit(0)\n'
                'time.sleep(10)\n', 0.2)
            self.assertTrue(result["timed_out"])
            self.assertFalse(result["turn_completed"])
            time.sleep(0.9)
            self.assertFalse((root / "workspace/escaped-write").exists())
            self.assertTrue((root / "logs/run.json").is_file())


if __name__ == "__main__":
    unittest.main()
