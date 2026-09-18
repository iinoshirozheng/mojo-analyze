# Category D: file-ingestion vs in-memory scanner boundary — 2026-09-18

## Question

**Does excluding bulk file ingestion materially collapse Category D's scanner-only Mojo-vs-C gap?**

The Sep-17 scanner-only decomposition had already removed numeric parsing, FNV hashing, probing/equality, and aggregation, yet still measured a large Mojo/C gap—especially on Linux arm64. That left a mixed prefix containing both file materialization and byte/delimiter scanning. This follow-up moves the timing boundary without changing the scanner itself.

## Experimental design

The experiment uses one Mojo binary and one C binary, each with two timing scopes:

- `--scope full`: start the timer before loading `orders.csv`, then scan it;
- `--scope scan`: load the exact same CSV before the timer, then time the same scanner.

The scanner is identical between the two scopes inside each language binary. Both scopes preserve:

- the same deterministic 10,000,000-row / 277.9 MiB Category-D corpus;
- header skip and all four field-boundary scans per row;
- the same byte-count bookkeeping;
- the same cross-language checksum contract.

The Mojo `scan` scope intentionally still times `String.as_bytes()` and the byte-scanning loop; only `open(...).read()` is moved outside the timer. The C `scan` scope moves `fopen`/seek/`malloc`/`fread`/close outside the timer. This is therefore an **ingestion/materialization timing-boundary test**, not a claim about cold-disk throughput.

Harness: `experiments/csvagg_scan_scope/`  
Workflow: `.github/workflows/research-csvagg-scan-scope.yml`  
Workflow run: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/35333511286

## Environment and verification

Both GitHub-hosted Linux architectures used:

- Mojo **1.0.0 (`ed45d567`)**;
- Ubuntu clang **18.1.3**;
- 2 warmups + **7 measured trials**;
- interleaved, rotating execution order across `mojo-full`, `c-full`, `mojo-scan`, `c-scan`;
- optimized assembly emitted for the same two binaries used for measurement.

Every measured mode on both architectures produced the identical checksum:

```text
10000000:68888897:109183569:15500599:57786009
```

Both matrix jobs completed successfully and uploaded JSON + assembly artifacts.

## Results

### Linux x86_64

| Scope | Mojo mean | C mean | Mojo/C mean | Mojo median | C median | Mojo/C median |
|---|---:|---:|---:|---:|---:|---:|
| read + scan | 0.635778 s | 0.375303 s | **1.694×** | 0.640241 s | 0.374780 s | **1.708×** |
| preloaded scan | 0.403406 s | 0.250098 s | **1.613×** | 0.405127 s | 0.249733 s | **1.622×** |

Stdevs were 0.013772 s / 0.001386 s for full Mojo/C and 0.015674 s / 0.000691 s for preloaded-scan Mojo/C.

Moving ingestion outside the timed region reduced the mean Mojo/C ratio by about **4.8%** (1.694× → 1.613×). That is a modest movement relative to the x86_64 scanner gap and close enough to the observed Mojo trial dispersion that it should not be overinterpreted as a precise component cost.

### Linux arm64

| Scope | Mojo mean | C mean | Mojo/C mean | Mojo median | C median | Mojo/C median |
|---|---:|---:|---:|---:|---:|---:|
| read + scan | 1.036331 s | 0.250686 s | **4.134×** | 1.034077 s | 0.250263 s | **4.132×** |
| preloaded scan | 0.420211 s | 0.178815 s | **2.350×** | 0.420000 s | 0.178498 s | **2.353×** |

Stdevs were 0.009101 s / 0.001549 s for full Mojo/C and 0.000792 s / 0.000933 s for preloaded-scan Mojo/C.

On arm64 the effect is large and stable: excluding file ingestion/materialization reduced the same-run mean ratio by about **43.2%** (4.134× → 2.350×), with the median telling the same story. Within the same binaries, the mean full-minus-scan timing boundary was about 0.616 s for Mojo versus 0.072 s for C. Those differences are useful localization evidence, but they are **not** presented as standalone cold-I/O benchmarks because repeated rounds use the host page cache and the language runtimes materialize file contents differently.

## Interpretation

The stronger hypothesis that the arm64 scanner-only gap is mostly the byte-scanning loop is **rejected**. A major part of the end-to-end arm64 disadvantage is introduced before the scanner proper, in the file-ingestion/materialization boundary.

The converse hypothesis that file ingestion explains the whole problem is also rejected. After the exact file bytes are already resident and the load is outside the timer, Mojo still takes about **2.35×** C on arm64 and **1.61×** C on x86_64 for the same checksum-gated scanner contract. There is therefore still a substantial in-memory byte-scanning / indexing / loop-control codegen problem to explain.

This experiment also strengthens the decomposition methodology: when a semantic cut can be implemented by moving the timer inside the **same compiled binary**, it avoids the codegen confound introduced by comparing separately compiled reduced programs. The remaining ratio is consequently a cleaner target for assembly/IR investigation.

## Conclusion

**File ingestion/materialization is a material, architecture-specific contributor to Category D's arm64 gap, but it is not the whole cause.** Excluding it collapses the mean arm64 ratio from 4.134× to 2.350×, while x86_64 moves only from 1.694× to 1.613×. The next investigation should stay on the now-isolated in-memory scanner and inspect its hot-loop byte access, bounds/safety checks, and branch/control lowering before introducing another implementation rewrite.

Canonical `ANALYSIS.md`, `results/results.json`, and charts are unchanged because these measurements come from GitHub-hosted shared runners and are used for localization, not canonical performance publication.
