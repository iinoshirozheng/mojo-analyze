# 2026-11-07 — Benchmark CLI trial-count preflight

## Single question

Can invalid `--trials` / `--warmup` values enter the canonical benchmark protocol and either crash after executing a child or silently distort the measured sample count?

## Source inspection and deterministic reproduction

At the inspected baseline, `scripts/bench.py` parsed integer CLI arguments but did not validate their range. `run_variant` iterates `range(warmup + trials)`, includes a duration only when `i >= warmup`, then `stats` computes `statistics.mean(times)`. An isolated Python reproduction of **that exact count/filter/statistics logic** gave:

| trials | warmup | measured samples | outcome |
|---:|---:|---:|---|
| 0 | 1 | 0 | `StatisticsError: mean requires at least one data point` |
| -1 | 1 | 0 | same |
| 2 | -1 | 1 | one sample instead of two, because `range(1)` and `i >= -1` |

These are deterministic Python protocol checks, **not Mojo timings**. The first case can execute a warmup child before failing. The third silently undercounts intended trials.

## Intervention

Require `--trials >= 1` and `--warmup >= 0` immediately after argument parsing, before opening results or running children. Added four negative-case tests to `tests/test_bench_cli_counts.py`; each checks exit code 2, the expected parser error, no subprocess invocation and byte-for-byte preservation of an existing result file. Updated CI discovery to run both the pre-existing checksum tests and new CLI tests.

## Verification status

The arithmetic failure modes above were reproduced locally using Python. The committed regression tests target the actual imported `scripts/bench.py`, but **the complete test suite and native Mojo benchmark were not executed in this environment**; GitHub Actions results must be checked before claiming cross-platform verification. The tests require no Mojo toolchain. No throughput, compiler, or canonical benchmark result was changed.

## Conclusion and next step

A correctness-gated benchmark must also validate its measurement protocol **before side effects**. Negative warmup counts can be worse than an exception because they produce plausible-looking sample statistics with the wrong sample count. Next: confirm the CI protocol-test step on x86_64 and arm64, then separately pursue the region-scoped arm64 scanner CPU-clock hypothesis.
