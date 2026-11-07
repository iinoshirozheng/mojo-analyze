"""Fail-closed CLI preflight tests; no Mojo toolchain is required.

Run: python -m unittest discover -s tests -p 'test_bench_cli_counts.py' -v
"""
import importlib.util
from pathlib import Path
from unittest import TestCase, mock
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bench_cli_under_test", ROOT / "scripts" / "bench.py")
BENCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCH)


class BenchmarkCliCountTests(TestCase):
    def test_invalid_counts_abort_before_any_child_or_result_write(self):
        cases = [
            (["--trials", "0"], "--trials must be at least 1"),
            (["--trials", "-1"], "--trials must be at least 1"),
            (["--warmup", "-1"], "--warmup must be nonnegative"),
            (["--trials", "0", "--warmup", "-2"], "--trials must be at least 1"),
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result_file = root / "results" / "results.json"
            result_file.parent.mkdir()
            previous = b'{"prior":"preserve"}\n'
            for args, message in cases:
                with self.subTest(args=args):
                    result_file.write_bytes(previous)
                    with mock.patch.object(sys, "argv", ["bench.py", *args]), \
                         mock.patch.object(BENCH, "ROOT", root), \
                         mock.patch.object(BENCH.subprocess, "run") as child, \
                         mock.patch("sys.stderr") as stderr:
                        with self.assertRaises(SystemExit) as raised:
                            BENCH.main()
                        self.assertEqual(raised.exception.code, 2)
                        self.assertIn(message, "".join(str(c) for c in stderr.write.call_args_list))
                        child.assert_not_called()
                    self.assertEqual(result_file.read_bytes(), previous)


if __name__ == "__main__":
    import unittest
    unittest.main()
