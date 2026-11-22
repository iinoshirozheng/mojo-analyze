"""Regression tests for portable benchmark TIME_SECONDS wire syntax.

Run: python -m unittest discover -s tests -p 'test_bench_time_protocol.py'
"""
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "bench.py"
spec = importlib.util.spec_from_file_location("mojo_bench_protocol", MODULE_PATH)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class TimingTokenTests(unittest.TestCase):
    def test_standard_decimal_and_exponent(self):
        for token, expected in (("0.25", 0.25), ("1e-3", 0.001),
                                ("+2.5E+1", 25.0), (".5", 0.5)):
            with self.subTest(token=token):
                actual, checksum = bench.parse_output(
                    f"TIME_SECONDS: {token}\nCHECKSUM: abc123\n"
                )
                self.assertEqual(actual, expected)
                self.assertEqual(checksum, "abc123")

    def test_python_only_underscore_syntax_rejected(self):
        for token in ("1_0", "1e1_0", "1_000.5"):
            with self.subTest(token=token):
                with self.assertRaisesRegex(RuntimeError, "invalid TIME_SECONDS"):
                    bench.parse_output(
                        f"TIME_SECONDS: {token}\nCHECKSUM: abc123\n"
                    )

    def test_non_decimal_tokens_rejected(self):
        for token in ("nan", "inf", "0x1p-2", "1.0 trailing", r"1\\x25"):
            with self.subTest(token=token):
                with self.assertRaisesRegex(RuntimeError, "invalid TIME_SECONDS"):
                    bench.parse_output(
                        f"TIME_SECONDS: {token}\nCHECKSUM: abc123\n"
                    )


class StdoutPositionTests(unittest.TestCase):
    """Markers are authoritative only when they terminate stdout."""

    def test_valid_markers_follow_diagnostics(self):
        self.assertEqual(
            bench.parse_output(
                "preparing input\nTIME_SECONDS: 0.25\nCHECKSUM: abc123\n"
            ), (0.25, "abc123")
        )

    def test_trailing_error_does_not_validate_stale_marker_pair(self):
        # Before the positional check this was accepted as a successful run.
        with self.assertRaisesRegex(RuntimeError, "final two"):
            bench.parse_output(
                "TIME_SECONDS: 0.25\nCHECKSUM: abc123\n"
                "ERROR: post-run verification failed\n"
            )

    def test_wrong_order_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "final two"):
            bench.parse_output("CHECKSUM: abc123\nTIME_SECONDS: 0.25\n")

    def test_interleaved_diagnostic_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "final two"):
            bench.parse_output(
                "TIME_SECONDS: 0.25\nlog: later work\nCHECKSUM: abc123\n"
            )

    def test_duplicate_marker_still_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "duplicate TIME_SECONDS"):
            bench.parse_output(
                "TIME_SECONDS: 0.2\nTIME_SECONDS: 0.25\nCHECKSUM: abc123\n"
            )

    def test_no_protocol_markers_still_report_missing(self):
        self.assertEqual(bench.parse_output("not a benchmark\n"), (None, None))


if __name__ == "__main__":
    unittest.main()
