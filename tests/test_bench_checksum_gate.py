"""Subprocess contract tests; no Mojo toolchain or benchmark corpus is needed.

Run: python -m unittest discover -s tests -p 'test_bench_checksum_gate.py' -v
Set MOJO_ANALYZE_BENCH_FILE to test an older harness with these same fixtures.
The emitted times are protocol fixtures, not performance measurements.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HARNESS = Path(os.environ.get(
    "MOJO_ANALYZE_BENCH_FILE",
    str(Path(__file__).resolve().parents[1] / "scripts" / "bench.py"),
)).resolve()

RUNNER = """
import importlib.util
import json
from pathlib import Path
import sys
spec = importlib.util.spec_from_file_location("bench_under_test", sys.argv[1])
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)
bench.ROOT = Path(sys.argv[2])
bench.BENCHMARKS = json.loads((bench.ROOT / "fixtures.json").read_text())
sys.argv = [str(spec.origin)] + sys.argv[3:]
bench.main()
"""


def variant(label, checksum="42", code=None):
    if code is None:
        code = f"print('TIME_SECONDS: 0.125'); print('CHECKSUM: ' + {checksum!r})"
    return {"label": label, "cmd": [sys.executable, "-S", "-c", code]}


def benchmark(name="fixture", checksums=("42", "42"), variants=None):
    return {
        "name": name,
        "category": "test-only protocol fixture",
        "params": {"fixture": True},
        "variants": variants if variants is not None else [
            variant(f"implementation-{i}", checksum)
            for i, checksum in enumerate(checksums)
        ],
    }


# A valid old category must survive a failed run byte-for-byte, and a successful
# partial run must preserve its decoded contents. Formatting is intentional.
OLD = b'{\n "old": {"category":"old fixture","params":{},"variants":{"_checksum_ok":true,"reference":{"times":[0.25],"checksum":"9","mean":0.25,"median":0.25,"stdev":0.0,"min":0.25,"max":0.25,"n":1}}}\n}\n'


class ChecksumPublicationGateTests(unittest.TestCase):
    def run_case(self, fixtures, *, only=None, existing=OLD):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "results" / "results.json"
            if existing is not None:
                output.parent.mkdir()
                output.write_bytes(existing)
            (root / "fixtures.json").write_text(json.dumps(fixtures))
            command = [sys.executable, "-S", "-c", RUNNER, str(HARNESS), str(root),
                       "--trials", "2", "--warmup", "1"]
            if only is not None:
                command += ["--only", only]
            result = subprocess.run(command, capture_output=True, text=True,
                                    timeout=30, check=False)
            return result, output.read_bytes() if output.exists() else None

    def assert_rejected(self, result, output, expected=OLD):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(output, expected)
        self.assertNotIn("=== Summary", result.stdout)
        self.assertNotIn("mean=", result.stdout)
        self.assertNotIn("Wrote ", result.stdout)

    def test_full_mismatch_preserves_previous_bytes(self):
        result, output = self.run_case([benchmark(checksums=("42", "43"))])
        self.assert_rejected(result, output)
        self.assertIn("CHECKSUM MISMATCH", result.stderr)
        self.assertIn("fixture", result.stderr)
        self.assertIn("implementation-1", result.stderr)

    def test_partial_mismatch_preserves_previous_bytes(self):
        result, output = self.run_case([benchmark(checksums=("42", "43"))],
                                       only="fixture")
        self.assert_rejected(result, output)

    def test_mismatch_does_not_create_result_file(self):
        result, output = self.run_case([benchmark(checksums=("42", "43"))],
                                       existing=None)
        self.assert_rejected(result, output, expected=None)

    def test_later_mismatch_does_not_publish_earlier_valid_category(self):
        result, output = self.run_case([
            benchmark(name="good"),
            benchmark(name="bad", checksums=("42", "43")),
        ])
        self.assert_rejected(result, output)

    def test_full_success_replaces_old_snapshot(self):
        result, output = self.run_case([benchmark()])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(output)
        self.assertEqual(set(data), {"fixture"})
        self.assertTrue(data["fixture"]["variants"]["_checksum_ok"])
        record = data["fixture"]["variants"]["implementation-0"]
        self.assertEqual(record["times"], [0.125, 0.125])
        self.assertEqual(record["checksum"], "42")
        self.assertEqual(record["n"], 2)
        self.assertEqual(record["mean"], 0.125)
        self.assertIn("=== Summary", result.stdout)

    def test_partial_success_preserves_unselected_category(self):
        result, output = self.run_case([benchmark(), benchmark(name="unselected")],
                                       only="fixture")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(output)
        self.assertEqual(set(data), {"old", "fixture"})
        self.assertEqual(data["old"], json.loads(OLD)["old"])
        self.assertTrue(data["fixture"]["variants"]["_checksum_ok"])

    def test_warmup_checksum_disagreement_is_rejected(self):
        code = (
            "from pathlib import Path; p=Path('counter'); "
            "n=int(p.read_text()) if p.exists() else 0; "
            "p.write_text(str(n+1)); print('TIME_SECONDS: 0.125'); "
            "print('CHECKSUM: ' + ('wrong-warmup' if n == 0 else '42'))"
        )
        result, output = self.run_case([
            benchmark(variants=[variant("varying", code=code)]),
        ])
        self.assert_rejected(result, output)
        self.assertIn("non-deterministic checksum", result.stderr)

    def test_missing_checksum_is_rejected(self):
        result, output = self.run_case([
            benchmark(variants=[variant("missing", code="print('TIME_SECONDS: 0.125')")]),
        ])
        self.assert_rejected(result, output)
        self.assertIn("missing TIME_SECONDS/CHECKSUM", result.stderr)

    def test_child_failure_is_rejected(self):
        result, output = self.run_case([
            benchmark(variants=[variant("failed", code="raise SystemExit(7)")]),
        ])
        self.assert_rejected(result, output)
        self.assertIn("command failed (7)", result.stderr)


    def test_nonfinite_time_rejected_before_publication(self):
        for value in ("NaN", "Infinity", "-Infinity", "1e309", "-1e309"):
            with self.subTest(time=value):
                code = f"print('TIME_SECONDS: {value}'); print('CHECKSUM: 42')"
                bad = variant("bad-time", code=code)
                result, output = self.run_case([
                    benchmark(variants=[variant("good"), bad]),
                ])
                self.assert_rejected(result, output)
                self.assertIn("invalid TIME_SECONDS", result.stderr)

    def test_nonpositive_time_rejected_before_publication(self):
        for value in ("0", "-0.0", "-0.125"):
            with self.subTest(time=value):
                code = f"print('TIME_SECONDS: {value}'); print('CHECKSUM: 42')"
                result, output = self.run_case([
                    benchmark(variants=[variant("bad-time", code=code)]),
                ])
                self.assert_rejected(result, output)
                self.assertIn("invalid TIME_SECONDS", result.stderr)

    def test_bad_time_in_warmup_is_rejected(self):
        code = (
            "from pathlib import Path; p=Path('time_counter'); "
            "n=int(p.read_text()) if p.exists() else 0; "
            "p.write_text(str(n+1)); "
            "print('TIME_SECONDS: ' + ('NaN' if n == 0 else '0.125')); "
            "print('CHECKSUM: 42')"
        )
        result, output = self.run_case([
            benchmark(variants=[variant("warmup-invalid", code=code)]),
        ])
        self.assert_rejected(result, output)
        self.assertIn("invalid TIME_SECONDS", result.stderr)

    def test_bad_time_after_valid_category_does_not_publish_any(self):
        code = "print('TIME_SECONDS: inf'); print('CHECKSUM: 42')"
        result, output = self.run_case([
            benchmark(name="good-category"),
            benchmark(name="bad-category", variants=[variant("bad-time", code=code)]),
        ])
        self.assert_rejected(result, output)
        self.assertIn("invalid TIME_SECONDS", result.stderr)

    def test_bad_time_without_old_file_does_not_create_one(self):
        code = "print('TIME_SECONDS: nan'); print('CHECKSUM: 42')"
        result, output = self.run_case([
            benchmark(variants=[variant("bad-time", code=code)]),
        ], existing=None)
        self.assert_rejected(result, output, expected=None)

    def test_small_positive_duration_still_publishes(self):
        code = "print('TIME_SECONDS: 1e-9'); print('CHECKSUM: 42')"
        result, output = self.run_case([
            benchmark(variants=[variant("tiny-but-valid", code=code)]),
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(output, parse_constant=lambda token: self.fail(token))
        row = data["fixture"]["variants"]["tiny-but-valid"]
        self.assertEqual(row["times"], [1e-9, 1e-9])
        self.assertEqual(row["mean"], 1e-9)
        self.assertTrue(data["fixture"]["variants"]["_checksum_ok"])

if __name__ == "__main__":
    unittest.main()
