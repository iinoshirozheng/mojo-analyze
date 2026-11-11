"""Regression tests for fail-closed, atomic benchmark result publication."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("benchmark_harness_atomic", ROOT / "scripts" / "bench.py")
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class AtomicPublicationTests(unittest.TestCase):
    def test_replaces_old_snapshot_only_after_complete_serialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.json"
            path.write_text('{"old":true}', encoding="utf-8")
            payload = {"sieve": {"variants": {"mojo": {"times": [0.1], "checksum": "ok"}}}}
            bench.publish_results_atomically(path, payload)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), payload)
            self.assertEqual(sorted(p.name for p in path.parent.iterdir()), ["results.json"])

    def test_replace_failure_preserves_prior_snapshot_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.json"
            prior = '{"validated":true}'
            path.write_text(prior, encoding="utf-8")
            with patch.object(bench.os, "replace", side_effect=OSError("injected replacement failure")):
                with self.assertRaisesRegex(OSError, "injected replacement failure"):
                    bench.publish_results_atomically(path, {"new": True})
            self.assertEqual(path.read_text(encoding="utf-8"), prior)
            self.assertEqual(sorted(p.name for p in path.parent.iterdir()), ["results.json"])

    def test_serialization_failure_preserves_prior_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.json"
            path.write_text('{"validated":true}', encoding="utf-8")
            with self.assertRaises(TypeError):
                bench.publish_results_atomically(path, {"unserializable": object()})
            self.assertEqual(path.read_text(encoding="utf-8"), '{"validated":true}')
            self.assertEqual(sorted(p.name for p in path.parent.iterdir()), ["results.json"])


if __name__ == "__main__":
    unittest.main()
