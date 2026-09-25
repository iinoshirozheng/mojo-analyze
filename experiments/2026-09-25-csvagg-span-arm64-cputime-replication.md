# Arm64 checked-Span CPU-time replication — 2026-09-25

## Question
Does the Sep-24 CPU-time/wall-time relationship reproduce in an independent run on a newer arm64 hosted runner?

## Method
The existing Category-D diagnostic was rerun unchanged: Mojo 1.2.0.dev2026092105 (e9569894), clang 18.1.3, Neoverse-N2, CPU 0 pinning, 10M-row / 277.9 MiB corpus, identical checksum, 2 warmups and 30 rotated trials across checked Span, pointer control and C control. The rerun used ubuntu-24.04-arm image 20260920.129.1 in Azure westus2.

## Result
Checked Span again separated at the existing 0.45 s threshold: 14 fast and 16 slow trials. Fast means were 0.331348 s wall and 0.987877 s process CPU; slow means were 0.635491 s wall and 1.288417 s process CPU. Slow minus fast was +0.304143 s wall and +0.300540 s CPU, so CPU-accounted time increased by 98.8% of the wall-time increase. Across all 30 Span samples, wall and CPU time correlated at about r=0.9988. Pointer and C controls remained tight. One Span sample reached 1.128769 s, so the slow mean should not be interpreted as one stable slow-mode center.

## Conclusion
The Sep-24 CPU/wall co-movement independently reproduces on a newer runner image and different region. This weakens a one-run host/accounting explanation, but does not identify mechanism because CPU accounting still spans the whole invocation. The next clean experiment remains a thread/process CPU clock scoped to the scanner region. Canonical ANALYSIS.md, results, charts and benchmark code are unchanged.

Evidence: workflow 35985827133, rerun job 108032373904, artifact 10858504277, digest 6c6344e2c744af1e420327167bd26b9ad7aad32c5b26c9773bd35aa289858750.
