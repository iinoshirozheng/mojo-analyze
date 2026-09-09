# Rust Sieve bounds-check codegen — 2026-09-09

## Research question

Does the bounds check on the canonical Rust Category-B Sieve marking write survive optimized `rustc` codegen, and does removing only that check materially improve the benchmark?

This follows the focused 2026-09-02 experiment in [`2026-09-02-rust-sieve-unsafe.md`](2026-09-02-rust-sieve-unsafe.md). That experiment changed only

```rust
is_prime[j] = false;
```

to

```rust
unsafe { *is_prime.get_unchecked_mut(j) = false; }
```

and found no x86_64 win and a small arm64 win. The unresolved causal question was whether the optimizer had already removed the safe write's check.

## Method

Source variants:

- safe: `rust/src/bin/sieve.rs`
- unsafe marking write: `rust/src/bin/sieve_unsafe.rs`

Both were compiled on GitHub-hosted Linux x86_64 and arm64 with:

```text
rustc 1.98.1 (48a229cea 2026-09-01)
LLVM 22.1.8
rustc -C opt-level=3 -C codegen-units=1
```

The one-shot codegen probe emitted optimized LLVM IR and assembly for both variants. The existing timing harness also ran **2 warmups + 7 measured trials** at `--limit 50000000` on each architecture. The exact workflow run is:

- https://github.com/iinoshirozheng/mojo-analyze/actions/runs/34338872636

Correctness gate: every safe and unsafe execution produced the identical checksum:

```text
3001134:548121944
```

The one-shot workflow job was removed after collecting the artifacts; the existing source variants and timing harness remain reproducible.

## Codegen result: the hot safe write still has a bounds check

The hypothesis that optimized `rustc` had already eliminated the marking-write bounds check is **rejected** on both tested architectures.

### Optimized LLVM IR

The safe variant's marking loop contains an explicit `j < len` test before the store:

```llvm
%_75 = icmp ult i64 %j.sroa.0.071, %_4
br i1 %_75, label %bb31, label %panic6.invoke

bb31:
  %_21 = getelementptr inbounds nuw i8, ptr %85, i64 %j.sroa.0.071
  store i8 0, ptr %_21, align 1
```

The unsafe variant directly forms the address and stores:

```llvm
bb9:
  %j.sroa.0.067 = phi i64 ...
  %_73 = getelementptr inbounds nuw i8, ptr %85, i64 %j.sroa.0.067
  store i8 0, ptr %_73, align 1
```

The same structural difference appears in the optimized IR emitted on x86_64 and arm64.

A whole-file count of `panic_bounds_check` references is not sufficient by itself: both variants still contain other checked indexing operations. The decisive evidence is the check immediately surrounding this specific marking store.

### x86_64 assembly

Safe hot loop:

```asm
.LBB7_86:
    cmpq    %rbx, %rdi
    jae     .LBB7_91
    movb    $0, (%r14,%rdi)
    addq    %rcx, %rdi
    cmpq    %rax, %rdi
    jbe     .LBB7_86
```

Unsafe hot loop:

```asm
.LBB7_86:
    movb    $0, (%r14,%rsi)
    addq    %rcx, %rsi
    cmpq    %rax, %rsi
    jbe     .LBB7_86
```

Removing `get_unchecked_mut` therefore really does remove one compare plus a conditional branch from each marking iteration on this build.

### arm64 assembly

Safe hot loop:

```asm
.LBB7_75:
    cmp     x0, x20
    b.hs    .LBB7_89
    strb    wzr, [x21, x0]
    add     x0, x0, x8
    cmp     x0, x19
    b.ls    .LBB7_75
```

Unsafe hot loop:

```asm
.LBB7_75:
    strb    wzr, [x21, x9]
    add     x9, x9, x8
    cmp     x9, x19
    b.ls    .LBB7_75
```

Again, the unchecked variant removes the per-iteration compare/branch rather than merely changing source syntax.

## Timing cross-check

These are shared-runner measurements, so they are supporting evidence rather than new canonical benchmark numbers.

| Architecture | safe mean | unsafe mean | safe median | unsafe median | safe / unsafe mean |
|---|---:|---:|---:|---:|---:|
| Linux x86_64 | 0.251793 s | 0.255905 s | 0.248093 s | 0.253998 s | 0.9839x |
| Linux arm64 | 0.209173 s | 0.200217 s | 0.205965 s | 0.198080 s | 1.0447x |

On x86_64, the unchecked variant was about **1.6% slower by mean** in this run even though the extra check is unquestionably gone. Treat that as no demonstrated performance benefit, not as evidence that bounds checks are beneficial; the run-to-run noise is larger than a small effect of this size.

On arm64, the unchecked variant was about **4.5% faster by mean**. The earlier 2026-09-02 run also favored the unsafe variant on arm64, though by only about 2.2%, while x86_64 again showed effectively no win. The repeated direction makes a small arm64 benefit plausible, but it still does not account for the full language-level Category-B gap.

## Conclusion

**The safe Rust Sieve's hot marking bounds check survives `-O3` on both tested architectures.** The prior near-null x86_64 timing result was not caused by rustc proving the check redundant and deleting it.

At the same time, deleting the check is not a large universal optimization:

- x86_64 shows no repeatable win despite a visibly shorter inner loop;
- arm64 shows a small benefit in both focused runs;
- the same source-level safety check therefore has architecture-dependent performance impact.

The stronger reusable lesson is to inspect optimized IR/assembly before inferring performance cost from a source-level safety construct. Presence in codegen establishes that a cost *can* exist; only measurement establishes whether it is material on a particular microarchitecture and workload.

No canonical `ANALYSIS.md`, `results/results.json`, or benchmark implementation is changed from these shared-runner focused measurements.

## Reproduction references

- Safe source: `rust/src/bin/sieve.rs`
- Unsafe source: `rust/src/bin/sieve_unsafe.rs`
- Timing harness: `scripts/bench_sieve_rust_unsafe.py`
- Earlier timing note: `experiments/2026-09-02-rust-sieve-unsafe.md`
- Workflow run: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/34338872636
- Codegen artifacts from that run: `rust-sieve-codegen-x86_64` and `rust-sieve-codegen-arm64`
