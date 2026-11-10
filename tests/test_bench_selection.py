"""Regression tests for fail-closed --only benchmark selection.

Run: python3 -m unittest discover -s tests -p 'test_bench*.py' -v
No Mojo toolchain or benchmark binaries required.
"""
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bench.py"
spec = importlib.util.spec_from_file_location("bench_selection_under_test", SCRIPT)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class SelectionGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "results").mkdir()
        self.result_path = self.root / "results" / "results.json"
        self.sentinel = '{"previous": {"untouched": true}}'
        self.result_path.write_text(self.sentinel)
        self.sample = [{
            "name": "sieve", "category": "test", "params": {},
            "variants": [{"label": "mojo", "cmd": ["fake-mojo"]}],
        }]
        self.root_patch = patch.object(bench, "ROOT", self.root)
        self.bench_patch = patch.object(bench, "BENCHMARKS", self.sample)
        self.root_patch.start()
        self.bench_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.bench_patch.stop)

    def invoke(self, *args):
        with patch.object(sys, "argv", ["bench.py", *args]), \
             patch.object(bench.subprocess, "run") as child, \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            try:
                bench.main()
                code = 0
            except SystemExit as exc:
                code = exc.code
            return code, child.call_count

    def test_unknown_only_rejected_without_child_or_publication(self):
        code, calls = self.invoke("--only", "siev")
        self.assertEqual(code, 2)
        self.assertEqual(calls, 0)
        self.assertEqual(self.result_path.read_text(), self.sentinel)

    def test_mixed_known_and_unknown_rejected_atomically(self):
        code, calls = self.invoke("--only", "sieve,typo")
        self.assertEqual(code, 2)
        self.assertEqual(calls, 0)
        self.assertEqual(self.result_path.read_text(), self.sentinel)

    def test_empty_tokens_rejected(self):
        for selection in ("", ",", "sieve,", ",sieve", "sieve,,sieve"):
            with self.subTest(selection=selection):
                code, calls = self.invoke("--only", selection)
                self.assertEqual(code, 2)
                self.assertEqual(calls, 0)
                self.assertEqual(self.result_path.read_text(), self.sentinel)

    def test_known_selection_still_runs_and_merges(self):
        class Completed:
            returncode = 0
            stdout = "TIME_SECONDS: 0.125\\nCHECKSUM: abc123\\n"
            stderr = ""

        with patch.object(sys, "argv", ["bench.py", "--only", " sieve ", "--trials", "1", "--warmup", "0"]), \
             patch.object(bench.subprocess, "run", return_value=Completed()) as child, \
             redirect_stdout(io.StringIO()):
            bench.main()
        self.assertEqual(child.call_count, 1)
        data = json.loads(self.result_path.read_text())
        self.assertIn("previous", data)
        self.assertTrue(data["sieve"]["variants"]["_checksum_ok"])
        self.assertEqual(data["sieve"]["variants"]["mojo"]["times"], [0.125])


if __name__ == "__main__":
    unittest.main()
