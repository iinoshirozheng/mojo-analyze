# 2026-09-11 — Fixed-width FNV-1a Mojo vs C differential

## Research question

After the Category C/D raw-slot experiments showed that slot representation alone does not explain the remaining Mojo-vs-C gap, does the **FNV-1a hash primitive itself** show a measurable Mojo-vs-C cost when parsing, probing, key ownership, table storage, and file I/O are removed?

This is a focused diagnostic experiment, not a new canonical benchmark category and not a replacement for the primary Apple M4 Pro results in `ANALYSIS.md` / `results/results.json`.

## Contract

The Mojo and C programs implement the same fixed-width hash workload:

- 4,096 blocks × 32 bytes each;
- deterministic xorshift64-filled byte buffer, prepared before timing;
- 4,000,000 FNV-1a 64-bit hash iterations (128,000,000 bytes hashed);
- FNV offset basis `14695981039346656037` and prime `1099511628211`;
- raw byte storage in both languages (`unsafe_alloc[UInt8]` in Mojo, `malloc` in C);
- no parser, file I/O, hash table, probing, string allocation, or key-copy work;
- checksum = XOR of `(hash + iteration)` over all iterations;
- 2 discarded warmups + 7 measured trials per implementation;
- exact checksum equality required before accepting timings.

Sources:

- `experiments/fnv_fixed/fnv.mojo`
- `experiments/fnv_fixed/fnv.c`
- `experiments/fnv_fixed/run_bench.py`
- `.github/workflows/research-fnv-fixed.yml`

Definitive workflow run: **34588010392** on commit `e560c2e65bbbe8925f8ecc1488890da38c07fdab`.

Both architectures used **Mojo 1.0.0 (`ed45d567`)** and **Ubuntu clang 18.1.3** on Ubuntu 24.04 hosted runners.

## Correctness

Every accepted trial produced the same checksum in Mojo and C on both architectures:

`11482223147755189951`

The runner also rejects within-implementation checksum drift, so timing data is only emitted after the correctness gate passes.

## Results

### Linux x86_64

| Implementation | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| C | 0.094055 s | 0.094019 s | 0.093612 s | 0.094675 s |
| Mojo | 0.099763 s | 0.099495 s | 0.096705 s | 0.105914 s |

- Mojo / C mean ratio: **1.0607×** — Mojo was **6.1% slower** by mean.
- Mojo / C median ratio: **1.0582×** — Mojo was **5.8% slower** by median.
- The Mojo trial range was about **9.2% of its mean**, driven by one slow shared-runner trial. The C range was about **1.1%**. The median therefore deserves more weight than the exact mean margin here, though both estimators agree on direction.

### Linux arm64

| Implementation | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| C | 0.054744 s | 0.054749 s | 0.054725 s | 0.054761 s |
| Mojo | 0.074661 s | 0.074611 s | 0.074541 s | 0.074855 s |

- Mojo / C mean ratio: **1.3638×** — Mojo was **36.4% slower** by mean.
- Mojo / C median ratio: **1.3628×** — Mojo was **36.3% slower** by median.
- Dispersion was very small: roughly **0.07%** range/mean for C and **0.42%** for Mojo.

An earlier arm64 run from workflow 34587780980 independently produced a similar Mojo/C mean ratio of about **1.372×**, so the large arm64 direction is reproducible across two hosted-runner executions. That earlier run is supporting evidence only; run 34588010392 is the definitive cross-architecture result because both architectures completed under the same self-contained workflow revision.

## Interpretation

The null hypothesis that “once both languages use the same FNV-1a policy, the hash primitive is effectively equal-cost” is **not supported** by this experiment. Even after parsing, probing, allocation, table storage, and file I/O are removed, Mojo remains measurably slower than C for this scalar fixed-width FNV loop, and the size of that difference is strongly architecture-dependent.

This does **not** establish FNV as the sole or dominant cause of the full Category C/D application gaps. Those workloads still contain parsing, delimiter scanning, hash-table probing, equality checks, aggregation, and I/O, and the canonical headline results run on different primary hardware. The experiment therefore narrows the investigation rather than closing it:

1. matching hash policy is necessary for a fair comparison, but matching the source-level algorithm does not guarantee equal compiled cost;
2. the much larger arm64 differential makes architecture-specific code generation a plausible next question;
3. parser/probe paths remain unresolved and should not be blamed on hashing without profiling;
4. shared-runner timings remain advisory and do not modify canonical `ANALYSIS.md` or `results/results.json`.

## Conclusion

**Fixed-width FNV-1a itself is a real Mojo-vs-C differential in this controlled workload, especially on Linux arm64, but it is only one component of the remaining Category C/D gap.** The strongest next follow-up is to inspect the generated FNV loop on x86_64 versus arm64 and then profile parsing/probing separately, rather than performing another storage rewrite.
