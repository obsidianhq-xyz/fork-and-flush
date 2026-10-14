import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("schedule", ROOT / "skills/fork-and-flush/scripts/plan.py")
schedule = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schedule)


class ScheduleTests(unittest.TestCase):
    def test_reference_schedule_accounts_for_all_four_workers(self):
        result = schedule.plan(100)
        self.assertEqual([p["allocation"] for p in result["phases"]], [24, 9, 24, 9, 24, 10])
        self.assertEqual(sum(p["allocation"] for p in result["phases"]), 100)

    def test_feasible_schedules_never_overspend(self):
        for budget in range(17, 250):
            for branches in (1, 2, 3, 4, 5):
                result = schedule.plan(budget, branches)
                self.assertEqual(sum(p["allocation"] for p in result["phases"]), budget)
                self.assertTrue(all(p["allocation"] > 0 for p in result["phases"]))

    def test_rejects_overlapping_rounds_and_bad_inputs(self):
        cases = [(100, 6, "0.06", ["0", "0.33", "0.66"]),
                 (1, 4, "0.06", ["0"]), (0, 4, "0.06", ["0"]),
                 (100, 0, "0.06", ["0"]), (100, 4, "0.06", ["0", "0"]),
                 (100, 4, "0.06", ["0.33"]), (100, 4, "nan", ["0"])]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                schedule.plan(*args)

    def test_two_branch_custom_schedule(self):
        phases = schedule.plan(20, 2, "0.1", ["0", "0.5"])["phases"]
        self.assertEqual([p["allocation"] for p in phases], [4, 6, 4, 6])


class EvaluatorTests(unittest.TestCase):
    def evaluate(self, source):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.py"
            path.write_text(source)
            output = subprocess.check_output([sys.executable, str(ROOT / "examples/bin-packing/evaluate.py"), str(path)], timeout=5)
            return json.loads(output)

    def test_valid_incumbent(self):
        result = self.evaluate((ROOT / "examples/bin-packing/candidate.py").read_text())
        self.assertTrue(result["valid"])
        self.assertEqual(result["score"], 491)

    def test_invalid_candidates_have_no_score(self):
        for source in ["def pack(items, capacity): return []",
                       "def pack(items, capacity): return [items] if items else []",
                       "def pack(items, capacity): raise RuntimeError('failed')"]:
            with self.subTest(source=source):
                result = self.evaluate(source)
                self.assertFalse(result["valid"])
                self.assertIsNone(result["score"])


if __name__ == "__main__":
    unittest.main()
