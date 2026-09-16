# Category-D parser-only vs parse+hash decomposition — 2026-09-16

## Question

How much of Category D's **pre-table** Mojo-vs-C gap is already present before variable-length FNV-1a hashing?

The 2026-09-15 decomposition removed hash-table probing, key equality and aggregation while preserving CSV read + delimiter scanning + numeric parsing + category hashing. That experiment showed a 1.705× Mojo/C parse+hash ratio on x86_64 and 3.155× on arm64, so the strongest next cut point was to remove FNV while preserving the same parser/scanner prefix.

## Experiment

Added a parser-only Mojo/C pair under `experiments/csvagg_parseronly/` and ran it in the **same interleaved rounds** as the existing parse+hash pair.

Parser-only preserves:

- reading the same generated 10,000,000-row / 277.9 MiB Category-D CSV file;
- header skipping;
- order-id delimiter scanning;
- category-span discovery;
- quantity parsing;
- price-cents parsing and line-end scanning.

Parser-only removes:

- variable-length FNV-1a hashing;
- hash-table probing;
- key equality;
- aggregation/table updates.

To keep the parser-only work observable, both languages produce `rows:revenue_sum:category_bytes_total`. The existing parse+hash pair retains its `rows:hash_xor:revenue_sum:category_bytes_total` checksum.

### Environment and execution

Workflow: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/35083338301  
Harness commit: `3e5c0fecbcc11700470cb0ca32f7d38804c0b35f`  
Toolchains: Mojo 1.0.0 (`ed45d567`) from the locked Pixi environment; Ubuntu clang 18.1.3.  
Architectures: GitHub-hosted Linux x86_64 (`__archspec=zen2`) and Linux arm64 (`__archspec=neoverse_n2`).  
Trials: 2 warmups + 7 measured trials per binary, with execution order rotated each round.

Both jobs completed successfully. Result JSON and optimized parser-only assembly were retained as workflow artifacts.

## Correctness gate

All seven measured trials and both warmups were deterministic within each binary, and the cross-language checksums matched on both architectures:

- parser-only: `10000000:26261536001964:109183569`
- parse+hash: `10000000:3168868070999988426:26261536001964:109183569`

Timing conclusions below are therefore based only on checksum-equivalent work contracts.

## Results

### Linux x86_64

| Variant | Mojo mean | C mean | Mojo/C mean | Mojo median | C median | Mojo/C median |
|---|---:|---:|---:|---:|---:|---:|
| parser-only | 0.650581 s | 0.339874 s | **1.914×** | 0.649518 s | 0.339390 s | **1.914×** |
| parse+hash | 0.811136 s | 0.393096 s | **2.063×** | 0.811283 s | 0.393339 s | **2.063×** |

At this semantic boundary, adding variable-length FNV widens the Mojo/C ratio by about **0.149×**. Parser-only already accounts for about 80.2% of the Mojo parse+hash wall time and 86.5% of the C parse+hash wall time in this run.

The separately compiled binaries imply an approximate wall-time increment of 0.1606 s for Mojo versus 0.0532 s for C when FNV is present. That subtraction is useful directionally but is **not** treated as an exact isolated hash cost because removing code can change compiler optimization and layout.

### Linux arm64

| Variant | Mojo mean | C mean | Mojo/C mean | Mojo median | C median | Mojo/C median |
|---|---:|---:|---:|---:|---:|---:|
| parser-only | 0.972203 s | 0.272371 s | **3.569×** | 0.971458 s | 0.272603 s | **3.564×** |
| parse+hash | 1.077862 s | 0.342854 s | **3.144×** | 1.080441 s | 0.343135 s | **3.149×** |

The parser-only ratio is actually **larger** than the parse+hash ratio. In other words, the severe arm64 disadvantage is already present before FNV is introduced; adding the same FNV work to both languages narrows the relative ratio in this run.

Parser-only is about 90.2% of Mojo parse+hash wall time and 79.4% of C parse+hash wall time. The separately compiled binaries imply an approximate FNV-associated increment of 0.1057 s for Mojo and 0.0705 s for C, again only as a directional decomposition rather than an exact component timer.

## Codegen inspection

The workflow emitted optimized parser-only assembly for both languages and architectures. The parser-only assemblies do not contain the FNV-1a prime/multiply chain, confirming that the intervention removed hashing rather than merely making its output dead.

Whole-file assembly size is not a useful direct performance metric here: the Mojo artifacts include substantial runtime/startup/generic-library code (12,892 lines on x86_64 and 12,147 on arm64) while the C files are 335 and 339 lines. The useful conclusion from this artifact is the semantic/codegen boundary, not a claim that file line count explains runtime.

## Conclusion

**Variable-length FNV is not the primary explanation for the Category-D pre-table gap, especially on arm64.**

- x86_64: a large **1.914×** Mojo/C disadvantage already exists in the parser-only prefix; FNV makes the same-run ratio moderately worse at **2.063×**.
- arm64: the parser-only prefix is already **3.569×** slower in Mojo, while parse+hash is **3.144×**. The strongest disadvantage therefore precedes FNV.

This narrows the remaining search space from `file read + delimiter scan + numeric parse + hash` to the **file-read / scanner / numeric-parser prefix**. It also rejects a stronger version of the hypothesis that the arm64 Category-D gap is mainly a hash primitive/codegen problem.

The next high-value experiment is another semantic-boundary cut: separate **read+delimiter scanning** from **numeric parsing**, or otherwise profile the parser-only hot region before changing more storage/hash representations.

## Scope / non-conclusions

- Do not subtract two independently compiled binaries and call the difference an exact component cost.
- Do not compare today's same-run ratios directly with prior hosted-runner ratios as though absolute runner performance were stable.
- This experiment does not identify whether file reading, delimiter scanning, bounds checks, numeric accumulation or another parser-prefix detail is the remaining root cause.
- Canonical `ANALYSIS.md`, `results.json` and charts remain unchanged; this is a focused hosted-runner decomposition experiment.
