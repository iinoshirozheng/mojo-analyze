# Category D parse+hash decomposition — 2026-09-15

## Question

How much of Category D's Mojo-vs-C end-to-end gap is already present after file read, delimiter scanning, quantity/price parsing, and variable-length FNV-1a hashing, **before** hash-table slot lookup, probing, byte equality, and per-category aggregation?

This follows the raw-slot and variable-length-unroll experiments. Those interventions were too small or architecture-specific to explain the full Category-D gap, so the next useful step was to split the workload at a semantic boundary rather than try another representation tweak.

## Experiment

The focused variants are:

- `experiments/csvagg_parsehash/csvagg_parsehash.mojo`
- `experiments/csvagg_parsehash/csvagg_parsehash.c`
- `experiments/csvagg_parsehash/run_bench.py`
- `.github/workflows/research-csvagg-parsehash.yml`

Both focused implementations preserve the same Category-D input and the same work up through:

1. reading the 10,000,000-row CSV into memory;
2. skipping the header;
3. byte scanning `order_id` and `category` delimiters;
4. parsing `quantity` and `price_cents` digit by digit;
5. hashing the raw category byte span with the same FNV-1a offset/prime.

They then stop before the table. To prevent dead-work timing, both produce a shared checksum over row count, XOR of category hashes, revenue sum, and total category-byte length. The canonical Mojo and C Category-D binaries are also run in the same job for a same-run end-to-end ratio.

Each architecture uses two warmup rounds plus seven measured rounds. The four binaries rotate execution order each round so one implementation is not systematically first or last on a shared runner.

## Verification

Workflow run: `34956359784`

Toolchains on both jobs:

- Mojo `1.0.0 (ed45d567)`
- Ubuntu clang `18.1.3`
- Ubuntu 24.04 hosted runners
- x86_64 and arm64 jobs both completed successfully

All measured/warmup executions were deterministic and cross-language checksums agreed:

- parse+hash: `10000000:3168868070999988426:26261536001964:109183569`
- canonical Category D: `10000000:99:electronics:5073122132805`

The workflow also emitted optimized assembly for the focused Mojo and C variants. Assembly confirms both binaries contain the expected delimiter/numeric/FNV work and that the table code is absent from the focused sources. Whole-binary assembly size is not treated as a performance metric because Mojo carries substantial runtime/support code; no stronger pass-level codegen claim is made from the broad grep alone.

Artifacts:

- x86_64 artifact `10391975162`
- arm64 artifact `10392060563`

## Results

| Architecture | Variant | Mean | Median |
|---|---|---:|---:|
| Linux x86_64 | parse+hash Mojo | 0.751860 s | 0.751974 s |
| Linux x86_64 | parse+hash C | 0.440932 s | 0.440691 s |
| Linux x86_64 | full Mojo | 1.050677 s | 1.050292 s |
| Linux x86_64 | full C | 0.512700 s | 0.505787 s |
| Linux arm64 | parse+hash Mojo | 1.084753 s | 1.084440 s |
| Linux arm64 | parse+hash C | 0.343814 s | 0.343703 s |
| Linux arm64 | full Mojo | 1.290696 s | 1.290185 s |
| Linux arm64 | full C | 0.418892 s | 0.419295 s |

Relative ratios:

| Architecture | Parse+hash Mojo/C | Full Mojo/C | Mojo parse+hash / full | C parse+hash / full |
|---|---:|---:|---:|---:|
| Linux x86_64 | **1.705×** | **2.049×** | 71.6% | 86.0% |
| Linux arm64 | **3.155×** | **3.081×** | 84.0% | 82.1% |

Median ratios tell the same qualitative story: about 1.706× parse+hash versus 2.077× full on x86_64, and about 3.155× parse+hash versus 3.077× full on arm64.

## Interpretation

The result sharply narrows Category D's open question.

### arm64: the gap is already present before table operations

Removing slot lookup, probing, key equality, and aggregation does **not** reduce the Mojo/C ratio. The focused parse+hash path is actually slightly wider at 3.155× than the same-run full ratio of 3.081×. Parse+hash accounts for roughly 84% of Mojo's full time and 82% of C's.

That rejects a strong version of the hypothesis that Category D's arm64 gap is primarily a Mojo hash-table/probing problem. On this runner, the dominant relative disadvantage exists in the file-read / delimiter-scan / numeric-parse / variable-length-hash prefix.

### x86_64: the prefix is already slower, but table work widens the gap

The focused path is still 1.705× C, so a substantial gap exists before any table operation. The full same-run ratio grows to 2.049×, which means probing/equality/aggregation or their interaction with surrounding code adds another Mojo-relative disadvantage on x86_64.

This is consistent with the earlier raw-slot result: storage representation alone was only a few percent, so the remaining table-side cost is more likely in probing/equality/control flow than in `List` backing storage itself.

### Cross-architecture conclusion

There is no single portable "hash table is the bottleneck" explanation. The decomposition boundary changes the ratio materially on x86_64 but not on arm64. The next experiment should split the **prefix itself**—for example parser-only versus parser+hash with an identical checksum contract—before another table/storage rewrite.

The result also shows why end-to-end ratios should be decomposed with equal-contract variants: a component can be a large fraction of runtime in both languages while the *relative* disadvantage behaves differently by architecture.

## Limits

- These are GitHub-hosted shared-runner measurements, so exact small percentage differences are advisory rather than canonical performance claims.
- Subtracting two separately compiled program timings is not a cycle-accurate attribution of the removed table stage; compiler optimization can change around the cut point. The robust evidence is the large ratio behavior at the semantic boundary, especially the arm64 non-reduction.
- File reading remains inside the timed region by design because canonical Category D includes it.
- This experiment does not distinguish delimiter scanning, decimal parsing, FNV hashing, bounds checks, or compiler loop transformations inside the focused prefix.
- Canonical `ANALYSIS.md`, `results/results.json`, and charts are unchanged.

## Next candidate

Build a **parser-only** pair that preserves the same file read, delimiter scans, quantity/price parsing, and observable checksum but omits FNV. Compare it against today's parse+hash pair in the same interleaved job. That would isolate the variable-length hashing contribution from the parser/scanner contribution without reintroducing hash-table behavior.
