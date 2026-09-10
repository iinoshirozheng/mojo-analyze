# Mojo Ecosystem Radar

Broad discovery of Mojo repositories, original articles, research papers, application domains, and meaningful ecosystem changes. Useful sources need not map to today's benchmark experiment; discovery breadth and independently verified research depth are separate goals.

## Editorial and discovery policy

Before authoring a new brief, read and apply [RADAR_POLICY.md](RADAR_POLICY.md). The full-report target is 20–30 distinct entries, normally including 12–16 repositories and 6–10 original reading selections, with official updates when meaningful. These are quality-controlled targets, not quotas to fill with fabricated news or repetitive links.

Distinguish **recent developments**, **newly discovered projects**, and **older technical reading**. Aim for diverse owners and application domains rather than repeatedly checking only the watchlist below. Report actual coverage and search limitations. The integrated research phase still selects exactly one verifiable task, followed by one engineering-knowledge capture gate.

The scheduled Mojo workflow is expected to read this policy from `main` before its ecosystem phase so later policy revisions take effect without copying the full discovery rules into each daily brief.

## Daily briefs

| Date | Highlights | Research candidates |
|---|---|---|
| [2026-09-10](2026-09-10.md) | 24-entry radar: Sep-10 Mojo/MAX nightly, comptime `nextafter`, iterable `Counter`; 12 repo profiles spanning regex, BLAS, Intel GPU, audio, 3DGS, FFI, benchmarking and GPU dataframes | Category D Mojo slot-storage differential; ExtraMojo SIMD bytes; mojo-regex comptime work placement; controlled join workload; BenchSuite estimator cross-check |
| [2026-09-09](2026-09-09.md) | 24-entry radar: Sep-9 Mojo 1.1/MAX 26.6 nightly, `hlcf.elif` canonicalizers, safer Array init idiom; 12 fresh repo profiles spanning CLI, terminal, numerics, GUI, notebooks, crypto and Kafka | Rust Sieve bounds-check codegen; `fill_with_unrolled` codegen; ArgMojo compile cost; MatMojo static/dynamic codegen; Thistle primitive replication |
| [2026-09-08](2026-09-08.md) | 26-entry broad radar: 16 repo profiles + 10 readings; new evening discoveries include BlazeSeq bioinformatics, Larecs ECS, Linamo linear algebra and mojolearn cross-vendor GPU ML | shared-runner estimator sensitivity; Decimo carry chains; BlazeSeq ownership modes; Larecs archetype iteration; Linamo static/dynamic codegen |
| [2026-09-07](2026-09-07.md) | Mojo 1.1/MAX 26.6 Sep-7 nightly; compiler `hlcf.if`→`hlcf.elif` consolidation; `mojo-http` quiet-machine/variance/drift benchmark guards | stable-vs-nightly branch differential; shared-runner estimator sensitivity; C/D hash-gap codegen profiling; fixed-width hash workload |
| [2026-09-06](2026-09-06.md) | `mojo-http` ring handoff + lost-wake/order fixes; `wgpu-mojo` 0.2.1 packaging/ABI provenance; official-nightly status corrected by Sep-7 evidence | Rust Category C hasher cost; wake-credit correctness; benchmark provenance sidecar; WebGPU phase decomposition |
| [2026-09-05](2026-09-05.md) | official tree quiet; `mojo-http` spawn workers + accept sharing; `mojo.httpx` benchmark architecture + async TLS lowering; `OfflinePoly.mojo` | controlled-host regression baselines; coroutine inline/no-inline probe; worker-distribution contract; fork-vs-spawn interop; geometry primitive |
| [2026-09-04](2026-09-04.md) | official tree quiet; `mojo.httpx` codec/proxy FFI; `mojo-http` GIL-detach performance; `wgpu-mojo`; `mojo-xml` toolchain-drift CI pattern | stable+nightly differential; Mojo↔Python boundary cost; streaming codec FFI; WebGPU dispatch/readback |
| [2026-09-03](2026-09-03.md) | Mojo 1.1 nightly line; quantified Modular GPU kernel changes; HTTP client/server activity; Mojo async lowering probes; MojoVec | stable-vs-nightly differential; async compiler probes; GPU useful-work density/determinism; vector-search SIMD |
| [2026-09-02](2026-09-02.md) | Mojo 1.0 + open compiler/toolchain; SIMD/GPU JSON, DuckDB GPU offload, Arrow/Marrow, LLM training, portability/FFI projects | structural JSON scan; GPU crossover curves; Mojo 1.x longitudinal history; KGEN/codegen tracing |

