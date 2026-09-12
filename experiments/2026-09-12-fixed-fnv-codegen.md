# 2026-09-12 — Fixed-width FNV-1a cross-architecture codegen differential

## Research question

Yesterday's controlled fixed-width FNV-1a experiment found that the same Mojo source-level algorithm was modestly slower than C on Linux x86_64 but much slower on Linux arm64. Does optimized generated code reveal a concrete structural difference in the timed 32-byte hash loop that can explain why matching the source algorithm did not produce matching cost?

This is one focused codegen follow-up to `2026-09-11-fixed-fnv-differential.md`. It does not introduce a new canonical benchmark category or change the Apple M4 Pro headline results.

## Method

The exact existing workload was reused without changing its semantics:

- 4,096 deterministic blocks × 32 bytes;
- 4,000,000 FNV-1a hashes over 128 MB total input;
- identical 64-bit FNV offset basis and prime in Mojo and C;
- raw byte storage in both implementations;
- no parsing, probing, table allocation, string ownership, or file I/O in the timed region;
- 2 discarded warmups + 7 measured trials;
- exact Mojo/C checksum equality required before timing is accepted.

Workflow run **34687667690**, commit `402032e3020459f1d3d99037972de9b0672cebea`, used:

- Mojo 1.0.0 (`ed45d567`);
- Ubuntu clang 18.1.3;
- Ubuntu 24.04 hosted runners on x86_64 and arm64;
- `mojo build --emit asm` for Mojo and `clang -O3 -S` for C.

The workflow uploaded the timing JSON plus both assembly files for each architecture. Whole-binary assembly size/opcode totals are not used as the main evidence because a Mojo executable includes substantial formatting/runtime code that the tiny C program does not.

## Correctness

Every measured Mojo and C execution on both architectures produced the same checksum:

`11482223147755189951`

This is the same checksum as the September 11 experiment.

## Timing cross-check

The purpose of this run is codegen, but timing was repeated to ensure the observed direction remained valid.

### Linux x86_64

| Implementation | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| C | 0.093214 s | 0.093253 s | 0.093102 s | 0.093297 s |
| Mojo | 0.096856 s | 0.096420 s | 0.096140 s | 0.099085 s |

- Mojo/C mean ratio: **1.0391×** — Mojo was about **3.9% slower**.
- Mojo/C median ratio: **1.0340×** — Mojo was about **3.4% slower**.
- The exact margin is smaller than September 11's shared-runner result (~6%), but the direction is unchanged; no canonical timing is updated from either run.

### Linux arm64

| Implementation | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| C | 0.054784 s | 0.054784 s | 0.054768 s | 0.054799 s |
| Mojo | 0.074820 s | 0.074832 s | 0.074607 s | 0.075015 s |

- Mojo/C mean ratio: **1.3657×** — Mojo was about **36.6% slower**.
- Mojo/C median ratio: **1.3659×** — Mojo was about **36.6% slower**.
- This closely reproduces September 11's ~36.4% arm64 result and the earlier ~37.2% supporting run.

## Codegen result: clang fully unrolls the 32-byte FNV chain; Mojo 1.0 does not

The decisive structural difference is the same on both architectures.

### x86_64

The C hot path is fully unrolled for all 32 bytes. In one outer hash iteration, assembly contains a straight dependency chain of byte loads, XORs, and `imulq` operations for offsets 0 through 31. There is no inner loop branch; only the outer 4,000,000-iteration loop remains.

The Mojo hot path retains the source-level 32-byte counted loop:

```text
load byte
increment byte index
xor hash, byte
imul hash, FNV_PRIME
compare byte index with 32
branch back while not equal
```

The FNV prime is hoisted into a register in both implementations, so repeated materialization of the constant is not the issue.

### arm64

Clang again fully unrolls the 32-byte chain. The hot path performs loads at offsets 0 through 31 with `eor` + `mul` operations and no per-byte loop branch; the final step is folded into `madd` before the outer-loop update.

Mojo again retains a counted byte loop:

```text
ldrb byte
add byte_index, 1
cmp byte_index, 32
eor hash, byte
mul hash, FNV_PRIME
b.ne inner_loop
```

Thus, for each 32-byte hash Mojo executes the inner compare/conditional-branch machinery 32 times, whereas clang's C output has no inner branch. Across 4,000,000 hashes that is roughly **128 million inner-loop branch decisions** in the Mojo code versus none in the unrolled C hash chain, in addition to the common outer-loop control.

## Interpretation

This experiment identifies a concrete codegen mismatch that the source-level comparison hid: **the fixed-trip 32-byte loop is fully unrolled by clang at `-O3`, but remains a scalar counted loop in Mojo 1.0 on both x86_64 and arm64.** The arithmetic itself remains the same FNV dependency chain; the difference is loop transformation/control overhead and the instruction scheduling opportunities created by unrolling.

The result is strong enough to reject the idea that the fixed-width differential should be interpreted only as an inherent cost of `UInt64` XOR/multiply in Mojo. Loop optimization is part of the compiled-cost difference.

It is **not** enough to claim that lack of unrolling alone explains the full timing ratio or why arm64 suffers much more than x86_64. The same structural mismatch exists on both architectures, while its measured penalty differs sharply. Microarchitectural branch/control costs, scheduling, register allocation, backend decisions, and other lowering details may contribute. A causal performance attribution requires a subsequent controlled variant that forces or manually expresses equivalent 32-step unrolling in Mojo and re-measures both architectures.

## Methodological lesson

For fixed-trip scalar kernels, matching the source algorithm and constants is not sufficient for an apples-to-apples performance explanation. Before rewriting data structures or blaming a primitive operation:

1. verify identical outputs;
2. inspect optimized code at the actual hot loop, not whole-binary instruction counts;
3. check loop-unrolling/vectorization/branch structure explicitly;
4. only then design one minimal source transformation to test causality.

Whole-binary assembly size was especially misleading here: Mojo's emitted file contains thousands of lines of formatting/runtime support, while the actual timed hash loop is small. Hot-region structural comparison is the useful evidence.

## Conclusion

**The fixed-width FNV Mojo-vs-C gap has a concrete codegen candidate: clang fully unrolls the known 32-byte inner loop on both x86_64 and arm64, while Mojo 1.0 leaves a per-byte counted loop.** This explains why identical source-level hash policy does not imply equivalent generated work, but a future controlled unrolled-Mojo experiment is required before assigning the entire performance gap to this mechanism.

Canonical `ANALYSIS.md`, `results/results.json`, and charts are intentionally unchanged.
