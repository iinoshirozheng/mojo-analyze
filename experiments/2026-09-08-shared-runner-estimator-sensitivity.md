# Shared-runner estimator sensitivity — 2026-09-08

## Research question

Do the qualitative winners in the current five-category Linux benchmark suite change when a three-trial shared-runner result is summarized by **mean**, **median**, or **best-of-3**, and is a simple >5% within-run dispersion rejection enough to prevent estimator-sensitive conclusions?

This is a methodology experiment surfaced by the 2026-09-07 ecosystem brief. It does **not** change the canonical benchmark implementations or `ANALYSIS.md` conclusions.

## Evidence

Three independent successful GitHub Actions runs were selected, one per recent daily state of `main`:

| Run | Date (UTC) | Head SHA | Artifacts used |
|---|---|---|---|
| #46 / `34026719667` | 2026-09-06 | `2d9364c580d4ad3b78cf443181ab6f5a4749af55` | `results-linux-x86_64`, `results-linux-arm64` |
| #52 / `34110437536` | 2026-09-07 | `d36639ed9ccb4b6463d391d4ad6354b2100d4602` | `results-linux-x86_64`, `results-linux-arm64` |
| #53 / `34210411684` | 2026-09-08 | `df60ba410cec13a41edbc331f20c074381431e75` | `results-linux-x86_64`, `results-linux-arm64` |

Each normal Linux matrix job used the repository's standard `1 warmup + 3 measured trials`. Combining the three independent runs therefore gives **9 measured observations per architecture/benchmark/variant** while retaining the per-run three-trial structure needed to study estimator choice.

The analysis covered 2 architectures × 5 benchmarks × 3 runs = **30 benchmark/run/architecture cells**, containing 150 implementation cells and 450 measured timings.

## Correctness gate

All 30 benchmark/run/architecture cells had `_checksum_ok = true`. Within every cell, all implementations reported the same workload checksum. No timing was used from a checksum-invalid cell.

This verifies output equivalence for the existing benchmark contract; it does not imply that every implementation uses the same library, storage strategy, or algorithmic mechanism. Those semantic differences remain documented elsewhere in the repository.

## Estimators

For each implementation's three measured times in one workflow run:

- **mean** = arithmetic mean of the three trials;
- **median** = middle value of the three trials;
- **best-of-3** = minimum measured time;
- **relative range** = `(max - min) / median`.

The >5% diagnostic is deliberately simple and is tested here as a candidate warning threshold, not declared a canonical validity gate.

## Results

### Winner sensitivity within individual shared-runner jobs

- **Mean and median selected the same winner in all 30/30 cells.**
- **Best-of-3 agreed with the mean winner in 29/30 cells.**
- The only winner flip was **Linux x86_64 Sieve in run #52**.

Run #52 x86_64 Sieve:

| Variant | Trials (s) | Mean (s) | Median (s) | Best (s) | Relative range |
|---|---|---:|---:|---:|---:|
| C | `0.196057, 0.197598, 0.199432` | 0.197696 | 0.197598 | 0.196057 | 1.7% |
| Mojo | `0.205249, 0.195946, 0.205391` | 0.202195 | 0.205249 | **0.195946** | 4.6% |
| NumPy | `0.213943, 0.215337, 0.209515` | 0.212932 | 0.213943 | 0.209515 | 2.7% |
| Rust | `0.218277, 0.251860, 0.230388` | 0.233508 | 0.230388 | 0.218277 | 14.6% |
| Python | `4.304637, 4.615755, 4.304101` | 4.408164 | 4.304637 | 4.304101 | 7.2% |

Mean and median both put **C first**. Best-of-3 instead picks **Mojo**, by only about 0.000111 s. Importantly, neither C nor Mojo crosses the proposed 5% relative-range warning threshold. A threshold that rejects only visibly noisy cells therefore would **not** prevent this best-of-N winner flip.

### Full ordering is more estimator-sensitive than the winner

Looking at the complete five-implementation order, not just first place:

- mean vs median order matched in **27/30** cells;
- mean vs best-of-3 order matched in **27/30** cells;
- median vs best-of-3 order matched in **26/30** cells.

The differences were concentrated in Sieve and close C/Rust ordering in Mandelbrot; most did not affect the first-place language.

### Dispersion diagnostic

Only **8/150 implementation cells (5.3%)** exceeded a 5% within-run relative range. The largest was Rust Sieve in run #52 x86_64 at **14.6%**. Other >5% cells were Sieve variants or slow Python Mandelbrot measurements.

This diagnostic is useful for identifying obviously noisy measurements, but the x86_64 Sieve winner flip demonstrates that it cannot make best-of-N robust by itself: selection bias can matter even when both competing variants individually look “quiet.”

### Aggregating the three independent runs

Pooling the nine measured observations per architecture/benchmark/variant and recomputing mean, median, and global best produced the **same winner for all three estimators in all 10 architecture × benchmark combinations**:

| Architecture | Mandelbrot | Sieve | Word-frequency | CSV | JSON |
|---|---|---|---|---|---|
| Linux x86_64 | Mojo | C | C | C | C |
| Linux arm64 | Mojo | NumPy | C | C | C |

The closest pooled case remains Linux x86_64 Sieve. Across nine observations, C wins by:

- **1.65% on mean** (`0.191025 s` C vs Mojo ratio 1.0165),
- **3.87% on median** (`0.197598 s` C vs Mojo ratio 1.0387),
- only **0.26% on global best** (`0.166687 s` C vs Mojo ratio 1.0026).

That shrinking gap under the minimum statistic is exactly why a single best-of-N value should not be used as strong evidence on a shared runner.

## Conclusion

The hypothesis that estimator choice would routinely overturn the current five-category winners is **rejected for this sample**: mean and median agree on all 30 per-run winners, and the three-run pooled winners are identical under mean, median and best.

The useful negative result has one qualification: **best-of-N is less robust for close races**. It produced one per-run winner flip that a 5% per-variant dispersion filter would not catch. Therefore:

1. keep mean/median or repeated relative ratios as the primary descriptive evidence on shared runners;
2. treat best-of-N as an advisory lower-bound statistic, not a canonical winner selector;
3. keep dispersion checks, but do not assume they remove minimum-selection bias;
4. when the observed gap is only a few percent, require repeated independent runs or a controlled host before promoting a regression/winner claim.

No canonical benchmark code, `results/results.json`, README benchmark table, or `ANALYSIS.md` conclusion is changed by this shared-runner methodology study.

## Reproduction

1. Download the two normal results artifacts from workflow runs `34026719667`, `34110437536`, and `34210411684`.
2. For every benchmark, require `_checksum_ok == true` and identical checksum strings across variants.
3. For each variant and run, calculate mean, median, `min(times)`, and `(max(times)-min(times))/median(times)`.
4. Compare winner and full ordering under the three estimators.
5. Concatenate the three trial arrays for the same architecture/benchmark/variant to form nine observations and repeat the estimator comparison.

Artifact retention is finite, so the run IDs, head SHAs, formulas, raw exceptional-cell timings, and pooled winner table are recorded here for independent review after artifacts expire.
