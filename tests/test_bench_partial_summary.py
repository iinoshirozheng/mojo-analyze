"""Regression: partial benchmark summaries must not imply stale categories were rerun."""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

BENCH_PATH = Path(__file__).resolve().parents[1] / "scripts" / "bench.py"
spec = importlib.util.spec_from_file_location("bench_partial_summary", BENCH_PATH)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class PartialSummaryTests(unittest.TestCase):
    def test_partial_run_preserves_old_data_but_reports_only_measured_category(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "results").mkdir()
            previous = {
                "old": {
                    "category": "historical",
                    "params": {},
                    "variants": {
                        "mojo": {
                            "times": [3.0], "checksum": "old",
                            "mean": 3.0, "median": 3.0, "stdev": 0.0,
                            "min": 3.0, "max": 3.0, "n": 1,
                        },
                        "_checksum_ok": True,
                    },
                }
            }
            path = root / "results" / "results.json"
            path.write_text(json.dumps(previous))
            categories = [{
                "name": "new", "category": "fresh", "params": {},
                "variants": [{"label": "mojo", "cmd": ["synthetic"]}],
            }]
            output = io.StringIO()
            with (
                mock.patch.object(bench, "ROOT", root),
                mock.patch.object(bench, "BENCHMARKS", categories),
                mock.patch.object(bench, "run_variant", return_value=([1.0, 1.2], "new")),
                mock.patch.object(sys, "argv", ["bench.py", "--only", "new", "--trials", "2", "--warmup", "0"]),
                contextlib.redirect_stdout(output),
            ):
                bench.main()
            saved = json.loads(path.read_text())
            self.assertIn("old", saved)
            self.assertIn("new", saved)
            summary = output.getvalue().split("=== Summary (mean seconds, lower is better) ===", 1)[1]
            self.assertIn("\nnew:", summary)
            self.assertNotIn("\nold:", summary)
            self.assertEqual(saved["new"]["variants"]["mojo"]["n"], 2)


if __name__ == "__main__":
    unittest.main()
