# Mojo Ecosystem Radar

Broad discovery of Mojo repositories, original articles, research papers, application domains, and meaningful ecosystem changes. Discovery breadth and independently verified research depth are separate goals.

## Editorial policy

Before each run, read and apply [RADAR_POLICY.md](RADAR_POLICY.md). Distinguish recent developments, newly discovered projects, and older technical reading; use diverse discovery routes; report search limitations; do not turn external performance claims into `mojo-analyze` results without reproduction.

## Daily briefs

| Date | Highlights | Research candidates |
|---|---|---|
| [2026-09-13](2026-09-13.md) | 24-entry radar: Mojo 1.2/MAX 26.7 Sep-13 nightly; KDA golden oracle; fused EP dispatch/layout; 12 fresh repo discoveries spanning Safetensors, protobuf/gRPC, Arrow/Polars, Gaussian processes, build/reflection tooling, date-time, Vulkan and interop | manually unrolled fixed-FNV causal probe; Float64 oracle hierarchy; Safetensors mmap/access decomposition; protobuf fixed-schema codec; Python↔Mojo conversion boundary |
| [2026-09-12](2026-09-12.md) | 24-entry radar: Mojo 1.2/MAX 26.7 nightly; `@inline` migration; stride-correct advanced fusion; scientific ML, parsers, crypto, serverless, FFI, graphics and geometry | fixed-FNV cross-arch codegen; CSV SIMD tokenizer; 1.0→1.2 inline migration; skew-sensitive probing; stride-correctness fixture |
| [2026-09-11](2026-09-11.md) | 24-entry radar: Sep-11 Mojo/MAX nightly and 1.1 release-branch cut; Iceberg/storage, GPU ML, HPC, vision, compression, parsing, image processing and tooling | fixed-width FNV differential; CRC32 micro-workload; compile-time specialization cost; parity-oracle methodology; image-pipeline fusion |
| [2026-09-10](2026-09-10.md) | 24-entry radar: Sep-10 nightly, comptime `nextafter`, iterable `Counter`; regex, BLAS, Intel GPU, audio, 3DGS, FFI, benchmarking and GPU dataframes | Category D raw slots; ExtraMojo SIMD bytes; regex comptime work placement; controlled join; estimator cross-check |
| [2026-09-09](2026-09-09.md) | 24-entry radar: Sep-9 nightly, `hlcf.elif` canonicalizers, safer Array init; CLI, terminal, numerics, GUI, notebooks, crypto and Kafka | Rust Sieve bounds-check codegen; `fill_with_unrolled`; ArgMojo compile cost; MatMojo codegen; Thistle primitive |
| [2026-09-08](2026-09-08.md) | 26-entry broad radar: BlazeSeq bioinformatics, Larecs ECS, Linamo linear algebra, mojolearn cross-vendor GPU ML, plus graphics/audio/FFI/tooling | estimator sensitivity; Decimo carry chains; BlazeSeq ownership modes; Larecs iteration; Linamo codegen |
| [2026-09-07](2026-09-07.md) | Sep-7 Mojo 1.1/MAX 26.6 nightly; `hlcf.if`→`hlcf.elif`; benchmark environment guards | stable-vs-nightly branch differential; estimator sensitivity; hash-gap profiling; fixed-width hash workload |
| [2026-09-06](2026-09-06.md) | `mojo-http` ring handoff/lost-wake fixes; `wgpu-mojo` packaged baseline | Rust hasher cost; wake-credit correctness; provenance sidecar; WebGPU phase decomposition |
| [2026-09-05](2026-09-05.md) | server multiprocessing/accept sharing; HTTP benchmark architecture; async TLS lowering; OfflinePoly | controlled-host baselines; coroutine probe; worker distribution; fork-vs-spawn; geometry primitive |
| [2026-09-04](2026-09-04.md) | codec/proxy FFI; GIL-detach performance; WebGPU; stable/nightly CI pattern | compiler differential; Python boundary; codec FFI; WebGPU dispatch/readback |
| [2026-09-03](2026-09-03.md) | Mojo 1.1 nightly starts; MoE/persistent GPU work; HTTP async probes; MojoVec | stable/nightly lane; async probes; GPU useful-work density; vector-search SIMD |
| [2026-09-02](2026-09-02.md) | Mojo 1.0 + open compiler; SIMD/GPU JSON, DuckDB, Arrow/Marrow, LLM training, portability/FFI | structural JSON scan; GPU crossover; Mojo 1.x history; KGEN tracing |

## Persistent themes

- stable canonical Mojo 1.0 results versus advisory 1.2/nightly drift checks, with exact toolchain provenance;
- KGEN/pass-level and hot-region assembly inspection before attributing source-level performance gaps;
- benchmark correctness beyond checksums: numerical oracles, external conformance suites, determinism and layout/stride fixtures;
- data movement, transfer, layout conversion, FFI and runtime ownership as first-class benchmark costs;
- shared-runner evidence kept distinct from controlled-host regression gates;
- architecture-specific behavior verified separately on x86_64, arm64 and relevant GPU targets;
- diverse workloads beyond HTTP/LLM: data systems, graphics, audio, bioinformatics, numerical/scientific, game/runtime, serialization and developer tooling;
- mixed-language repositories and generated bindings included when they materially extend Mojo workflows;
- external author benchmarks treated as replication candidates, not copied conclusions;
- raw ecosystem news becomes a research candidate only after it can be reduced to one fair, independently verifiable experiment.
