# Mojo 1.1 → 1.2 nightly checked-`Span` scanner differential

**Observed:** 2026-09-21  
**Scope:** one focused Category-D in-memory scanner/codegen experiment.  
**Workflow:** GitHub Actions run `35588217725` (`ubuntu-24.04` x86_64 and `ubuntu-24.04-arm` arm64).  
**Probe commits:** `c72e35665bf54883a9652621ee58dc26777c462e`, then `14462e8d3fab426d44917df6455fa90a3ae552c8` to increase the measured sample to 15 trials.

## Question

The 2026-09-19 mechanism probe found that checked `Span[UInt8]` byte indexing accounts for most of the isolated Mojo-vs-C scanner gap under Mojo 1.0, and the 2026-09-20 version differential showed that released Mojo 1.1 does not materially remove that cost. Does the Sep-21 Mojo 1.2 nightly (`1.2.0.dev2026092105`) improve the same checked-access path while leaving the unchecked-pointer control essentially unchanged?

This is a **version differential of the same source-level mechanism probe**. It is not a new benchmark category and not a recommendation to make the canonical benchmark unsafe.

## Method

- Source: `experiments/csvagg_scan_access/csvagg_scan_access.mojo`.
- Input: the normal synthetic Category-D corpus, **10,000,000 rows / 277.9 MiB / 99 categories**.
- Mojo 1.1 compiler: **1.1.0 (`8189361e`)**.
- Mojo 1.2 nightly compiler: **1.2.0.dev2026092105 (`e9569894`)**, resolved from the nightly channel in an exact temporary Pixi environment.
- C reference: Ubuntu clang **18.1.3**, `-O3`.
- Each Mojo binary contains the same two runtime modes:
  - `span`: checked `data[i]` access;
  - `ptr`: identical scanner/control flow except the byte load comes from `data.unsafe_ptr()[unsafe_offset=i]`.
- The file is loaded before the timed scanner in every variant.
- The harness first requires exact checksum agreement, then runs **2 discarded warmups + 15 measured trials**. Five variants are rotated through execution order on every trial.
- All five variants on both architectures produced exactly the same checksum:
  `10000000:68888897:109183569:15500599:57786009`.
- Optimized assembly was emitted for Mojo 1.1, Mojo 1.2 nightly, and C.

## Results

### Linux x86_64

| Variant | Mean | Median | Stdev | vs C mean |
|---|---:|---:|---:|---:|
| Mojo 1.1 checked `Span` | 0.358452 s | 0.356524 s | 0.005523 s | 1.3793× |
| Mojo 1.1 unsafe pointer | 0.275340 s | 0.275309 s | 0.000957 s | 1.0595× |
| Mojo 1.2 nightly checked `Span` | 0.368185 s | 0.367651 s | 0.001849 s | 1.4168× |
| Mojo 1.2 nightly unsafe pointer | 0.276194 s | 0.275960 s | 0.002772 s | 1.0628× |
| C scanner | 0.259880 s | 0.257497 s | 0.008662 s | 1.0000× |

- Mojo 1.2-nightly checked `Span` is **2.72% slower by mean and 3.12% slower by median** than Mojo 1.1 in this run.
- The pointer control is essentially unchanged: **+0.31% by mean, +0.24% by median**.
- In Mojo 1.2 nightly, pointer mode is about **25.0% faster** than checked Span by mean time (`Span / ptr = 1.3331×`).
- The C mean contains one visible high trial (`0.290153 s`), so the exact C-relative mean ratios should not be overinterpreted. The compiler-version differential and the checked-vs-pointer intervention are the stronger evidence here.

There is therefore **no x86_64 evidence that this nightly removes the checked-Span cost**. The observed ~3% checked-path slowdown is small enough that this shared-runner experiment should not be promoted into a general compiler-regression claim.

### Linux arm64

