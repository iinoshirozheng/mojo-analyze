# Does a cross-variant checksum mismatch actually fail the benchmark run?

Observed: **2026-11-05 (Asia/Taipei)**. Scope: one benchmark-methodology investigation and its regression fix. No Mojo performance ranking was measured or changed.

## Question and provenance

`CONTRIBUTING.md` and `ANALYSIS.md` promise that the CPU harness refuses timings when language variants disagree. Does that promise hold at the process exit, result-file and reporting boundaries?

Sources inspected before selecting the task: current `main`, `ecosystem/RADAR_POLICY.md`, `CONTRIBUTING.md`, the methodology section of `ANALYSIS.md`, the latest September brief/index, recent commits, and the September 24 arm64 CPU-time experiment. The latter's region-scoped CPU-clock follow-up remains valuable, but the local execution environment has no Mojo/Pixi toolchain. Rather than invent native measurements, this run selected a fully executable harness-methodology test suggested by today's [Despell/noeira discoveries](../ecosystem/2026-11-05.md).

Baseline:
- source checkout: `cd21c3587af4d2fd177779ffe9083ca9dc380efc`;
- unchanged pre-fix harness blob: `6475e78e8b236b6b7fcbc69c83ed2066708093de`;
- the local source copy was verified against that exact Git blob SHA before testing;
- runtime: Python **3.13.5**, Linux **x86_64**;
- test mechanism: real subprocess invocation of the harness's `main()` with temporary fixture configuration and real Python child processes; only the benchmark commands/root are replaced;
- every child emits protocol fixtures, not real workload timings: `TIME_SECONDS: 0.125`, with either matching or deliberately different checksums.

## Reproduced defect

The baseline verifies that each individual variant is deterministic, but cross-variant disagreement only sets `_checksum_ok = false`. Execution continues, overwrites `results/results.json`, prints a comparative timing summary and exits **0**.

A representative negative control emits checksum `42` for implementation 0 and `43` for implementation 1, each consistently across one warmup and two collected samples. The old harness prints both the mismatch warning and `Wrote .../results/results.json`, then prints `=== Summary ... ===` and returns success. A consumer relying on exit status can therefore accept a failed correctness comparison.

This demonstrates a failure of enforcement, **not** that previous stored real benchmark results were necessarily incorrect.

## Single focused change

The cross-variant mismatch path now raises `RuntimeError` containing the benchmark name and checksum map. Because all selected results remain in memory until the final write, a failed full run or `--only` run leaves an existing result file byte-for-byte unchanged and does not create a new one.

Per-variant progress now says samples were collected pending checksum validation. Performance statistics are not printed before the final successful validation boundary. The successful result schema, benchmark commands, trial collection, checksum parser and statistics calculations remain unchanged; the latter functions and benchmark definitions were compared by AST.

The existing Benchmark workflow runs the small standard-library regression suite before expensive toolchain setup. This adds a regression gate, not a new benchmark or experimental CI workload.

## Before/after verification

Command:

```sh
python -m unittest discover -s tests -p 'test_bench_checksum_gate.py' -v
python -m py_compile scripts/bench.py tests/test_bench_checksum_gate.py
```

The same nine tests produced **4 failures / 5 passes before**, and **9 passes after** the fix:

| Contract tested | Before | After |
|---|---|---|
| Full-run mismatch: nonzero exit, no summary, preserve old bytes | FAIL | PASS |
| Partial-run mismatch: nonzero exit, preserve old bytes | FAIL | PASS |
| Mismatch with no old result: do not create a result file | FAIL | PASS |
| Later category mismatch: do not publish earlier passing categories | FAIL | PASS |
| Matching full run replaces old snapshot and retains statistics/schema | PASS | PASS |
| Matching partial run preserves unselected category | PASS | PASS |
| Warmup-only checksum disagreement is rejected | PASS | PASS |
| Missing checksum field is rejected | PASS | PASS |
| Child process exits nonzero | PASS | PASS |

The negative-test helper checks exit status, exact file bytes/absence, and absence of `Summary`, `mean=` and `Wrote` in stdout. The positive controls verify stored sample counts, checksum, mean and partial-merge contents. No nondeterministic wall-time thresholds are used.

To reproduce the negative control against the exact old harness using the new test file:

```sh
git show cd21c3587af4d2fd177779ffe9083ca9dc380efc:scripts/bench.py > /tmp/mojo-bench-before.py
MOJO_ANALYZE_BENCH_FILE=/tmp/mojo-bench-before.py \
  python -m unittest discover -s tests -p 'test_bench_checksum_gate.py' -v
# Expected: four failures, because the old harness returns success on mismatch.
```

## Conclusion and limits

**A checksum comparison is not an operational correctness gate unless failure blocks publication and reaches the caller as failure.** This repository's cross-variant branch violated that requirement; controlled fault injection reproduced it and a minimal fail-closed change repaired it.

The tests cover newly executed selected categories and preserve existing full/partial semantics. They do not audit legacy unselected result records, establish that agreeing implementations match an independent oracle, validate all possible malformed numeric fields, or make the final file write crash-atomic. Those are separate questions, not silently claimed guarantees.

This run did not compile Mojo, rerun the five native workloads, inspect new native assembly, or establish an end-to-end CI success result. The native source, canonical `results/results.json`, charts and `ANALYSIS.md` are unchanged. Existing scanner/codegen questions remain open.
