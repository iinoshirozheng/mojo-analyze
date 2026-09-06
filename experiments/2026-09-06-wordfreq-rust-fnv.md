# Rust Category C: default `HashMap` hasher vs FNV-1a

Date: 2026-09-06

## Research question

How much of Rust Category C's word-frequency runtime comes from the standard
`HashMap` hasher, independently of the implementation's separate owned-key
allocation cost?

The canonical Rust Category C implementation uses `HashMap<Vec<u8>, u64>` and
allocates an owned byte vector for each token insertion path. That differs from
Category D, whose Rust map borrows `&str` keys. To isolate the hasher rather
than accidentally measuring two changes at once, this experiment deliberately
keeps Category C's existing `Vec<u8>` ownership strategy unchanged.

## Change

Added `rust/src/bin/wordfreq_fnv.rs`, identical in workload and tokenization to
`rust/src/bin/wordfreq.rs` except that the map uses the same validated
incremental FNV-1a `Hasher` used by the earlier Category D experiment:

- same deterministic 15,000,000-token corpus
- same ASCII alphanumeric tokenization and lowercase conversion
- same owned `Vec<u8>` keys and `std::mem::take` allocation behavior
- same `HashMap::entry` aggregation
- same top-word scan and tie-breaking
- same release profile
- only the map hasher changes

A focused harness (`scripts/bench_wordfreq_rust_fnv.py`) runs 2 warmups plus 7
measured trials for each binary, rejects non-deterministic checksums, requires
exact checksum agreement between variants, and writes its own experiment JSON
without touching canonical `results/results.json`.

Workflow run:
https://github.com/iinoshirozheng/mojo-analyze/actions/runs/34026612241

The first focused CI attempt failed before timing because that job had not
regenerated the synthetic corpus. The job was corrected to run the existing
deterministic `prepare-corpus` task first; no benchmark result from the failed
attempt was used.

## Verification

Both Linux architectures compiled under Rust 1.98.1 / LLVM 22.1.8 and every
measured execution produced the exact same checksum:

`15000000:317:the:2366876`

| Linux runner | Default mean | FNV-1a mean | Default / FNV | Mean-time reduction |
|---|---:|---:|---:|---:|
| x86_64 | 0.650154 s | 0.544444 s | 1.1942x | 16.3% |
| arm64 | 0.751995 s | 0.698422 s | 1.0767x | 7.1% |

Seven-trial details:

- x86_64 default: median 0.646592 s, stdev 0.009394 s
- x86_64 FNV-1a: median 0.536961 s, stdev 0.019743 s
- arm64 default: median 0.751912 s, stdev 0.001046 s
- arm64 FNV-1a: median 0.696975 s, stdev 0.003161 s

The direction is consistent across both architectures despite shared-runner
noise: the non-cryptographic hasher materially reduces Category C runtime.

## Conclusion

**Rust's default `HashMap` hasher is a real, measurable cost in Category C, but
it is not the whole explanation for Rust's implementation behavior.** Swapping
only the hasher yields a 1.194x mean speedup on Linux x86_64 and 1.077x on Linux
arm64 while preserving the existing owned-key allocation strategy and exact
output.

Together with the earlier Category D hasher experiment, this supports a broader
methodological conclusion: cross-language hash-table benchmarks should not
quietly attribute a standard-library map's security-oriented hashing policy to
the language/compiler itself. Hasher policy and key ownership are independent
implementation choices and should be isolated separately.

The canonical benchmark remains unchanged. Its Rust variant is still the honest
"standard library default" baseline; this FNV variant is causal evidence about
one implementation choice, not a replacement scoreboard entry. Because these
measurements come from shared GitHub-hosted Linux runners, `ANALYSIS.md`'s
controlled-machine numbers are also left unchanged.
