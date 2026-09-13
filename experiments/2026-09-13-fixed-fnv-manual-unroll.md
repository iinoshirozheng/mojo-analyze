# 2026-09-13 — Manual unrolling closes the fixed-width FNV loop gap

## Research question

The September 12 codegen differential showed that clang fully unrolls the known 32-byte FNV-1a inner loop while Mojo 1.0 leaves a counted loop on both Linux x86_64 and arm64. Is that loop-transformation mismatch actually causal for the fixed-width Mojo-vs-C performance gap?

This experiment changes exactly one mechanism: the Mojo hash body is written as 32 explicit byte/XOR/multiply steps instead of a `while k < 32` loop. Data generation, raw storage, FNV constants, outer iteration count, checksum, C comparator, warmups and measured trials are unchanged.

## Method

Workflow run **34751149904**, source/setup commit `2f074b7891027b22220c863166f5244acb0bcb60`, ran on Ubuntu 24.04 hosted runners for x86_64 and arm64.

The shared contract is unchanged from the September 11–12 fixed-width experiments:

- 4,096 deterministic blocks × 32 bytes;
- 4,000,000 FNV-1a hashes over 128 MB of selected input;
- identical 64-bit FNV offset basis and prime;
- raw byte storage;
- no parsing, probing, allocation, string ownership, or file I/O in the timed hash region;
- 2 discarded warmups + 7 measured trials per implementation;
- exact checksum equality required across counted-loop Mojo, manually unrolled Mojo, and C;
- optimized assembly emitted for all three binaries on both architectures.

The intervention is intentionally source-level rather than a compiler flag: `fnv_unrolled.mojo` spells out offsets 0 through 31 explicitly. That makes it possible to test whether removing the inner-loop control changes performance while preserving the exact arithmetic dependency chain.

## Correctness

Every measured execution of all three implementations on both architectures produced the same checksum:

`11482223147755189951`

No timing is interpreted without that agreement.

## Results

### Linux x86_64

| Implementation | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| Mojo counted loop | 0.072859 s | 0.072335 s | 0.069039 s | 0.080786 s |
| Mojo manual unroll | 0.055942 s | 0.055356 s | 0.052503 s | 0.062149 s |
| C `-O3` | 0.054385 s | 0.054099 s | 0.053152 s | 0.055648 s |

- Manual unrolling reduced Mojo mean time by **23.2%** and median time by **23.5%** relative to the counted-loop Mojo variant.
- The unrolled Mojo variant was only **2.9% slower by mean** and **2.3% slower by median** than C in this run.
- One slower unrolled-Mojo trial (`0.062149 s`) makes the mean less stable than the median, but both estimators show the same large intervention effect.

The C absolute time on this shared x86_64 runner is materially lower than the previous day's run, so this experiment does **not** use cross-day absolute values as evidence. The controlled within-run counted-versus-unrolled comparison is the relevant result.

### Linux arm64

| Implementation | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| Mojo counted loop | 0.074713 s | 0.074756 s | 0.074569 s | 0.074780 s |
| Mojo manual unroll | 0.055040 s | 0.055013 s | 0.054997 s | 0.055197 s |
| C `-O3` | 0.054778 s | 0.054760 s | 0.054742 s | 0.054853 s |

- Manual unrolling reduced Mojo mean time by **26.3%** and median time by **26.4%**.
- Counted-loop Mojo was **36.4% slower than C by mean**, reproducing the earlier arm64 differential.
- After manual unrolling, Mojo was only **0.48% slower by mean** and **0.46% slower by median** than C.

The arm64 measurements are exceptionally tight across all seven trials, so the intervention almost completely closes the previously reproducible fixed-width gap on this architecture.

## Codegen verification

The assembly confirms that the source intervention produced the intended hot-loop change rather than merely timing two syntactically different programs that compiled the same way.

### x86_64 counted-loop Mojo

The hot hash body retains per-byte loop control:

```text
movzbl  (%rsi,%r8), %r9d
xorq    %r9, %rdi
imulq   %rcx, %rdi
incq    %r8
cmpq    $32, %r8
jne     .LBB0_7
```

### x86_64 manually unrolled Mojo

The hot region is a straight chain of loads/XORs/multiplies at fixed offsets 0–31. There is no inner `cmp`/`jne`; only the outer hash-iteration control remains. This now has the same high-level loop shape as clang's C output.

### arm64 counted-loop Mojo

The corresponding inner control is visible as:

```text
add     x12, x12, #1
cmp     x12, #32
eor     x14, x14, x15
mul     x14, x14, x10
b.ne    .LBB0_7
```

### arm64 manually unrolled Mojo

The hot region becomes fixed-offset `ldrb` + `eor` + `mul` operations with no per-byte conditional branch; the final arithmetic can also be folded into surrounding instructions. Again, this matches the structural property observed in clang's fully unrolled C hash chain.

## Interpretation

This is the causal follow-up that September 12's assembly comparison required. For this fixed-trip 32-byte FNV workload, **the missing loop transformation was not merely correlated with the gap: forcing equivalent unrolling in Mojo removes roughly one quarter of Mojo's runtime and nearly eliminates the arm64 Mojo-vs-C differential.**

The result is especially strong on arm64 because three observations line up:

1. the counted-loop variant reproduces the prior ~36% Mojo/C gap;
2. the intervention removes exactly the per-byte counted-loop branch structure identified in assembly;
3. the unrolled variant lands within about half a percent of C with identical checksums.

On x86_64 the same intervention is also large (~23%), but shared-runner absolute C timing moved enough across days that only the within-run intervention should be treated as durable evidence.

## What this does not prove

This does **not** establish that manual unrolling is the right fix for Category C or D, or that loop control explains their entire real-world gap. Their keys have variable lengths and their timed regions also contain parsing, delimiter scanning, probing, equality checks, aggregation and I/O. A 32-byte compile-time-fixed microkernel deliberately removes those confounders.

It also does not justify changing canonical Apple M4 Pro benchmark results. This is a Linux shared-runner microexperiment used to test one compiler/codegen mechanism.

The next useful Category C/D work is therefore still profiling or pass/codegen inspection of the real parser/hash/probe path, but with a sharper lesson: when a hot loop has a statically knowable or specializing trip count, verify whether Mojo and the comparator perform the same loop transformation before attributing the cost to the arithmetic itself.

## Conclusion

**Hypothesis confirmed for the fixed-width kernel.** Mojo 1.0's retained 32-iteration counted loop is a material cause of the isolated FNV gap. Replacing only that loop with 32 explicit operations makes Mojo about **23% faster on x86_64 and 26% faster on arm64**, and reduces the arm64 gap to C from roughly **36% to <0.5%** in the same run. Optimized assembly verifies that the per-byte branch was actually removed.

Canonical `ANALYSIS.md`, `results/results.json`, and charts remain unchanged.
