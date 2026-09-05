# Category D: how much does Rust's default HashMap hasher cost?

Date: 2026-09-05

## Research question

Category D's Rust implementation uses borrowed `&str` keys, so unlike category C
it does not carry an owned-key allocation confound. That makes it a clean place
to test one specific hypothesis from `CONTRIBUTING.md`: how much of Rust's CSV
aggregation time comes from `std::collections::HashMap`'s default hasher versus
a cheap non-cryptographic hash?

This experiment changes only the `BuildHasher`. It does **not** replace the
canonical Rust result.

## Change

Added `rust/src/bin/csvagg_fnv.rs`, which is otherwise identical to
`rust/src/bin/csvagg.rs`:

- same input file and file I/O timing boundary;
- same borrowed `&str` category keys;
- same `HashMap::entry(...).or_insert(0)` aggregation;
- same integer parsing and arithmetic;
- same top-category scan and checksum;
- same Rust release profile (`opt-level = 3`).

The only intended variable is the hasher. The experimental variant uses a
standard-library-only `BuildHasherDefault` around incremental 64-bit FNV-1a, so
no external crate or unrelated data-structure change is introduced.

A focused harness (`scripts/bench_csvagg_rust_fnv.py`) runs 2 warmups + 7
measured trials per variant and refuses to report a result unless both variants
produce the exact same checksum. Raw experiment outputs are stored as CI
artifacts rather than overwriting canonical `results/results.json`.

Workflow run:
- https://github.com/iinoshirozheng/mojo-analyze/actions/runs/33959524960

## Verification

Both Linux architectures compiled successfully and all measured runs produced
the same checksum:

`10000000:99:electronics:5073122132805`

| Linux runner | Default HashMap mean | FNV-1a mean | Default / FNV | Effect |
|---|---:|---:|---:|---|
| x86_64 | 1.230920 s | 1.114450 s | 1.1045x | FNV ~10.5% faster |
| arm64 | 1.003074 s | 0.964321 s | 1.0402x | FNV ~4.0% faster |

Seven-trial dispersion was low in the corrected run: x86_64 stdev was about
1.06% of the default mean and 0.19% of the FNV mean; arm64 was about 0.30% and
0.11%, respectively. The improvement direction is therefore consistent across
both architectures, while its magnitude is architecture-sensitive.

## Important failed first attempt

The first FNV implementation was **not** valid evidence even though its output
checksum matched. Its `Hasher::write()` implementation reset the FNV offset
basis on every call. Rust's `Hash` implementation is allowed to feed one key to
a hasher through multiple `write` calls (for example, string hashing may append
a sentinel), so resetting state violated the `Hasher` streaming contract and
created severe collision behavior. That invalid version appeared dramatically
slower than the default hasher.

The corrected implementation initializes the offset basis once in `Default` and
updates `self.0` incrementally across every `write` call. Only the corrected run
above is used for the conclusion.

This failure is a methodology reminder: checksum agreement proves semantic
output equivalence, but it does **not** prove that an experimental substitute
preserved the intended algorithmic mechanism or complexity. Performance
experiments still need API-contract and implementation sanity checks.

## Conclusion

**Rust's default HashMap hasher is a measurable Category-D cost, but not a
single dominant explanation.** Replacing only the hasher with FNV-1a improves
the full realistic CSV workload by about 10.5% on Linux x86_64 and 4.0% on
Linux arm64. That is large enough to matter when interpreting Rust-vs-Mojo/C
results, but small enough—and architecture-dependent enough—that it should not
be described as "the" cause of the category's ranking.

The canonical benchmark remains unchanged because its stated methodology uses
standard-library defaults, and these measurements come from shared GitHub
runners rather than the controlled macOS machine used for the headline table.
The experimental FNV variant is retained so the hasher effect can be reproduced
or re-checked on a controlled host later.
