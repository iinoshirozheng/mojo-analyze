# Finite positive `TIME_SECONDS` as a benchmark publication prerequisite

**Observed:** 2026-11-06 (Asia/Taipei). **Scope:** exactly one benchmark-methodology investigation. **No native performance/codegen comparisons were made.**

## Question

After the November 5 cross-variant checksum publication fix, can a benchmark whose variants *agree on their checksums* still publish an invalid performance result because a child prints `NaN`, `Infinity`, zero or negative elapsed time?

The harness's stdout protocol is an input boundary, not a trusted numeric type. The canonical `ANALYSIS.md` correctness claim should hold for the timing values as well as result checksums.

## Baseline and isolated failure mechanism

- Starting `main`: `e023f14993f89b1681aeee89acf6d3267f2fbfd6`.
- Pre-change harness blob: `904e1c19d8bd31fbccb90f0bca3fbc00cc2874d8`, `scripts/bench.py`.
- `parse_output()` used Python `float()`, which accepts `NaN`, `Infinity`, `-Infinity` and `1e309` (overflowing to positive infinity). The harness previously checked only presence and checksum equality, then computed statistics and wrote default `json.dumps` output.
- A small independent Python standard-library probe confirmed that `json.dumps({"time": float("NaN")})` emits a nonstandard `NaN` token by default; negative and zero durations are also accepted by `float()`.

These establish a *source-level invalid-publication path*, not a claim that any real benchmark has emitted these values.

## Single focused intervention

After required fields are parsed and before adding a checksum or recorded sample, `run_variant()` now demands `math.isfinite(t) and t > 0`. Invalid values raise a contextual `RuntimeError`; the existing staged-in-memory result path then leaves an older `results.json` unchanged and does not create one when absent. Warmups are subject to the same contract as measured trials.

No benchmark implementation, corpus, checksum algorithm, statistics formula, chart, or canonical measured result is changed. Existing `test_bench_checksum_gate.py` now includes timing-validity fault injection, reusing its real subprocess and temporary-result-file fixtures.

## Verification

**Actual run:** [GitHub Actions benchmark run 42201180145](https://github.com/iinoshirozheng/mojo-analyze/actions/runs/42201180145) for commit `23b2a21f29cafde8995138d3d7a2dc2d1ccc0aca`. The `Test checksum publication gate` step **completed successfully on both Linux x86_64 and Linux arm64** jobs, before toolchain/build steps. The standard-library test suite contains **15 tests**: nine earlier checksum/exit/publication cases and six added timing contract tests.

New fault-injection cases:
1. `NaN`, `Infinity`, `-Infinity`, `1e309`, `-1e309` must all fail closed, retaining existing bytes.
2. `0`, `-0.0`, `-0.125` must fail closed.
3. A nonfinite *warmup* duration cannot be discarded silently.
4. A valid prior category cannot be published if a later selected category's time is invalid.
5. With no existing result file, an invalid sample must not create one.
6. A finite, strictly positive `1e-9` second protocol fixture remains accepted and appears in the normal valid JSON schema.

Each negative fixture uses a **correct, deterministic checksum `42`**; it isolates timing validity from checksum disagreement. Negative checks cover failure exit status, absence of reported mean/summary and `Wrote`, and exact previous-result bytes or file absence. These child timings are protocol fixtures, **not measured Mojo throughput**.

Run locally on an environment with Python:

```sh
python3 -m unittest discover -s tests -p 'test_bench_checksum_gate.py' -v
python3 -m py_compile scripts/bench.py tests/test_bench_checksum_gate.py
```

## Result and limits

**Confirmed:** an invalid numeric timing value can now block publication even when all checksums match. A matching checksum is necessary but is not sufficient to make a timing result meaningful. The previous invalid path was identified by direct code inspection and a Python float/JSON probe; the post-change protection was exercised in the repository's cross-architecture CI test steps.

This test does not verify the actual elapsed-time accuracy of a positive finite value, reject duplicate or ambiguous stdout records, audit existing historical JSON, prove crash-atomic output-file replacement, or establish native Mojo performance. Whole-workflow benchmark completion must be checked independently from the already-passed lightweight test step. The previously identified **arm64 checked-Span scanner CPU-clock question** remains open.

## Source and traceability

- code/test commit: [23b2a21f29cafde8995138d3d7a2dc2d1ccc0aca](https://github.com/iinoshirozheng/mojo-analyze/commit/23b2a21f29cafde8995138d3d7a2dc2d1ccc0aca)
- changed paths: `scripts/bench.py`, `tests/test_bench_checksum_gate.py`
- CI: [run 42201180145](https://github.com/iinoshirozheng/mojo-analyze/actions/runs/42201180145), jobs `127836562716` (arm64) and `127836563083` (x86_64)
- prior related research: `experiments/2026-11-05-checksum-publication-gate.md`