| Variant | Mean | Median | Stdev | vs C mean |
|---|---:|---:|---:|---:|
| Mojo 1.1 checked `Span` | 0.331345 s | 0.331334 s | 0.001693 s | 1.8585× |
| Mojo 1.1 unsafe pointer | 0.194664 s | 0.194202 s | 0.002419 s | 1.0919× |
| Mojo 1.2 nightly checked `Span` | 0.439498 s | 0.332961 s | 0.136883 s | 2.4652×* |
| Mojo 1.2 nightly unsafe pointer | 0.192889 s | 0.192934 s | 0.000785 s | 1.0819× |
| C scanner | 0.178284 s | 0.178338 s | 0.000374 s | 1.0000× |

`*` The Mojo-1.2-nightly checked-Span mean is **not representative of one stable timing population**. Its 15 trials are visibly bimodal:

- 9 fast trials: approximately **0.330–0.333 s**, mean **0.332084 s**;
- 6 slow trials: approximately **0.568–0.617 s**, mean **0.600620 s**.

The corresponding Mojo 1.1 checked path, both pointer controls, and C are stable in the same job. Every fast and slow Mojo-1.2 checked-Span trial still passed the checksum contract.

For the stable center of the distribution, the Mojo-1.2 checked-Span **median is only 0.49% slower** than Mojo 1.1; the pointer median is **0.65% faster**. Using medians, pointer mode remains about **42.1% faster** than the checked path on arm64. Thus the normal/fast mode shows the same mechanism as Mojo 1.1 rather than a material fix.

The new slow mode is evidence of **timing instability specific to the Mojo-1.2 checked variant in this hosted-runner observation**, but this single run does not identify its cause. It must not be reported as a 32.6% compiler regression merely because the arithmetic mean is inflated by the second mode. A repeated run and/or lower-level system evidence would be required to attribute it to the compiler/runtime rather than a runner interaction.

## Codegen check

The optimized assembly also does not support a claim that the nightly broadly removed checked-access machinery:

- x86_64 assembly lines, Mojo 1.1 / 1.2 nightly: **13,572 / 13,089**;
- arm64 assembly lines, Mojo 1.1 / 1.2 nightly: **12,364 / 11,957**;
- the bounds diagnostic string remains present once in both compiler versions on both architectures;
- whole-binary x86 `jae` counts are **26 / 25**;
- whole-binary arm64 `b.hs` counts are **16 / 16**.

These whole-binary mnemonic counts are only supporting diagnostics and are **not** a hot-loop branch census. The stronger test remains the same-source checked-vs-pointer runtime intervention, combined with the stable pointer control across compiler versions.

## Conclusion

**Reject the hypothesis that the Sep-21 Mojo 1.2 nightly materially fixes the checked-`Span` byte-access cost in this Category-D scanner.** On x86_64 the checked path is slightly slower while the pointer control is flat; on arm64 the normal/median checked-path behavior is essentially unchanged and the pointer control is also flat. The large checked-vs-pointer gap therefore persists on this pinned nightly.

The arm64 result adds a separate methodology warning: one compiler/variant produced a clearly **bimodal** distribution while correctness stayed intact. In that situation, a single arithmetic mean is not a defensible estimate of a stable performance regime. Report the raw distribution/median, keep the anomaly distinct from the mechanism conclusion, and repeat before assigning causality.

The unsafe-pointer path remains a diagnostic intervention only. Canonical benchmark code should stay safe unless an independently justified design change removes the overhead without weakening the semantics. The same probe should be repeated when Mojo 1.2 reaches a stable release rather than treating a nightly result as permanent.

Because these timings come from GitHub-hosted shared runners, this result stays in an experiment note and does **not** rewrite `ANALYSIS.md`, canonical `results.json`, or charts.

## Evidence / provenance

- Workflow run: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/35588217725
- x86_64 artifact ID: `10632144723` (`csvagg-scan-access-nightly-x86_64`), SHA-256 `17f345b821bda565684766b6636501dbf7b2892bf9634fc543dfda037e2e5e57`.
- arm64 artifact ID: `10633421507` (`csvagg-scan-access-nightly-arm64`), SHA-256 `604e89e625d9a288c15b19cd8c02646f4140c080209174b40b47bafec7d5f37f`.
- Probe source: `experiments/csvagg_scan_access/csvagg_scan_access.mojo`.
- Harness: `experiments/csvagg_scan_access/run_nightly_bench.py`.
- Workflow: `.github/workflows/research-csvagg-scan-access-nightly.yml`.
