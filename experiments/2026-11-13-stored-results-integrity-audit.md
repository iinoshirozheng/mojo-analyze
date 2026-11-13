# 2026-11-13 — Independent stored-results integrity audit

## Single research question
Does the committed canonical `results/results.json` faithfully represent its own raw trial vectors, and are the stored checksum gates consistent? This is a **methodology/integrity audit**, not a new Mojo performance experiment. It is prioritized as a reproducible correctness check while the unresolved arm64 checked-Span region-scoped CPU-clock investigation requires a suitable instrumented runner.

## Frozen evidence
- Repository `main` at the start of this run: `8da0e6b010ae349c6938cd86daad14f9f5db4e15`.
- Exact inspected `results/results.json` Git blob: `c8b9084e1839bef977b52d8b517ff905de447cba` ([permalink](https://github.com/iinoshirozheng/mojo-analyze/blob/c8b9084e1839bef977b52d8b517ff905de447cba/results/results.json)).
- Canonical Python harness: `scripts/bench.py` blob `a535d28997f5486868637488f00af4f64740f87e`.
- Source was read through the connected GitHub API and recomputed in an independent JavaScript arithmetic pass. No compiler or native binaries were run.

## Method and checks
For every variant, recompute `mean=sum(times)/n`, sorted median, sample standard deviation with denominator `n-1`, minimum, maximum and `n` directly from raw `times`. Require all times to be finite and positive, require the stored `n` to equal the vector length, and check every category's variant checksum strings agree and `_checksum_ok === true`. Compare each stored statistic with its independently recomputed value using absolute tolerance `1e-10 * max(1, abs(reference))`; this threshold accommodates JSON decimal floating-point arithmetic but does not hide meaningful discrepancies. This is a deterministic data-integrity check, **not** a significance test or compiler-speed comparison.

## Verified results
- **5 categories × 5 variants = 25 variant records**, each with **7 trials**, for **175 raw elapsed-time observations**.
- **0 invalid/nonpositive/nonfinite trial values**, **0 sample-count mismatches**, **0 statistical-field mismatches** across mean, median, sample stdev, min, max and n.
- **0 checksum-gate mismatches**: within each of five categories, all five variant checksum strings agree and `_checksum_ok` is true.
- Maximum relative discrepancy across recomputed numeric statistics was approximately **3.34 × 10⁻¹⁶** (floating-point rounding only).
- Highest sample coefficient of variation (sample stdev/mean) was **4.47%**, for category E's manual Python implementation; next was sieve NumPy **3.84%**. These describe only the already stored seven-trial samples and do not establish cross-machine stability.

## Interpretation and negative result
**No internal inconsistency was found in the stored snapshot.** The data-level hypothesis that historical reported means, counts or checksum flags disagree with the committed trial vectors was rejected for this exact blob. This does **not** independently verify that executable implementations computed the correct problem answer, that the checksums were honestly emitted, that compiler versions were pinned at execution, or that published speedup comparisons are statistically conclusive. The checksum audit verifies recorded agreement, not a fresh oracle.

No canonical benchmark data, charts, `ANALYSIS.md`, source code or performance conclusion changed. A future audit should re-run the same checks against the new results blob and independently execute cross-language checksum oracles.

## Next highest-priority experiment
On a pinned Linux arm64 runner, instrument **region-scoped process/thread CPU clocks** around the checked-Span scanner, retain existing controls, verify checksums, and use enough rotated trials to distinguish the observed ~0.33s / ~0.56s / ~0.62s submodes. Inspect generated assembly and hardware counters if available; do not infer a mechanism from whole-process CPU/wall ratios alone.
