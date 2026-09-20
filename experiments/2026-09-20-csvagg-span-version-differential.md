# Mojo 1.0 → 1.1 checked-`Span` scanner differential

**Observed:** 2026-09-20  
**Scope:** one focused Category-D in-memory scanner/codegen experiment.  
**Workflow:** GitHub Actions run `35504356048` (`ubuntu-24.04` x86_64 and `ubuntu-24.04-arm` arm64).  
**Probe commit:** `b952e5ec55c2948b73ccb5d296ce93a993f57575`.

## Question

The 2026-09-19 scanner probe showed that, under Mojo 1.0.0, replacing checked `Span[UInt8]` byte indexing with an explicitly unsafe pointer read removed most of the isolated Mojo-vs-C scanner gap. Does that checked-access cost materially improve in the released Mojo 1.1.0 compiler/stdlib, or does the same mechanism persist?

This is a **version differential of the same source-level mechanism probe**, not a new benchmark category and not a recommendation to make the canonical benchmark unsafe.

## Method

- Source: `experiments/csvagg_scan_access/csvagg_scan_access.mojo`.
- Input: the normal synthetic Category-D corpus, **10,000,000 rows / 277.9 MiB / 99 categories**.
- Mojo 1.0 compiler: **1.0.0 (`ed45d567`)**, from the repository lock.
- Mojo 1.1 compiler: **1.1.0 (`8189361e`)**, resolved in an exact temporary Pixi environment so the repository lock stayed unchanged.
- C reference: Ubuntu clang **18.1.3**, `-O3`.
- Each Mojo binary contains the same two runtime modes:
  - `span`: checked `data[i]` access;
  - `ptr`: identical scan/control flow except the byte load comes from `data.unsafe_ptr()[unsafe_offset=i]`.
- The C reference uses the existing in-memory scanner path.
- The file is loaded before the timed scan in all cases.
- Correctness gate before timing, then **2 discarded warmups + 7 measured trials**, with five variants rotated through execution order.
- All five variants on both architectures produced exactly the same checksum:
  `10000000:68888897:109183569:15500599:57786009`.
- Optimized assembly was emitted for Mojo 1.0, Mojo 1.1, and C.

## Results

### Linux x86_64

| Variant | Mean | Median | Stdev | vs C mean |
|---|---:|---:|---:|---:|
| Mojo 1.0 checked `Span` | 0.359424 s | 0.362948 s | 0.007707 s | 1.3863× |
| Mojo 1.0 unsafe pointer | 0.280547 s | 0.280308 s | 0.003267 s | 1.0821× |
| Mojo 1.1 checked `Span` | 0.362176 s | 0.362687 s | 0.004156 s | 1.3969× |
| Mojo 1.1 unsafe pointer | 0.274068 s | 0.274384 s | 0.001369 s | 1.0571× |
| C scanner | 0.259270 s | 0.259873 s | 0.001636 s | 1.0000× |

- Mojo 1.0 `Span / ptr`: **1.2812× mean**, **1.2948× median**; pointer mode is about **21.95% faster** than checked Span.
- Mojo 1.1 `Span / ptr`: **1.3215× mean**, **1.3218× median**; pointer mode is about **24.33% faster**.
- Checked-Span mean from 1.0 → 1.1 changed by only **+0.77%** (slower in this shared-runner sample).
- Pointer mean from 1.0 → 1.1 improved by about **2.31%**.

### Linux arm64

| Variant | Mean | Median | Stdev | vs C mean |
|---|---:|---:|---:|---:|
| Mojo 1.0 checked `Span` | 0.330645 s | 0.330023 s | 0.001194 s | 1.8509× |
| Mojo 1.0 unsafe pointer | 0.195201 s | 0.194455 s | 0.002791 s | 1.0927× |
| Mojo 1.1 checked `Span` | 0.331992 s | 0.331569 s | 0.001255 s | 1.8584× |
| Mojo 1.1 unsafe pointer | 0.193530 s | 0.192859 s | 0.001620 s | 1.0833× |
| C scanner | 0.178640 s | 0.178606 s | 0.000289 s | 1.0000× |

- Mojo 1.0 `Span / ptr`: **1.6939× mean**, **1.6972× median**; pointer mode is about **40.96% faster**.
- Mojo 1.1 `Span / ptr`: **1.7155× mean**, **1.7192× median**; pointer mode is about **41.71% faster**.
- Checked-Span mean from 1.0 → 1.1 changed by only **+0.41%**.
- Pointer mean from 1.0 → 1.1 improved by about **0.86%**.

## Codegen check

The assembly evidence does **not** support a claim that Mojo 1.1 eliminated this safety machinery:

- x86_64 Mojo 1.0 / 1.1 assembly lines: **13,737 / 13,572**;
- arm64 Mojo 1.0 / 1.1 assembly lines: **12,808 / 12,364**;
- the bounds diagnostic string remains present once in both compiler versions on both architectures;
- whole-binary x86 `jae` counts are **26 / 26**;
- whole-binary arm64 `b.hs` counts are **18 / 16**.

Those mnemonic counts are only a coarse diagnostic: they include the whole binary and therefore are **not** a hot-loop branch census. They are retained as supporting evidence only. The runtime checked-vs-pointer intervention remains the stronger causal test.

## Conclusion

**Reject the hypothesis that released Mojo 1.1 materially fixes the checked-`Span` byte-access cost seen in this Category-D scanner.** On both Linux architectures, the checked-Span path is essentially unchanged in absolute time from Mojo 1.0, while the unsafe-pointer intervention still removes most of the relative Mojo-vs-C scanner gap. The measured penalty is still strongly architecture-dependent: roughly **24%** on this x86_64 run versus **42%** on arm64 when expressed as pointer-mode speedup over checked Span.

This narrows the interpretation of the Sep-19 result: the mechanism is **not merely a Mojo-1.0-only artifact**; it persists in released Mojo 1.1 for this workload and source shape. It is still inappropriate to generalize it to all `Span` access or to make the canonical benchmark unsafe. A later 1.2/stable differential should re-run the same correctness-preserving probe rather than assume this cost is permanent.

Because these timings come from GitHub-hosted shared runners, they stay in an experiment note and do **not** rewrite `ANALYSIS.md`, canonical `results.json`, or charts.

## Evidence / provenance

- Workflow run: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/35504356048
- x86_64 artifact ID: `10602998459` (`csvagg-scan-access-version-x86_64`)
- arm64 artifact ID: `10602898811` (`csvagg-scan-access-version-arm64`)
- Each artifact contains the timing JSON plus Mojo-1.0, Mojo-1.1 and C assembly.
- Probe source: `experiments/csvagg_scan_access/csvagg_scan_access.mojo`
- Harness: `experiments/csvagg_scan_access/run_version_bench.py`
