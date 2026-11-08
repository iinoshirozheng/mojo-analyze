# Duplicate benchmark stdout records must fail closed — 2026-11-08

## Question

Does the canonical benchmark harness accept multiple `TIME_SECONDS:` or `CHECKSUM:` records from one child and silently use the last record, allowing an invalid or contradictory output to be published?

## Source inspection and intervention

At baseline `scripts/bench.py`, `parse_output()` iterated over stdout and assigned each matching record into the same variable. No count check existed, so `TIME_SECONDS: 0.25\nTIME_SECONDS: 0.125\nCHECKSUM: 42` returned `(0.125, "42")`, and `CHECKSUM: wrong\nCHECKSUM: 42` returned the last checksum. Cross-variant agreement cannot detect this if the last checksum agrees.

One focused change: raise `RuntimeError` on the second `TIME_SECONDS` or `CHECKSUM` line, even if the values are identical. The existing fail-closed publication path then stops before writing `results/results.json`. Added four subcases (contradictory and identical duplicates for both record types) to `tests/test_bench_checksum_gate.py` using the existing subprocess fixture harness and byte-preservation assertion.

Source change commit: [55c1d937](https://github.com/iinoshirozheng/mojo-analyze/commit/55c1d937e5dacc2a1f34731c91bcbba6cb76d8a7). Test commit: [c2aeb028](https://github.com/iinoshirozheng/mojo-analyze/commit/c2aeb0289effcffd7f20a0af97b29722b22b59f9).

## Verification and limitations

The parser's exact new logic was exercised locally in Python against a duplicated time, a duplicated checksum and a valid single-record control: both duplicates raised the expected `RuntimeError`; the control returned `(0.125, "42")`. This is a **unit-level parser check**, not a full checkout test run. The connected GitHub CI [workflow 42469851789](https://github.com/iinoshirozheng/mojo-analyze/actions/runs/42469851789) was **queued** at the initial check; it must pass before claiming full subprocess/CI verification. The local container could not download GitHub sources due to DNS resolution, so no full-suite result is claimed. No Mojo binaries or new performance measurements were run.

The test asserts rejection occurs before publishing and preserves old result bytes, including in partial/full execution as already covered by the existing harness suite. A future CI failure should be treated as a failed validation, not silently promoted to Verified.

## Conclusion

The baseline protocol was ambiguous and vulnerable to last-record-wins. The change makes exactly-one timing and checksum record a required condition for publication. This is a methodology/correctness hardening change, **not** evidence of any Mojo speedup. No canonical `ANALYSIS.md`, benchmark data or charts were changed.