## Persistent watchlist

This list preserves earlier research leads; it is not an exhaustive source list or a substitute for fresh discovery. Unchanged watchlist items should not dominate a new brief or count toward its source targets.

- Mojo / Modular releases, compiler and standard-library changes
- Mojo 1.1 nightly → stable transition and performance/codegen deltas
- exact nightly package revision as a first-class benchmark provenance field
- `hlcf.if` → `hlcf.elif` compiler canonicalization and downstream branch/codegen effects
- KGEN/compiler work affecting optimization, CPU SIMD, GPU lowering, ownership or memory safety
- stable canonical toolchain + advisory latest-nightly drift testing
- controlled-host performance regression baselines kept separate from noisy shared CI
- benchmark artifact provenance tied to exact source/toolchain/parameters
- machine-quietness, variance and comparator-drift checks as benchmark-validity dimensions
- async/coroutine lowering regressions surfaced by real networking libraries
- MAX and cross-vendor accelerator developments, especially persistent-kernel and cross-block cooperation patterns
- `mojo.httpx`, `mojo-http`, `flare` and other serious networking/FFI projects
- wake-credit / parked-worker invariants in ring + notification designs
- Python runtime/GIL/thread-state boundary costs in Mojo interoperability
- fork vs fresh-exec/spawn semantics when Mojo embeds stateful foreign runtimes
- accepted-connection ownership/fairness in multiprocess networking
- substantial Mojo systems/data/graphics/game-engine projects
- `wgpu-mojo` as an external WebGPU/graphics/compute substrate watch; 0.2.1 is the first channel-installable baseline
- native FFI ABI pins as distinct from package semantic-version compatibility
- `marrow` and other data systems that expose hashing/semantic-correctness tradeoffs
- MojoVec and other real-world SIMD/vector-search implementations
- `OfflinePoly.mojo` and other geometry/combinatorics applications as sources of non-string benchmark primitives
- reproducible external benchmark suites worth independently replicating
- FFI and interoperability projects that expose measurable boundary costs
- projects that reveal CPU-vs-GPU crossover behavior rather than only peak GPU numbers
- BlazeSeq and other bioinformatics pipelines exposing zero-copy versus owned/batched tradeoffs
- Larecs and other ECS/game-runtime work exposing archetype/SIMD/scheduler costs
- Linamo/NuMojo numerical-library design and codegen tradeoffs
- mojolearn and other cross-vendor GPU projects with explicit numerical reproducibility profiles
- ArgMojo and other Mojo-native developer tooling using compile-time validation/reflection
- scientific/statistical packages (`MSL`, `StaMojo`, `MatMojo`) where compatibility and numerical-validation contracts are first-class
- private/internal compiler-interface dependencies such as `mojokernel`'s LLDB integration
- Thistle and other crypto projects where test vectors and side-channel/security boundaries matter more than headline throughput
- ExtraMojo, mojo-regex and other small libraries exposing isolated SIMD/comptime experiments
- MojoSplat / gsplat_mojo and other 3D rendering work exposing stage-level GPU and interop boundaries
- mojo-bindgen and other FFI generators where ABI layout validation is a first-class correctness gate
- MXFrame and other GPU query/dataframe projects exposing cardinality/skew and transfer/setup tradeoffs

The radar favors inspectable technical substance over stars or novelty alone. Early-stage prototypes and educational implementations are welcome when their distinctive idea and maturity are explained. Becoming a verified benchmark result requires a separate fair experiment and an appropriate correctness contract; appearing in the discovery collection does not.