# 2026-11-12 — Partial benchmark summary provenance

## One focused question
Does `pixi run bench --only new` report historical categories preserved in `results/results.json` as if they were measured during this invocation?

## Evidence and finding
At the inspected `main` baseline, the partial-run path loads the existing JSON snapshot and merges only the selected categories. That is correct preservation behavior. However, the final summary iterated `results.items()`, not the current `benchmarks` selection. Consequently a partial run containing a previous `old` category printed `old` in the current summary, even though it had not been executed. This is a **provenance/reporting methodology issue**, not evidence of incorrect timings or checksum mismatch.

## Intervention
Changed the summary loop to iterate the resolved `benchmarks` selection, then retrieve each just-validated entry from `results[name]`. The published JSON still preserves unselected historical categories; the console summary now describes only the current invocation. Added `tests/test_bench_partial_summary.py`: a synthetic run mocks a single selected category, preloads a historical result, checks both categories survive in JSON, and checks only the selected category appears after the summary header.

Commits: [fix](https://github.com/iinoshirozheng/mojo-analyze/commit/b9c08443b22439224e1ec989e4d22df430923998), [regression test](https://github.com/iinoshirozheng/mojo-analyze/commit/b00b3f427b77ef54cf2c02ac029f752859d1d22c).

## Verification boundary
The issue and fix were verified by direct inspection of the exact GitHub source and control-flow comparison. The test was committed but **not executed successfully in this session**: the local runtime could not resolve raw.githubusercontent.com to obtain the repository checkout, and no workflow run was returned for the test commit at inspection time. Therefore this is a source-verified correction with a pending executable regression check, **not** a completed native Mojo benchmark or CI-verified result. Do not change `ANALYSIS.md`, timing results or charts on this basis.

## Next
Run `python3 -m unittest discover -s tests -p 'test_bench*.py' -v` in CI; separately, the strongest unresolved performance hypothesis remains the arm64 checked-Span scanner's region-scoped CPU-clock study with pinned Mojo and stable C/pointer controls.
