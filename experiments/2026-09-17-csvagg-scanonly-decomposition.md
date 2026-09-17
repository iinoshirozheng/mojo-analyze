# Category-D scanner-only vs parser-only decomposition — 2026-09-17

## Question

How much of Category D's remaining **parser-prefix** Mojo-vs-C gap is already present before quantity/price numeric parsing?

The 2026-09-16 parser-only experiment removed FNV and hash-table work but retained file read, delimiter scanning, and digit-to-integer accumulation. It still measured a same-run Mojo/C ratio of about 1.91× on x86_64 and 3.57× on arm64. The next semantic cut is therefore to remove numeric accumulation while preserving the same file-read and field-scanning structure.

## Experiment

Added a scanner-only Mojo/C pair under `experiments/csvagg_scanonly/` and ran it in the **same interleaved rounds** as the existing parser-only pair.

Scanner-only preserves:

- reading the same generated 10,000,000-row Category-D CSV file inside the timed region;
- header skipping;
- scanning all four fields to their delimiters/newline;
- field-boundary bookkeeping.

Scanner-only removes:

- quantity digit-to-integer accumulation;
- price digit-to-integer accumulation;
- revenue multiplication/summing;
- variable-length FNV hashing;
- hash-table probing, equality, and aggregation.

To keep scanner work observable, both languages emit `rows:order_id_bytes:category_bytes:quantity_bytes:price_bytes`. The parser-only pair retains its separate `rows:revenue_sum:category_bytes` checksum. Checksums are compared **within each semantic contract**, not across the scanner and parser variants.

### Environment and execution

Workflow: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/35208929618  
Harness commit: `f0845450bb24f64cb44ad2c9bd052c317ca1116c`  
Toolchains: repository-locked Mojo 1.0.0 (`ed45d567`) and Ubuntu clang 18.1.3.  
Architectures: GitHub-hosted Linux x86_64 (`ubuntu-24.04`) and Linux arm64 (`ubuntu-24.04-arm`).  
Trials: 2 warmups + 7 measured trials per binary, with execution order rotated each round.

Both architecture jobs completed successfully. Timing JSON and optimized scanner/parser assembly were retained as workflow artifacts.

## Correctness gate

All warmups and measured trials were deterministic within each binary, and Mojo/C checksums matched on both architectures:

- scanner-only: `10000000:68888897:109183569:15500599:57786009`
- parser-only: `10000000:26261536001964:109183569`

Timing conclusions below are based only on checksum-equivalent Mojo/C work contracts.

## Results

### Linux x86_64

| Variant | Mojo mean | C mean | Mojo/C mean | Mojo median | C median | Mojo/C median |
|---|---:|---:|---:|---:|---:|---:|
| scanner-only | 0.609980 s | 0.380391 s | **1.604×** | 0.609888 s | 0.374835 s | **1.627×** |
| parser-only | 0.625970 s | 0.391929 s | **1.597×** | 0.629556 s | 0.391321 s | **1.609×** |

The scanner-only Mojo/C ratio is essentially the same as the parser-only ratio. Removing numeric accumulation does **not** collapse the x86_64 disadvantage.

One scanner-C trial was visibly slower (`0.403049 s`) than the remaining cluster around roughly `0.371–0.392 s`, so the scanner mean ratio (1.604×) and median ratio (1.627×) differ more than usual. Both estimators support the same qualitative result: a roughly 1.6× cross-language gap is already present in file read + delimiter scanning + field-boundary bookkeeping.

The separately compiled binaries imply only a small scanner→parser wall-time increment in this run (about 0.0160 s for Mojo and 0.0115 s for C), but that subtraction is **not** treated as an exact numeric-parser cost because deleting code changes compiler optimization and layout.

### Linux arm64

| Variant | Mojo mean | C mean | Mojo/C mean | Mojo median | C median | Mojo/C median |
|---|---:|---:|---:|---:|---:|---:|
| scanner-only | 0.955270 s | 0.256706 s | **3.721×** | 0.953457 s | 0.255550 s | **3.731×** |
| parser-only | 0.973074 s | 0.274066 s | **3.551×** | 0.974584 s | 0.273926 s | **3.558×** |

The arm64 result is stronger: the scanner-only ratio is actually **larger** than parser-only. The seven measured trials are tight (scanner Mojo stdev ~0.0067 s; scanner C ~0.0028 s), and mean/median ratios agree closely.

Numeric parsing therefore cannot be the dominant explanation for the severe arm64 parser-prefix gap. The cross-language disadvantage is already present in the earlier **file-read / byte-scanning / loop-boundary** portion of the workload.

As with earlier semantic cuts, the separately compiled binaries should not be subtracted into a precise component timer. Ratio movement localizes where the disadvantage already exists; it does not make stage costs additive.

## Codegen inspection

The workflow emitted optimized scanner-only and parser-only assembly for Mojo and C on both architectures.

The C artifacts give a clear intervention check:

- scanner-only hot loops contain delimiter/newline byte loads, comparisons, index increments, and field-length bookkeeping;
- parser-only adds digit accumulation (`value = value * 10 + digit`) — on x86_64 clang lowers the decimal accumulation with LEA sequences, while arm64 contains `madd`/`mul`-style arithmetic in the parser hot region.

The scanner variants do not contain that numeric-parsing work in the corresponding C hot loops. Mojo whole-file assembly contains substantial runtime/generic-library code, so global instruction or line-count comparisons are not used as evidence; the retained artifacts are for targeted hot-region follow-up rather than whole-file counting.

## Conclusion

**The Category-D parser-prefix gap is already present before numeric parsing.**

- x86_64: scanner-only is about **1.60×–1.63×** Mojo/C, essentially the same as parser-only's **1.60×–1.61×**.
- arm64: scanner-only is about **3.72×–3.73×**, even larger than parser-only's **3.55×–3.56×**.

This rejects the stronger hypothesis that quantity/price decimal accumulation is the primary remaining cause of the parser-only Mojo/C disadvantage. After successively removing table operations, FNV hashing, and now numeric parsing, the severe arm64 gap survives in the **file-read + delimiter-scanning + loop/control prefix**.

The strongest next experiment is to separate **bulk file ingestion from in-memory scanning** while preserving identical bytes and checksum semantics, then inspect the scanner hot loop at a more local IR/assembly boundary. That can distinguish runtime/string/file-read overhead from byte-scanning/codegen without changing hash/table representations again.

## Scope / non-conclusions

- Hosted GitHub runners are secondary evidence; canonical M4 results remain unchanged.
- Do not call the difference between separately compiled scanner and parser binaries an exact numeric-parser cost.
- This experiment does not yet distinguish file-read/string materialization from delimiter-loop codegen.
- It does not justify changing `ANALYSIS.md`, `results.json`, or canonical charts.
- It does justify moving the Category-D investigation upstream from numeric parsing toward the file-ingestion / byte-scanning boundary.
