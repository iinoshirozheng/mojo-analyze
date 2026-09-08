# Mojo Radar: broad discovery policy

Version: 0.2.0  
User-requested scope revision: 2026-09-08 (Asia/Taipei)

## Purpose

The radar is a broad Mojo ecosystem discovery publication, not just a changelog for a handful of known repositories or a feeder for the current five benchmark categories. Give the reader more distinct projects, original articles, unfamiliar application domains, and technical ideas.

Separate two objectives:

1. **Discovery breadth:** survey broadly and publish a useful source collection.
2. **Research depth:** the integrated workflow subsequently completes exactly one verified experiment when feasible.

Do not reject an interesting repository, prototype, article, or conference presentation merely because it cannot become today's experiment. Keep the existing research correctness rules and the single post-run Notion capture gate unchanged.

## 1. Three freshness lanes

Every published item belongs to a lane:

- **Recent development:** a dated release, substantive commit/PR, original article, or documented technical change. Check the event date, not just a search engine's crawl date. Default search horizon: 7 days; extend to 30 days when useful, with dates explicit.
- **New discovery:** a repository or source not covered recently, regardless of its age. Say 'newly discovered', not 'newly created', unless repository creation metadata proves the latter.
- **Technical reading/backlog:** an older article, paper, tutorial, talk, or design document worth studying. Show original publication/revision date and toolchain-era caveats. Unknown dates remain unknown.

A quiet release day is an opportunity for discovery and reading, not an excuse to repeatedly expand 'no changes' sections for the same projects.

## 2. Breadth targets, never fabrication quotas

Target **20–30 distinct editorial entries** in a full daily radar, normally combining:

| Section | Target |
|---|---:|
| New discoveries and meaningfully active repositories | 12–16 |
| Original articles, papers, tutorials, talks, or design write-ups | 6–10 |
| Important official release/compiler/stdlib/MAX developments | 0–4, only when evidenced |

These are quality-controlled targets, not guaranteed daily supply. If fewer good sources are verified after broad searching, publish the actual number and explain coverage gaps. Never inflate the count with mirror articles, release reposts, individual commits from one project, or weak filler.

Aim for at least **60% of entries from source identities not covered in the preceding 14 daily briefs**. Count canonical repository identities and canonical article identities, not raw URLs. Audit the available history; do not invent a novelty percentage when only the index was checked.

Aim for at least **8 independent repository owners** and **5 technical domains**, including at least 2 non-LLM/non-networking domains. The official changelog and repeatedly featured watchlist should normally occupy no more than roughly one third of the report. Important breaking changes can override the mix, with the reason stated.

## 3. Discovery must precede watchlist maintenance

Use at least five independent routes rather than checking only yesterday's names:

1. **Broad GitHub discovery:** language, topic, description and source-file searches; inspect recently created and recently pushed projects separately. Do not make stars the eligibility criterion. Distinguish a substantive fork from a content-identical mirror.
2. **Mixed-language discovery:** include repositories with meaningful `.mojo` sources, bindings, compiler tooling, runtimes, or Mojo-targeting transpilers even if their dominant language is Python, Rust, C/C++, or JavaScript.
3. **Official community package catalogs/channels:** inspect candidate repository sources and version requirements. A catalog entry is a lead, not proof of current buildability or project quality.
4. **Original-author publications and showcases:** community forum posts, independent developer blogs, project documentation, engineering reports, and conference material. Follow roundups to the original author/repo; do not count the same story twice.
5. **Research papers and artifacts:** compiler, numerical computing, HPC, databases, scientific applications, and programming-language work involving Mojo. Separate measured results from projections and abstract-only inspection from a full paper review.
6. **Reference expansion:** inspect links, dependencies, related projects, and package maintainers discovered during the current search to escape the existing watchlist.

Search with multiple domain-specific combinations, not only 'Mojo latest'. Examples of useful topic combinations: Mojo ray tracing/BVH, game/physics/ECS, audio/FFT/DSP, geometry/simulation, database/Arrow/serialization, bioinformatics/alignment/FASTQ, numerical/BigInt/decimal, FFI/bindgen/libclang, R/Julia/Python interoperability, and test/profiler/compiler tooling.

