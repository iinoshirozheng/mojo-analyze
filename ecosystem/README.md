# Mojo Ecosystem Radar

Daily notes on technically meaningful developments in the Mojo ecosystem, with an emphasis on ideas that can turn into reproducible experiments for `mojo-analyze`.

## Daily briefs

| Date | Highlights | Research candidates |
|---|---|---|
| [2026-09-07](2026-09-07.md) | Mojo 1.1/MAX 26.6 Sep-7 nightly; compiler `hlcf.if`→`hlcf.elif` consolidation; `mojo-http` quiet-machine/variance/drift benchmark guards | stable-vs-nightly branch differential; shared-runner estimator sensitivity; C/D hash-gap codegen profiling; fixed-width hash workload |
| [2026-09-06](2026-09-06.md) | `mojo-http` ring handoff + lost-wake/order fixes; `wgpu-mojo` 0.2.1 packaging/ABI provenance; official-nightly status corrected by Sep-7 evidence | Rust Category C hasher cost; wake-credit correctness; benchmark provenance sidecar; WebGPU phase decomposition |
| [2026-09-05](2026-09-05.md) | official tree quiet; `mojo-http` spawn workers + accept sharing; `mojo.httpx` benchmark architecture + async TLS lowering; `OfflinePoly.mojo` | controlled-host regression baselines; coroutine inline/no-inline probe; worker-distribution contract; fork-vs-spawn interop; geometry primitive |
| [2026-09-04](2026-09-04.md) | official tree quiet; `mojo.httpx` codec/proxy FFI; `mojo-http` GIL-detach performance; `wgpu-mojo`; `mojo-xml` toolchain-drift CI pattern | stable+nightly differential; Mojo↔Python boundary cost; streaming codec FFI; WebGPU dispatch/readback |
| [2026-09-03](2026-09-03.md) | Mojo 1.1 nightly line; quantified Modular GPU kernel changes; HTTP client/server activity; Mojo async lowering probes; MojoVec | stable-vs-nightly differential; async compiler probes; GPU useful-work density/determinism; vector-search SIMD |
| [2026-09-02](2026-09-02.md) | Mojo 1.0 + open compiler/toolchain; SIMD/GPU JSON, DuckDB GPU offload, Arrow/Marrow, LLM training, portability/FFI projects | structural JSON scan; GPU crossover curves; Mojo 1.x longitudinal history; KGEN/codegen tracing |

## Persistent watchlist

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

The radar intentionally favors substantive technical activity over stars, novelty alone, or toy repositories. Findings should become benchmark candidates only after they can be reduced to a fair, checksum-verifiable experiment.
