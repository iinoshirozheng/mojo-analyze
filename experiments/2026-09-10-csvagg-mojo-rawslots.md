# Category D Mojo slot-storage differential — 2026-09-10

## Research question

Does replacing Category D's five fixed-capacity `List` hash-table slot arrays with raw-pointer storage materially reduce Mojo's CSV aggregation time, while leaving parsing, byte-span keys, FNV-1a hashing, open addressing, aggregation, and the output contract unchanged?

This is a falsification-oriented follow-up to the Category C raw-slot experiment. Category C had already shown that the same representation change was only ~1.9% faster on Linux x86_64 and ~1.5% slower on Linux arm64, so Category D needed its own controlled measurement rather than assuming `List` storage explained the remaining Mojo-vs-C gap.

## Controlled change

Canonical implementation: `benchmarks/csvagg/csvagg.mojo`.

Experimental implementation: `benchmarks/csvagg/csvagg_rawslots.mojo`.

The experimental variant changes only the five `CAPACITY = 1024` slot arrays:

- `slot_used`
- `slot_hash`
- `slot_start`
- `slot_end`
- `slot_revenue`

Canonical storage uses fixed-length `List[...]` values initialized to false/zero. The experimental version uses `unsafe_alloc[...]` plus `unsafe_offset` indexing and explicitly zero-initializes all five allocations inside the timed region. Deallocation remains outside the timed region, matching the canonical program's destructor timing. The parser, input bytes, category span representation, FNV-1a function, probe sequence, equality check, aggregation logic, top-category tie-breaking, and checksum are unchanged.

Harness: `scripts/bench_csvagg_mojo_rawslots.py`.

## Verification method

Valid evidence comes from GitHub Actions run **34465076912** on commit `55e46bbe044077f8f838fa887e31a78236e12a11`:

- Linux x86_64: GitHub-hosted Ubuntu 24.04, runner archspec `zen2`
- Linux arm64: GitHub-hosted Ubuntu 24.04, runner archspec `neoverse_n2`
- Mojo 1.0.0 / `mojo-compiler` 1.0.0; MAX 26.5.0 from the repository's locked Pixi environment
- 2 warmups + 7 measured trials for each variant on each architecture
- exact checksum gate before accepting timings
- `mojo build --emit asm` for both variants on both architectures

All 28 measured executions across the two implementations and two architectures produced the same checksum:

`10000000:99:electronics:5073122132805`

Artifacts from the valid run:

- x86_64: artifact `10147184624`, archive SHA-256 `90d84974fc47d4e02ef7d788310ae2dd127e2b169f3210c67f1395c853072444`
- arm64: artifact `10147183293`, archive SHA-256 `65939b7bc4425958c372e9108acbba8687ba13fb325128e7ac67c5dc7ebd304c`

Workflow: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/34465076912

### Discarded first attempt

An earlier measurement from run `34464574496` is intentionally **not** evidence for the conclusion. The first raw-pointer variant used the deprecated bare `alloc` API and initialized only `slot_used`, while the canonical `List` construction initializes every slot array. That made startup work less closely controlled and introduced compiler warnings. The variant was corrected to `unsafe_alloc` and explicit zero initialization of all five arrays before the valid run above. The earlier timings are discarded rather than averaged with the corrected experiment.

## Results

| Architecture | `List` mean | Raw-slot mean | `List` median | Raw-slot median | Mean effect |
|---|---:|---:|---:|---:|---:|
| Linux x86_64 | 1.070113 s | 1.024702 s | 1.069808 s | 1.024825 s | raw-slot **4.24% lower time** (`List/raw = 1.0443x`) |
| Linux arm64 | 1.278844 s | 1.290453 s | 1.279587 s | 1.287355 s | raw-slot **0.91% higher time** (`List/raw = 0.9910x`) |

Measured standard deviations:

- x86_64 `List`: 0.001967 s; raw-slot: 0.002543 s
- arm64 `List`: 0.006172 s; raw-slot: 0.005986 s

The x86_64 direction is internally consistent between mean and median (~4.2% lower raw-slot time). The arm64 direction is also internally consistent but very small: the raw-slot median is ~0.61% slower and its mean is ~0.91% slower. On a shared runner, the arm64 result is treated as **no material benefit**, not as evidence that raw pointers are intrinsically slower.

## Assembly inspection

The raw-slot binaries are structurally smaller, but this observation is deliberately not over-interpreted as a direct count of removed hot-loop bounds checks:

| Architecture | `List` assembly | Raw-slot assembly | Line change |
|---|---:|---:|---:|
| x86_64 | 464,925 bytes / 14,078 lines | 456,627 bytes / 13,795 lines | -283 lines |
| arm64 | 450,734 bytes / 13,304 lines | 444,494 bytes / 13,062 lines | -242 lines |

Whole-binary references to Mojo's `check_bounds::do_asserts` helper are unchanged (27 occurrences in each x86_64 assembly and 24 in each arm64 assembly), because the programs still use bounds-checked collections for input and other work. Therefore whole-binary helper counts cannot isolate slot-array checks. The representation change clearly alters generated code, but this experiment does **not** claim that every saved instruction is a removed slot bounds check or that binary-size reduction explains the timing delta.

Assembly SHA-256:

- x86_64 `List`: `6474b3a08f80d037ed235152ad1a9af21b9aba03e4a6e581ab7022662b8aa135`
- x86_64 raw-slot: `a48548e94e67a00aa95be3e95ceb2458980d6a168258c98e49661ec584af6113`
- arm64 `List`: `e73b3afc25bb15e358f38e9831ec5fc5f9d0d97baa7fa21fdb073bfb17099938`
- arm64 raw-slot: `0ab671b6c6bc4123c70658bfe0fe4d8e1e6879500c32f0378ddc75dd09fc55a3`

## Conclusion

**Reject the hypothesis that Category D's fixed-capacity `List` slot storage is the primary cause of Mojo's remaining gap.** The exact same storage intervention is modestly favorable on this x86_64 runner (~4.2% by mean/median) and neutral-to-slightly-negative on this arm64 runner. That is far smaller and less portable than the roughly multi-fold canonical Mojo-vs-C Category D gap documented in `ANALYSIS.md`.

The useful result is therefore mostly causal narrowing:

1. raw slot storage can remove a small amount of cost on some targets;
2. it is not a cross-architecture explanation for the benchmark's dominant performance difference;
3. a future Category D investigation should profile or inspect the parser/hash/probe hot path before another storage rewrite;
4. low-level representation wins observed in one workload or architecture should not be transferred to another without an otherwise-identical control.

Because these are shared-runner experiment numbers, this run does **not** modify canonical `results/results.json`, charts, or the headline timings in `ANALYSIS.md`.