Balance recent 7/30-day discovery with an explicitly labeled undated/older exploration pass. Rotate underserved domains across the week. Never claim a complete GitHub search after a timeout, missing page, or restricted search. Record the limitation and use another route.

## 4. Domain coverage

Across the week, include:

- language/compiler/stdlib/tooling;
- MAX, accelerator kernels, model architectures and distributed compute;
- databases, dataframes, parsing, serialization and storage;
- systems, networking, concurrency and runtime integration;
- graphics, rendering, games, GUI/TUI and physics;
- audio/video, image processing and signal processing;
- numerical/scientific computing, simulation and bioinformatics;
- interoperability, bindings, developer tools and learning material.

Do not let benchmarks about hashing, Sieve, or HTTP become the only lens through which projects are selected. Early-stage demos are eligible when they contain inspectable technical work or a distinctive idea; label maturity instead of excluding them categorically.

## 5. Verification and per-item metadata

Read the actual selected source. For repository-specific technical claims, inspect the README plus the relevant code, example, manifest, commit, test or design document as needed. Clearly mark when only documentation or a commit message was inspected.

Each profile should include:

- canonical name, repository/source URL, author/owner, technical domain;
- freshness lane; event/publication date when known; observed date;
- what the project/article actually does and what is distinctive;
- what changed since prior coverage, or why it is newly worth discovering;
- maturity and important limitations, including pinned/unknown toolchain compatibility;
- evidence level: documentation inspected, implementation inspected, author-reported measurement, or independently reproduced;
- a useful learning angle; an experiment idea is optional for every item but required for the final shortlist.

Never describe a wrapper over FFmpeg/BLAS/libclang as a pure-Mojo reimplementation of that dependency. Never promote prototype support to full language compatibility. Do not treat successful compilation, a screenshot, star counts, or checksum agreement alone as proof of performance quality.

Include direct canonical links and, for material recent changes, immutable commit/PR/release links when available. Explicitly distinguish author performance claims from `mojo-analyze` measurements. Do not change benchmark conclusions from external news.

## 6. Deduplication and presentation

Read the available previous 14 briefs, not just their summaries, before reporting a novelty metric. Normalize renamed repositories and article mirrors. Count a multi-part series as one discovery unless separate parts address independently substantial questions; disclose the counting choice.

One main profile per repository per day. Group related commits under it. Previously covered projects reappear only for substantive new work or an explicitly different technical deep dive. Unchanged watchlist status belongs in a compact appendix and does not count toward source targets.

Use this structure:

1. **Coverage summary:** actual entry counts, owners/domains, measured novelty if audited, search horizons, limitations.
2. **Important current developments:** verified dates, with no forced filler on quiet days.
3. **Repository discoveries:** broad, grouped by technical domain.
4. **Articles and technical reading:** original authors, dates, why to read.
5. **Three to five deep-dive picks:** synthesize selected entries rather than counting them again.
6. **Research candidates:** a short ranked shortlist; exactly one is selected in the separate research phase.
7. **Compact watchlist delta and search audit:** routes attempted, failed searches, unresolved verification.

The chat response may highlight selected entries but must clearly give the full report location and actual total. Do not reduce a broad source collection to a three-item chat summary without making the rest accessible.

## 7. Repository and integration boundaries

Keep `ecosystem/YYYY-MM-DD.md` and the reverse-chronological `ecosystem/README.md`. A same-day rerun should merge substantive additions and corrections without deleting prior useful coverage or duplicating entries. Commit the brief and index together when possible, preserving concurrent changes and never force-pushing.

This policy governs the radar phase only. Preserve the integrated workflow's one-experiment limit, checksum/methodology requirements, and a single final engineering-knowledge gate. Raw sources and daily discoveries do not automatically become Notion Knowledge Nodes. Preserve the existing name/Aliases deduplication, provenance, Draft/Verified evidence thresholds, and automated-write metadata.

**Scheduler binding:** committing this file does not edit or verify a ChatGPT scheduled task. To make its use explicit in that task, its instructions must tell the runner to read and apply `ecosystem/RADAR_POLICY.md` on `main` before Phase 1, while preserving Phases 2 and 3. Do not report that the scheduler was updated unless an actual scheduler update succeeded.
