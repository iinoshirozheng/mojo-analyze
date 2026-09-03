# Category C: do raw-pointer hash-table slots remove Mojo's List overhead?

Date: 2026-09-03

## Research question

`CONTRIBUTING.md` proposed a concrete explanation for category C's remaining
Mojo-vs-C gap: the otherwise-identical open-addressing byte-span hash table in
Mojo stores its five fixed-capacity slot arrays in `List[...]`, so repeated
slot probes may still pay enough bounds/storage overhead to matter. Category B
previously improved dramatically after moving its sieve buffer to raw memory.

This experiment asks only whether applying the same storage idea to category C
produces a similarly meaningful win.

## Change

Added `benchmarks/wordfreq/wordfreq_rawslots.mojo`, identical to the canonical
Mojo word-frequency implementation in:

- corpus parsing and timed file I/O
- FNV-1a hashing
- byte-span keys (no per-token String allocation)
- 8192-slot linear-probing table
- collision/key comparison logic
- final entry materialization and insertion sort
- workload and checksum

The only intended change is slot storage:

- canonical: `List[Bool]`, `List[UInt64]`, and `List[Int]`
- experiment: `alloc[UInt8/UInt64/Int]` plus `unsafe_offset` indexing

Raw-pointer deallocation is performed after the timer stops, matching the
canonical List variant whose destruction is not in its measured region.

A focused harness (`scripts/bench_wordfreq_rawslots.py`) ran both binaries with
2 discarded warmups + 7 measured trials on GitHub-hosted Linux x86_64 and
arm64 runners. It rejects results unless every run is deterministic and the two
variants produce the same checksum.

Workflow run:
https://github.com/iinoshirozheng/mojo-analyze/actions/runs/33741903445

## Verification

Both architectures compiled successfully and every run produced the identical
checksum:

`15000000:317:the:2366876`

| Linux runner | List-slot mean | Raw-slot mean | List / raw | Effect |
|---|---:|---:|---:|---|
| x86_64 | 0.653626 s | 0.641628 s | 1.0187x | raw ~1.9% faster |
| arm64 | 0.516413 s | 0.524102 s | 0.9853x | raw ~1.5% slower |

Dispersion was low in all four series (7 trials each): x86_64 stdev was
~1.67 ms for List and ~0.47 ms for raw slots; arm64 stdev was ~0.75 ms and
~1.18 ms respectively.

## Conclusion

**The hypothesis is not supported as an explanation for category C's large
Mojo-vs-C gap.** Replacing all five fixed-capacity `List` slot arrays with raw
pointers changes performance by only a few percent, and the sign even reverses
between the two Linux architectures. That is nowhere near the ~1.6x gap the
hypothesis was meant to explain.

This is a useful negative result. Category C should not copy category B's
optimization story by assumption: the hot cost is likely elsewhere (hash/key
byte scanning, branch/probe codegen, file/data handling, or other generated-code
differences). A future follow-up should inspect generated assembly/codegen or
profile the canonical category-C binary before attempting more unsafe storage
rewrites.

The experimental source and harness remain in the repository for
reproduction, but the one-off CI job is removed after this measurement so it
does not add permanent cost to every push.

`ANALYSIS.md` and canonical benchmark results are intentionally unchanged:
these measurements come from shared Linux runners, while the headline table is
from the controlled Apple M4 Pro/macOS environment.
