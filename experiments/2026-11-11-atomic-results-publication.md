# 2026-11-11 — Atomic publication of validated benchmark snapshots

## One question
Can a failure while serializing or replacing `results/results.json` destroy the previous validated snapshot, even after checksum gates pass?

## Finding and intervention
Before this change, `scripts/bench.py` wrote the final JSON directly via `Path.write_text`, which opens/truncates the destination before completing the write. A process interruption, serialization failure or I/O error could leave a partial/truncated canonical file. This is a **publication-methodology correctness risk**, not evidence that past results were corrupted.

Changed publication to write a sibling temporary file, `json.dump(..., allow_nan=False)`, flush/fsync it, and then `os.replace` the destination on the same filesystem. A `finally` block removes temporary files on failure. This is an atomic visibility guarantee for replacement on supported local filesystems, not a full power-loss durability guarantee for the parent directory (no directory fsync).

## Verification and limitations
Added `tests/test_bench_atomic_publish.py` with three subprocess-free regression cases: valid replacement, injected `os.replace` failure preserving prior bytes, and serialization failure preserving prior bytes; both failures must clean up temp files. Locally reproduced the same helper and fault-injection scenarios with Python 3: **3/3 passed**. GitHub's CI suite runs `python3 -m unittest discover -s tests -p 'test_bench*.py' -v` on x86_64 and arm64; the new test is included by filename. The local reproduction was not a checkout of the GitHub repository, and CI results were not yet independently observed; do **not** claim full repository/CI verification until the workflow confirms.

Commits: [test](https://github.com/iinoshirozheng/mojo-analyze/commit/1499d76e163f22c4a0de15ddf94eb7fbc6c912f3), [fix](https://github.com/iinoshirozheng/mojo-analyze/commit/cff2abe0597c2f025597a75a23ee5aa463e7a396).

No Mojo binaries were built; no benchmark timing, checksum or canonical `ANALYSIS.md` conclusion changed.

## Next
The higher-priority unresolved performance hypothesis remains the arm64 checked-`Span` scanner's region-scoped wall/process/thread CPU-clock diagnostic with pinned runner and stable C/pointer controls.
