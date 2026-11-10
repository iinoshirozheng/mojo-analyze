# 2026-11-10 — Fail-closed benchmark selection

## One question
Can an explicit `--only` typo or empty comma-separated token silently produce a successful no-op that preserves or republishes stale benchmark results, despite no selected workload having run?

## Baseline and causal mechanism
Inspected `scripts/bench.py` on main after the radar. The previous code used `set(args.only.split(",")) if args.only else None` and filtered known benchmark names. Thus `--only siev` yielded an empty benchmark list and still reached `out_path.write_text(...)` and a successful exit. `--only ""` was interpreted as a full run rather than an invalid explicit selection. A mixed `--only sieve,typo` silently ignored the unknown name. No performance measurements are implicated; this is a correctness/provenance protocol problem.

## Intervention
Validate the complete explicit selection **before reading or writing results and before launching any child process**. Strip whitespace, reject empty tokens and unknown names with argparse error (exit 2), and only then build the selected list. Preserve valid selection and partial-result merging.

Code commit: [53a78ef](https://github.com/iinoshirozheng/mojo-analyze/commit/53a78ef363c281a2b1a5de3f9569e33d7331db6e).
Regression-test commit: [42f3429](https://github.com/iinoshirozheng/mojo-analyze/commit/42f3429be17223ee33875e7272228daec092697b).
Tests: `tests/test_bench_selection.py` covers unknown-only, mixed known/unknown, empty tokens, and a valid whitespace-trimmed selection with result merge. The existing workflow discovers `test_bench*.py`.

## Verification status and limitations
The pre-fix failure mechanism is established by direct source inspection. Regression tests are committed but **not yet independently executed in this run**: the local container cannot resolve github.com for checkout, and GitHub combined status query for the test commit returned no statuses. Do not label cross-platform CI passed or a Mojo performance experiment completed until the tests actually run. The expected behavior is explicit and falsifiable: all invalid selections must exit 2, launch zero child processes, and preserve the existing result file byte-for-byte; a valid selection must still publish and merge.

No benchmark binary, compiler, `ANALYSIS.md`, result JSON or chart was modified. Next verification: `python3 -m unittest discover -s tests -p 'test_bench*.py' -v` on CI Linux x86_64 and arm64. If the test fails, repair the patch rather than claiming verified success.

## Conclusion
An explicit benchmark selection is part of the measurement contract. A fail-open selector can make an empty or incomplete run look successful even when checksum gates are correct. Enforce exact category resolution before execution/publication; do not interpret an empty selection as an acceptable successful benchmark.
