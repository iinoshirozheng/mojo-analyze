# Rust Sieve: does removing the hot-write bounds check explain the gap?

Date: 2026-09-02

## Research question

Category B's current Rust implementation trails C/Mojo, and `CONTRIBUTING.md`
listed a concrete hypothesis: Rust's checked `is_prime[j] = false` marking
write might be paying enough bounds-check overhead to explain a meaningful
part of that gap.

This experiment isolates exactly that question. It does **not** replace the
canonical safe-Rust result.

## Change

Added `rust/src/bin/sieve_unsafe.rs`, byte-for-byte equivalent in algorithm and
data representation to the existing Rust sieve except for the hottest marking
write:

```rust
unsafe {
    *is_prime.get_unchecked_mut(j) = false;
}
```

The surrounding loop guarantees `j <= limit`, while the vector length is
`limit + 1`. Reads, allocation, counting, checksum calculation, compiler
profile, workload size, and every other operation remain unchanged.

A focused CI harness runs safe and unsafe binaries separately with 2 warmups +
7 measured trials at `limit = 50_000_000`. The harness refuses the result if
checksums differ.

Workflow run: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/33638577387

## Verification

Both Linux architectures compiled successfully and produced the identical
checksum in every run:

`3001134:548121944`

| Linux runner | Safe Rust mean | Unsafe marking-write mean | Safe / unsafe | Result |
|---|---:|---:|---:|---|
| x86_64 | 0.209036 s | 0.209133 s | 0.9995x | no measurable win |
| arm64 | 0.189772 s | 0.185632 s | 1.0223x | ~2.2% win |

Seven-trial dispersion also does not support a large hidden effect. On x86_64
the unsafe mean is effectively identical (very slightly slower); on arm64 the
improvement is real-looking but small relative to the previously observed
Rust-vs-C/Mojo gap.

## Conclusion

**The original bounds-check explanation is not supported as the primary cause
of Rust's category-B deficit on Linux.** Removing only the hot marking-write
bounds check gives essentially zero improvement on x86_64 and about 2.2% on
arm64. That is far too small to explain the full ranking gap.

This is a useful negative result: a future Rust investigation should not simply
replace more indexing with `unsafe` and then assume any remaining difference is
"safe Rust overhead." Better next checks are generated assembly/codegen,
allocation/initialization cost, loop transformation/vectorization, and whether
LLVM already proves/removes the safe write's bounds check on x86_64.

The canonical benchmark and `ANALYSIS.md` numbers are intentionally unchanged:
these measurements come from shared GitHub-hosted Linux runners, while the
primary published table uses the controlled macOS machine. The experiment is
kept as causal evidence, not substituted into the main scoreboard.
