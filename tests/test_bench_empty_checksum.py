"""Regression tests: empty checksum must not be accepted as agreement.

Run with: python3 -m unittest discover -s tests -p 'test_bench*.py' -v
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

BENCH_PATH = Path(__file__).resolve().parents[1] / "scripts" / "bench.py"
spec = importlib.util.spec_from_file_location("bench_empty_checksum_under_test", BENCH_PATH)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class EmptyChecksumGateTests(unittest.TestCase):
    def test_empty_checksum_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "empty CHECKSUM"):
            bench.parse_output("TIME_SECONDS: 0.1\nCHECKSUM:\n")

    def test_whitespace_checksum_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "empty CHECKSUM"):
            bench.parse_output("TIME_SECONDS: 0.1\nCHECKSUM:   \t \n")

    def test_valid_checksum_remains_accepted(self):
        self.assertEqual(
            bench.parse_output("TIME_SECONDS: 0.1\nCHECKSUM: 0000\n"),
            (0.1, "0000"),
        )

    def test_empty_checksum_prevents_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "results" / "results.json"
            output.parent.mkdir()
            previous = '{"preserve":"yes"}'
            output.write_text(previous)
            fake_benchmarks = [{
                "name": "fixture", "category": "protocol", "params": {},
                "variants": [
                    {"label": "mojo", "cmd": ["fake-mojo"]},
                    {"label": "c", "cmd": ["fake-c"]},
                ],
            }]
            def fake_run(cmd, **kwargs):
                return SimpleNamespace(
                    returncode=0, stderr="",
                    stdout="TIME_SECONDS: 0.1\nCHECKSUM:  \n",
                )
            with patch.object(bench, "ROOT", root), \
                 patch.object(bench, "BENCHMARKS", fake_benchmarks), \
                 patch.object(bench.subprocess, "run", side_effect=fake_run), \
                 patch.object(sys, "argv", ["bench.py", "--trials", "1", "--warmup", "0"]):
                with self.assertRaisesRegex(RuntimeError, "empty CHECKSUM"):
                    bench.main()
            self.assertEqual(output.read_text(), previous)


if __name__ == "__main__":
    unittest.main()
