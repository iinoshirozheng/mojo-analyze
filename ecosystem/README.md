# Mojo Ecosystem Radar

Broad discovery of Mojo repositories, original articles, research papers, application domains, and meaningful ecosystem changes. Discovery breadth and independently verified research depth are separate goals.

## Editorial policy

Before each run, read and apply [RADAR_POLICY.md](RADAR_POLICY.md). Distinguish recent developments, newly discovered projects, and older technical reading; use diverse discovery routes; report search limitations; do not turn external performance claims into `mojo-analyze` results without reproduction.

## Daily briefs

| Date | Highlights | Research candidates |
|---|---|---|
| [2026-09-21](2026-09-21.md) | 24-entry radar: Sep-21 Mojo 1.2/MAX 26.7 nightly; stride-aware fusion alignment fix; recurrent-state index consistency; tuple match parsing; tokenizer, profiler, parser/compiler, Parquet, TLS, image and dataframe discoveries | Mojo 1.2 nightly Span scanner differential; Professor overhead calibration; Knap parity/perf replication; Parquet package-transition regression; Mojito parser differential |
| [2026-09-20](2026-09-20.md) | 24-entry radar: Sep-20 Mojo 1.2/MAX 26.7 nightly; pattern-match clustering; O(affix) String checks; prompt MAX leaf release; DuckDB, tokenization, geometry, PyTorch/MAX interop, hashing, ML and CLI discoveries | Mojo 1.0→1.1 Span scanner differential; String affix replication; DuckDB boundary decomposition; BPE flat-storage decode; Torch Mojo compile/cache boundary |
| [2026-09-19](2026-09-19.md) | 24-entry radar: Sep-19 Mojo 1.2/MAX 26.7 nightly; unified-closure GPU launch migration; workload-bounded model-input buffers; per-leaf KV cache coordination; benchmarking, scientific, bioinformatics, FFI/interoperability, Unicode, ML and geospatial discoveries | Category-D in-memory scanner codegen; Mojo 1.0→1.1 List growth; unified-closure launch codegen; Kelvin zero-cost check; R/Mojo ABI overhead |
| [2026-09-18](2026-09-18.md) | 24-entry radar: Mojo 1.1 / Modular 26.6 release details; cached custom-op execution and hidden transfer fixes; XML/Markdown, database, image, numerical, GUI, compression, scientific-ML and vector-compression discoveries | Category-D ingestion-vs-scan boundary; Mojo 1.1 List-growth differential; JSON structural index; custom-op cache key; FFI ABI oracle |
| [2026-09-17](2026-09-17.md) | 24-entry radar: Mojo 1.2/MAX 26.7 Sep-17 nightly; closure conversion and `Span` uninitialized-memory updates; Qwen3.5 state-row correctness; audio/DSP, graphics/FFI, physics, rendering, compression, ML and parsing discoveries | Category-D scanner-only cut; `Span` initialization policy; EmberJson structural index; raylib ABI oracle; FFT codegen |
| [2026-09-16](2026-09-16.md) | 24-entry radar: Mojo 1.2/MAX 26.7 Sep-16 nightly; atomic `.mojoc` cache publication; KV/TMA range safety; request-keyed RNG; scientific I/O, GPU ML, benchmarking, vector compression, parsing and tooling discoveries | Category-D parser-only decomposition; package-cache concurrency; HDF5 boundary costs; parser conformance; GPU launch decomposition |
| [2026-09-15](2026-09-15.md) | 24-entry radar: Mojo 1.2/MAX 26.7 Sep-15 nightly; `or`-pattern ref/lifetime fixes; Qwen3-VL video shape-contract repair; tooling, shader translation, parsers, agent systems, testing and networking discoveries | Category-D parse+hash decomposition; Tree-sitter conformance; YAML-Lite replication; WebSocket codec; package artifact compatibility |
| [2026-09-14](2026-09-14.md) | 24-entry radar: Mojo 1.2/MAX 26.7 Sep-14 nightly; `__match`/`hlcf.match` e2e support; latent sparse attention; broad discoveries spanning native agent/network stacks, compiler/game/database experiments, SIMD, audio, imaging and testing | real Category-D variable-length FNV unroll; Mojo 1.x sorting network; SSE/chunked parser; RESP codec; GPU power/transfer provenance |
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