# Arm64 checked-Span timing bands

Observed: 2026-09-26

## Question

Do the two verified 30-trial arm64 checked-Span runs support a simple binary fast/slow model?

## Method

I re-read the raw wall-time samples from jobs 107588131727 and 108032373904. Both used the same Mojo 1.2.0.dev2026092105 compiler revision, CPU-0 affinity, 10M-row corpus, 2 warmups plus 30 rotated trials, and the same checksum. I sorted each run and inspected adjacent gaps. No canonical benchmark result was changed.

## Result

Run 2026-09-24:
- fast: n=13, mean 0.333713 s, range 0.331482-0.336681
- intermediate: n=11, mean 0.558976 s, range 0.558096-0.560524
- high: n=6, mean 0.617585 s, range 0.617265-0.618059
- fast-to-intermediate gap: 0.221415 s
- intermediate-to-high gap: 0.056741 s

Independent rerun 2026-09-25:
- fast: n=14, mean 0.331348 s, range 0.329682-0.333418
- intermediate: n=4, mean 0.563109 s, range 0.560015-0.565079
- high: n=11, mean 0.616969 s, range 0.616104-0.617892
- one extreme sample: 1.128769 s
- fast-to-intermediate gap: 0.226596 s
- intermediate-to-high gap: 0.051025 s

The existing 0.45 s threshold is robust for the coarse baseline/degraded classification: across both runs the largest fast sample is 0.336681 s and the smallest non-fast sample is 0.558096 s, leaving an empty interval of about 0.221 s.

## Conclusion

The anomaly is robustly separated from the fast baseline, but the non-fast population is not homogeneous. Both independent runs reproduce an intermediate band near 0.56 s and a higher band near 0.617 s, with changing occupancy. A later region-scoped CPU-clock or hardware-counter study should report measurements per visible band rather than collapsing every non-fast trial into one mean. A single largest-gap clustering rule would also be misleading because the second run contains a lone 1.129 s extreme sample.

This is a methodology refinement, not a root-cause claim.

## Provenance

- workflow run 35985827133
- jobs 107588131727 and 108032373904
- artifacts 10802301857 and 10858504277
- probe source commit 96d25249849c78a85f41f6bc03204b9e7818c1a4
