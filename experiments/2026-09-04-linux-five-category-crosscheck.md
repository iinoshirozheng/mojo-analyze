# Linux five-category cross-check: does the macOS ranking generalize?

Date: 2026-09-04

## Research question

Now that Linux CI builds C and includes category E, do the current macOS rankings generalize to GitHub-hosted Linux x86_64 and Linux arm64, or are there repeatable architecture-specific reversals?

This is a cross-platform validation study, not a replacement for the canonical Apple M4 Pro numbers in `ANALYSIS.md`.

## Method

I aggregated the three most recent successful main-branch Benchmark workflow runs that contain all five categories and all five language/library variants:

- run 24: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/33739056015
- run 26: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/33742263617
- run 27: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/33857429717

Each CI run used one warmup plus 3 measured trials per variant. Pooling the three runs gives 9 measured trials per variant per architecture. All five categories passed the repository's cross-language checksum gate in all six architecture/run combinations; no timing below comes from a checksum mismatch.

Because GitHub-hosted runners are shared and absolute wall time varied noticeably between x86_64 runs, conclusions use both pooled means and per-run relative ratios. A claim is treated as robust only when the ordering or ratio direction repeats across all three runs.

## Results

### Linux x86_64

Pooled mean over 9 measured trials per variant:

| Category | Mojo | Rust | C | Optimized Python library | Winner |
|---|---:|---:|---:|---:|---|
| Mandelbrot | 0.0493 s | 0.1325 s | 0.1348 s | NumPy 0.7841 s | **Mojo** |
| Sieve | 0.2460 s | 0.2577 s | 0.2372 s | NumPy 0.2727 s | **C** |
| Word-frequency | 0.5737 s | 0.7449 s | 0.3327 s | Counter 3.2875 s | **C** |
| CSV aggregation | 1.1110 s | 1.1736 s | 0.4457 s | pandas 3.0857 s | **C** |
| JSON parsing | 0.9188 s | 0.7801 s | 0.4176 s | stdlib json 5.0827 s | **C** |

The relative ordering is broadly consistent with macOS. The most stable same-technique ratios were:

- Sieve Mojo/C median ratio across runs: **1.043x** (Mojo ~4.3% slower than C)
- Word-frequency Mojo/C: **1.744x**
- CSV aggregation Mojo/C: **2.487x**
- JSON parsing Mojo/C: **2.365x**

The exact wall times move with runner load, but these ranking directions persist.

### Linux arm64

Pooled mean over 9 measured trials per variant:

| Category | Mojo | Rust | C | Optimized Python library | Winner |
|---|---:|---:|---:|---:|---|
| Mandelbrot | 0.0923 s | 0.1093 s | 0.1093 s | NumPy 0.7963 s | **Mojo** |
| Sieve | 0.1646 s | 0.1909 s | 0.1736 s | NumPy 0.1447 s | **NumPy** |
| Word-frequency | 0.5158 s | 0.7589 s | 0.3005 s | Counter 3.2946 s | **C** |
| CSV aggregation | 1.3529 s | 1.0001 s | 0.4249 s | pandas 2.5600 s | **C** |
| JSON parsing | 1.2244 s | 0.6429 s | 0.4035 s | stdlib json 5.0217 s | **C** |

Three effects are especially stable across all three arm64 runs:

1. **The previously observed Sieve reversal remains real.** NumPy beats Mojo in all three new runs; Mojo/NumPy is roughly 1.11-1.18x depending on the run.
2. **Category D has an architecture-specific Mojo regression relative to Rust.** Mojo is slower than Rust in all three runs, with a median Mojo/Rust ratio of **1.342x**. On x86_64 the median ratio is **0.930x**, so the direction flips by architecture.
3. **Category E's Mojo-vs-Rust gap becomes much larger on arm64.** The median Mojo/Rust ratio is **1.902x** on arm64 versus **1.199x** on x86_64. The Mojo/C median ratio is **3.040x** on arm64 versus **2.365x** on x86_64.

Word-frequency is comparatively stable: Mojo remains ahead of Rust but well behind C on both Linux architectures.

## Conclusion

The clean five-category Linux comparison confirms that the repository's main qualitative ranking is not purely a macOS artifact: Mojo still wins explicit-SIMD Mandelbrot and C still dominates the scalar/data-processing categories on both Linux architectures.

However, **Linux arm64 is not just a uniformly slower version of x86_64**. It shows repeatable workload-specific changes in Mojo's relative position:

- Sieve: NumPy > Mojo only on this Linux arm64 environment.
- CSV aggregation: Mojo falls behind Rust by ~34% median, while it is slightly ahead of Rust on x86_64.
- JSON parsing: Mojo's deficit to Rust and C widens substantially on arm64.

These are architecture/backend investigation targets, not evidence that "arm64 is bad for Mojo" in general: Apple Silicon does not reproduce the same pattern. The next useful step for categories D/E is generated-code or profiling comparison on real Linux arm64 hardware, with particular attention to byte-scanning, integer parsing, branch structure, and memory-access lowering.

The canonical benchmark results are intentionally unchanged. This experiment strengthens the cross-platform evidence without mixing shared-runner Linux timings into the controlled-machine scoreboard.
