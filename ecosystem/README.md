# Mojo Ecosystem Radar

Daily notes on technically meaningful developments in the Mojo ecosystem, with an emphasis on ideas that can turn into reproducible experiments for `mojo-analyze`.

## Daily briefs

| Date | Highlights | Research candidates |
|---|---|---|
| [2026-09-03](2026-09-03.md) | Mojo 1.1 nightly line; quantified Modular GPU kernel changes; HTTP client/server activity; Mojo async lowering probes; MojoVec | stable-vs-nightly differential; async compiler probes; GPU useful-work density/determinism; vector-search SIMD |
| [2026-09-02](2026-09-02.md) | Mojo 1.0 + open compiler/toolchain; SIMD/GPU JSON, DuckDB GPU offload, Arrow/Marrow, LLM training, portability/FFI projects | structural JSON scan; GPU crossover curves; Mojo 1.x longitudinal history; KGEN/codegen tracing |

## Persistent watchlist

- Mojo / Modular releases, compiler and standard-library changes
- Mojo 1.1 nightly → stable transition and performance/codegen deltas
- KGEN/compiler work affecting optimization, CPU SIMD, GPU lowering, ownership or memory safety
- async/coroutine lowering regressions surfaced by real networking libraries
- MAX and cross-vendor accelerator developments, especially persistent-kernel and cross-block cooperation patterns
- `mojo.httpx` connection-pool work and `mojo-http` releases
- substantial Mojo systems/data/graphics/game-engine projects
- MojoVec and other real-world SIMD/vector-search implementations
- reproducible external benchmark suites worth independently replicating
- FFI and interoperability projects that expose measurable boundary costs
- projects that reveal CPU-vs-GPU crossover behavior rather than only peak GPU numbers

The radar intentionally favors substantive technical activity over stars, novelty alone, or toy repositories. Findings should become benchmark candidates only after they can be reduced to a fair, checksum-verifiable experiment.
