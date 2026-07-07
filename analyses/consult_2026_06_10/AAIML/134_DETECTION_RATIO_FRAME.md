# Detection Ratio Framing Correction

## Summary

The multi-task detection result (0.358 mAP) should be framed relative to the
single-task YOLOv8m ceiling (0.995 mAP) as a ratio, not conflated with a
percentage of the ceiling.

## Numerical Verification

| Quantity | Value | Computation |
|---|---|---|
| Multi-task detection mAP | 0.358 | eval on 250-batch subsample |
| Single-task YOLOv8m ceiling | 0.995 | full eval |
| Ratio of ceiling | 0.360 | 0.358 / 0.995 = 0.3598 |
| Percentage of ceiling | 36% | rounds to 36% |
| Multi-task cost | 64% | 1 - 0.358/0.995 = 0.6402 |

## Corrected Framing

**Correct**: "Multi-task detection reaches 36% of the single-task YOLOv8m
ceiling, a 64% multi-task cost."

**Incorrect** (previously stated in file 131): "64-68% of ceiling." The
0.358/0.995 ratio is 0.360, which rounds to 36%, not 64-68%. The prior framing
appears to have conflated 0.358 as a percentage (treating 0.358 as 36% of some
reference but then mislabeling it) or inverted the ratio.

**Incorrect**: "0.358 = 64% cost." The cost is derived from the ratio, not from
the raw mAP value. 0.358 is the raw detection mAP, not a percentage cost. The
cost is computed as 1 - (multi-task / single-task) = 64%.

## Caveats

- The 0.358 mAP figure comes from a 250-batch subsample evaluation, not a full
  evaluation. Full eval results are NaN in the checkpoint logs. The true
  multi-task detection mAP may differ from 0.358 once a full evaluation is run.
- The single-task YOLOv8m ceiling of 0.995 is from a full evaluation.
- The ratio comparison assumes the two evaluations are otherwise comparable
  (same dataset, same metric). They are -- both COCO val2017 mAP@0.5:0.95.

## D1 mAP=0.0004 Audit

D1 keypoint mAP of 0.0004 was audited. The 0-indexed alignment between the D1
training setup and evaluation pipeline was verified. There is no indexing bug.
The low value reflects genuine near-zero performance on D1 keypoints under the
current multi-task training regime, not a pipeline error.

## Recommendation

Drop the "BEATS SOTA" claim. The multi-task detection result of 0.358 mAP does
not beat the single-task SOTA of 0.995 mAP. At 36% of the single-task ceiling,
the multi-task model is not competitive with single-task detectors. This is
expected behavior for a unified multi-task model -- the trade-off is well known
in the literature. Frame the result honestly as a measurement of multi-task
cost: 64% detection degradation relative to the single-task YOLOv8m baseline.

Adopt the ratio framing consistently across all documentation. The numbers
tell a clear story: unified multi-task training gives you one model that can
handle multiple tasks, but detection performance drops to 36% of the dedicated
single-task alternative. Whether this trade-off is acceptable depends on the
application requirements.
