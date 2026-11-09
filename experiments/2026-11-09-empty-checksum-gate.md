# 2026-11-09 — Empty-checksum publication gate

## Question

Can all language variants emit `CHECKSUM:` with no value and still pass the cross-variant agreement gate, causing benchmark timings to be published?

## Pre-change reproduction / mechanism

In `scripts/bench.py`, `parse_output` previously set `checksum = line.split(":", 1)[1].strip()`. A line `CHECKSUM:  ` therefore yielded the empty string `""`, not `None`. `run_variant` checked `if t is None or c is None`, so the empty string was accepted. If all variants emitted the same empty string, `set(bench_checksums.values())` had cardinality one and the publication gate would accept it. This is a deterministic protocol issue, not a measured Mojo performance difference.

## Intervention

Reject an empty/whitespace-only `CHECKSUM` immediately in `parse_output`, before recording timings or publishing results. Add `tests/test_bench_empty_checksum.py` to the existing `python3 -m unittest discover -s tests -p 'test_bench*.py' -v` CI test discovery. Fixtures cover blank and whitespace-only checksums, a valid `0000` checksum, and preservation of an existing `results/results.json` on failure.

## Verification boundary

The source-level failure path was independently inspected before and after the change; the test fixtures exercise the actual `scripts/bench.py` module through importlib and mocks. **CI completion and a full native Mojo benchmark have not yet been independently confirmed at the time of writing.** Do not call this a measured speedup or an independently verified native benchmark result. Confirm Linux x86_64 and arm64 CI test-step success before marking cross-platform verification complete.

## Conclusion

A correctness gate must validate **non-empty semantic evidence**, not merely the presence of a marker and equality of possibly empty strings. Preserve prior published results on invalid protocol output. This complements, but does not duplicate, the existing checksum-mismatch, nonfinite-time, and duplicate-marker checks.

## Provenance

- [Harness](https://github.com/iinoshirozheng/mojo-analyze/blob/main/scripts/bench.py)
- [Regression fixtures](https://github.com/iinoshirozheng/mojo-analyze/blob/main/tests/test_bench_empty_checksum.py)
- Code commit: `d9ca5fc956427b55d2f1ae97bca1c630e9961644`
- Test commit: `7af46a5750e110e65f417fa759d94659e289ea69`
- Observed: 2026-11-09 Asia/Taipei.
