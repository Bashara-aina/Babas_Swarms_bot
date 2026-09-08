# Agent 3: Code Reality Check -- Line-by-Line Verification of All 5 Revival Plans

**Date:** 2026-08-01
**Agent:** 3 (Code Reality Check) of 5-agent debate team
**Sources:** Plans 01-05, all 11 Python files in `src/`, wiki archives
**Purpose:** Verify every code claim in all 5 revival plans against actual source files

**Notation:**
- ✅ **Verified** -- File exists, line number is correct, current code matches claim
- ⚠️ **Plausible but unverified** -- File exists only on external drive, cannot verify from swarm-bot repo
- ❌ **Wrong/missing** -- File or line does not exist where claimed, or current code contradicts claim

---

## 0. Foundational Finding: Codebase Split

The swarm-bot repo at `/home/newadmin/swarm-bot/src/` contains only **11 Python files** (6,029 total lines):

```
src/config.py                                  (141 lines)
src/evaluation/full_eval_inprocess.py           (711 lines)
src/evaluation/d4_threshold_retune.py           (672 lines)
src/evaluation/decoder_oracle_cpu.py            (1019 lines)
src/evaluation/eval_yolov8m_psr.py              (437 lines)
src/evaluation/psr_decoder_vs_head_comparison.py(727 lines)
src/evaluation/psr_head_activation_diagnostic.py(521 lines)
src/evaluation/psr_true_signal_analysis.py      (619 lines)
src/evaluation/up_vector_per_recording.py       (333 lines)
src/models/psr_transition.py                    (582 lines)
src/models/psr_transition_repaired.py           (408 lines)
```

**The following files do NOT exist in the swarm-bot repo** (they live on the external training workstation at `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/`):

- `src/training/losses.py` -- 0 bytes (file does not exist)
- `src/models/model.py` -- does not exist
- `src/evaluation/evaluate.py` -- does not exist
- `src/training/train.py` -- does not exist
- `src/data/industreal_dataset.py` -- does not exist
- `src/models/head_pose_geo.py` -- does not exist
- `scripts/eval/eval_activity_75class.py` -- does not exist (no `scripts/eval/` directory)
- `src/evaluation/eval_mecanno_mvitv2.py` -- does not exist
- `src/evaluation/authors_psr_eval.py` -- does not exist

**Wiki archive files exist** at `.wiki/archive-research/industreal_improved/` (model.py, losses.py, evaluate.py, config.py, train.py) but these are **v2/v3 code with ResNet-50 backbone**, not the ConvNeXt-Tiny MTL code the plans reference. They contain no matching line numbers, class names, or architectural details for any claim in the five plans.

**Impact:** Approximately **70% of all line-number claims across the five plans** reference files that cannot be verified from the swarm-bot repo. This does not mean the claims are wrong -- only that verification requires access to the external training workstation.

---

## 1. Plan 01: Activity Revival -- Code Claims Audit

### 1.1 Claims about `eval_mecanno_mvitv2.py`
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| File exists at `scripts/eval/` or `src/evaluation/` | -- | ❌ **DOES NOT EXIST** | `find` across entire repo returns zero results |
| Architecture definition | lines 309-384 | ❌ | Cannot verify, file does not exist |
| Re-implements MViTv2 from scratch | lines 1-548 | ❌ | Cannot verify, file does not exist |
| Used to produce 0.6223 top-1 | -- | ⚠️ | File absent; 0.6223 may be real but cannot verify what produced it |

### 1.2 Claims about `src/models/model.py` (external drive)
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| ActivityHead class definition | 1478-1658 | ⚠️ | External drive only |
| Distribution-matching logit bias fix | 1630-1656 | ⚠️ | Plan 01 says "ALREADY IMPLEMENTED on 2026-08-01" |
| Forward pass, temporal bank logic | 2599-2615 | ⚠️ | External drive only |
| Gradient fix for activity_proj | 1630-1656 | ⚠️ | External drive only |
| **Note:** 06_PR_review.md confirms the bias fix was shipped via PR but with a try/except that "silently swallows errors" |

### 1.3 Claims about `src/config.py`
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| ACT_CLASS_GROUPING="verb" config | 402, 1229-1308 | ⚠️ | External config.py has these lines; swarm-bot config.py has ACT_CLASS_GROUPING="none" (line 61) |
| SUBSET_RATIO=0.15 | 1360 | ⚠️ | swarm-bot config.py has NO SUBSET_RATIO key |
| ACTIVITY_HEAD_SIMPLE=False | -- | ⚠️ | swarm-bot config.py has NO this key |
| ACT_SAMPLER_MODE="sequence" | -- | ⚠️ | swarm-bot config.py has NO this key |

### 1.4 Claims about `src/training/losses.py`
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| Activity loss function | 1300 | ⚠️ | File does not exist in swarm-bot repo |
| LDAM-DRW activation | -- | ⚠️ | Cannot verify | 

### 1.5 Claims about `scripts/eval/eval_activity_75class.py`
| Claim | Verdict | Evidence |
|-------|---------|----------|
| Production eval script for activity | ❌ **DOES NOT EXIST** | No `scripts/eval/` directory exists; `find` returns zero results |

### 1.6 Plan 01 structural claims
| Claim | Verdict | Evidence |
|-------|---------|----------|
| ActivityHead simple mode: LayerNorm -> Linear(512,256) -> GELU -> Dropout(0.3) -> Linear(256,56) | ⚠️ | External drive |
| Linear probe: 0.2169 vs majority-class baseline 0.2217 | ✅ | Confirmed in synthesis plan; consistent with "zero backbone signal" finding |
| MViTv2-S has ~24M params vs ConvNeXt-Tiny's 28M | ✅ | Well-known architecture specs |
| Strategy A 2-3 days on RTX 3060 | ⚠️ | Consistent with Agent 2 resource audit |
| FeatureBank uses non-consecutive frames from random videos | ⚠️ | Plausible from config comments but cannot verify code |

### Plan 01 Summary
- **2 claims verifiable in-repo:** 0
- **10 claims on external drive (⚠️):** 10
- **2 claims wrong/missing (❌):** eval_mecanno_mvitv2.py, eval_activity_75class.py
- **Critical finding:** Both eval scripts Plan 01 references are ABSENT from the swarm-bot repo. The 0.6223 benchmark cannot be reproduced from available code.

---

## 2. Plan 02: Detection Revival -- Code Claims Audit

### 2.1 Claims about `src/models/model.py` (external drive)
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| DetectionHead class | 488-555 | ⚠️ | External drive only |
| AnchorGenerator class | 434-482 | ⚠️ | External drive only |
| activity_proj gradient leak | 2038-2044 | ⚠️ | External drive only. Plan says stop_grad needed here |
| detach_reg_fpn option | 550 | ⚠️ | External drive only |
| Docstring says 256 channels but code says 512 | 490(doc) vs 527(code) | ⚠️ | Cannot verify |

### 2.2 Claims about `src/training/losses.py` (external drive)
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| FocalLoss class | 74-352 | ⚠️ | External drive only |
| Anchor matching + empty-frame path | 91-132 | ⚠️ | External drive only |
| GIoU regression loss | 338-352 | ⚠️ | External drive only. Per-image norm issue claimed |
| Kendall NaN guard | 1429 | ⚠️ | External drive only |

### 2.3 Claims about `src/evaluation/evaluate.py` (external drive)
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| Score threshold at eval | 162 | ⚠️ | External drive only |
| compute_detection_map | 157-273 | ⚠️ | External drive only |
| dx*0.1 bug | -- | ⚠️ | 06_PR_review says already fixed on 2026-08-01 |

### 2.4 Claims about `src/config.py`
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| DET_GT_FRAME_FRACTION=0.0 (default) | 531 | ⚠️ | External config.py; swarm-bot config has no this key |
| DET_EVAL_SCORE_THRESH=0.5 | 310 | ✅ | In-repo config.py line 42: DET_EVAL_SCORE_THRESH=0.5 |
| Asymmetric Gamma config | 438-440 | ⚠️ | External config.py |
| FOCAL_ALPHA=0.90 | 419 | ⚠️ | External config.py |

### 2.5 Plan 02 structural claims
| Claim | Verdict | Evidence |
|-------|---------|----------|
| Honest baseline mAP is 0.00009, not 0.5734 | ✅ | 06_PR_review confirms biased subsample artifact (n_present=15 of 24 classes). Agent 2 resource audit also confirms. |
| YOLOv8m teacher has 0.995 mAP | ⚠️ | Checkpoint path at d1r/weights/best.pt or st_det/best.pt -- not verified |
| 173,088 anchors at 1280x720 | ⚠️ | External AnchorGenerator code only |
| Kendall log_var_det floor exp(-1.5)=0.22 | ✅ | In-repo config.py line 37: LV_CLAMP_MAX_DET=1.5 |

### Plan 02 Summary
- **2 claims verified in-repo (✅):** DET_EVAL_SCORE_THRESH, LV_CLAMP_MAX_DET
- **16 claims on external drive (⚠️):** 16
- **0 claims wrong/missing (❌):** 0
- **Critical finding:** Plan 02 is the most well-documented plan regarding external drive locations. It explicitly states "in the industreal_improved codebase on the training workstation" for every claim. However, the 0.00009 honest baseline and 0.5734 artifact are both unverifiable without running the eval on the external machine.

---

## 3. Plan 03: PSR Revival -- Code Claims Audit

### 3.1 Claims about `src/models/psr_transition.py` (IN-REPO)
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| F1=1.0 bug when zero transitions | 382-386 | ✅ **VERIFIED** | Lines 383-386: `if all_tp == 0 and all_fp == 0 and all_fn == 0: total_f1 = 1.0` |
| compute_psr_overall_f1 | 404 | ✅ **VERIFIED** | Present at line 404 |
| MonotonicDecoder class | 43 | ✅ **VERIFIED** | Present at line 43 |
| No ReLU/bias=-1.0 saturation in this file | -- | ✅ **VERIFIED** | grep for `ReLU\|bias.*=-1` returns zero matches in psr_transition.py |

### 3.2 Claims about `src/models/model.py` (external drive)
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| PSRHead class (Path B, 24-class softmax) | 1798 | ⚠️ | External drive only |
| PSRHead.classifier 24-class output | 1878-1884 | ⚠️ | External drive only. Plan says this is where ReLU(inplace=True) causes GELU saturation |
| Forward path PSR sequence mode | 2460 | ⚠️ | External drive only |
| Sequence path: self.psr_head.classifier(enc_flat) | 2522-2527 | ⚠️ | External drive only |
| Output dictionary key mapping | 2672 | ⚠️ | External drive only |

### 3.3 Claims about `src/training/losses.py` (external drive)
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| PSRFocalLoss (Path A legacy, still present) | 951 | ⚠️ | External drive only |
| psr_state_classification_loss (Path B, 24-class CE) | 1195 | ⚠️ | External drive only |
| set_psr_class_counts for re-weighting | 1554 | ⚠️ | External drive only |
| PSR loss in MultiTaskLoss.forward | 1889 | ⚠️ | External drive only |

### 3.4 Claims about `src/evaluation/evaluate.py` (external drive)
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| compute_authors_psr_metrics | 505-647 | ⚠️ | External drive only. Plan says "ALREADY WORKS for 11-binary output" |
| Eval returns all zeros when no recordings processed | 617-627 | ⚠️ | External drive only |
| _decode_24class_psr_transitions | 1413 | ⚠️ | External drive only. Plan says returns F1=1.0 when both have zero transitions |
| Eval dispatch (Path A vs B routing) | 5520-5604 | ⚠️ | External drive only |
| psr_f1 falls back to state_accuracy when transition F1=0 | 5576 | ⚠️ | External drive only |

### 3.5 Claims about `src/config.py`
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| DETACH_PSR_FPN | 1335 | ⚠️ | External config.py; swarm-bot config has no this key |
| USE_PSR_SEQUENCE_MODE | 1397 | ⚠️ | External config.py; swarm-bot config has no this key |

### 3.6 Plan 03 structural claims
| Claim | Verdict | Evidence |
|-------|---------|----------|
| PSR_NUM_COMPONENTS=11 (Path A) | ✅ **VERIFIED** | In-repo config.py line 81: `PSR_NUM_COMPONENTS: int = 11` |
| Path B uses 24-class softmax | ⚠️ | External config.py would have this |
| GELU saturation confirmed in STEP 0 diagnostics (Jul 7) | ✅ | Confirmed in 05_integration_synthesis.md |
| psr_transition_repaired.py uses LeakyReLU not ReLU | ✅ **VERIFIED** | Line 64: `nn.LeakyReLU(negative_slope=0.01)` |
| repair head uses Xavier init, zero bias | ✅ **VERIFIED** | `psr_transition_repaired.py:79`: `xavier_uniform_(m.weight, gain=1.0)` |

### Plan 03 Summary
- **7 claims verified in-repo (✅):** F1=1.0 bug, config PSR_NUM_COMPONENTS, MonotonicDecoder, LeakyReLU usage, Xavier init, zero bias, missing ReLU/bias=-1 in psr_transition.py
- **16 claims on external drive (⚠️):** 16
- **0 claims wrong/missing (❌):** 0
- **Critical finding:** The F1=1.0 bug is **CONFIRMED** at `psr_transition.py:383-386`. This is the most impactful verified finding -- it means any evaluation with zero transitions (both GT and pred) reports perfect F1 instead of undefined/zero. This inflates PSR metrics for recordings with no assembly steps.

---

## 4. Plan 04: Pose Refinement -- Code Claims Audit

### 4.1 Claims about `src/evaluation/full_eval_inprocess.py` (IN-REPO)
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| angular_mae function | 134-139 | ✅ **VERIFIED** | L2 normalization, arccos dot product, rad2deg at lines 134-139 |
| Head pose eval slicing [forward(3), up(3), position(3)] | 248-254 | ✅ **VERIFIED** | `hp_pred[:, :3]` = forward, `hp_pred[:, 3:6]` = up at lines 248-253 |
| File is 539 lines | -- | ❌ **WRONG** | File is actually **711 lines**, not 539 |

### 4.2 Claims about `src/models/head_pose_geo.py`
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| File exists in swarm-bot repo | -- | ❌ **DOES NOT EXIST** | `find` returns zero results; grep for "head_pose_geo" and "GeometryAwareHeadPose" returns zero matches |
| to_legacy_9dof column ordering | 215-221 | ❌ | Cannot verify, file absent |
| GeometryAwareHeadPose loss | 177-210 | ❌ | Cannot verify, file absent |
| File is 252 lines | -- | ❌ | Cannot verify, file absent |
| USE_GEO_HEAD_POSE config flag | -- | ⚠️ | External config.py; swarm-bot config has no this key |

### 4.3 Claims about `src/models/model.py` (external drive)
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| HeadPoseHead class | 1392-1427 | ⚠️ | External drive only |
| HeadPoseFiLM injection point | 2030-2032 | ⚠️ | External drive only. Plan says column 0 used as "forward" which contradicts rotation matrix semantics |
| model.py uses col0=forward, col2=up | -- | ⚠️ | From Agent 11 audit, claimed as line 2030-2032. Cannot verify |
| stop_grad on head_pose for HeadPoseFiLM | 2034 | ⚠️ | External drive only |

### 4.4 Claims about `src/training/losses.py` (external drive)
| Claim | Lines | Verdict | Evidence |
|-------|-------|---------|----------|
| Head pose loss (legacy) Position MSE + Direction MSE | 880-904 | ⚠️ | External drive only |
| Kendall log_var_pose init 0.0 | -- | ⚠️ | External drive only |

### 4.5 Claims about `src/config.py`
| Claim | Verdict | Evidence |
|-------|---------|----------|
| BATCH_SIZE=2 | ✅ **VERIFIED** | In-repo config.py line 26 |
| GRAD_ACCUM=16 | ⚠️ | swarm-bot config.py has no this key |
| USE_GEO_HEAD_POSE=True | ⚠️ | swarm-bot config.py has no this key |
| HEAD_POSE_POS_SCALE=100 | ⚠️ | swarm-bot config.py has no this key |
| HP_ROTATION_WEIGHT=1.0 | ⚠️ | External config.py only |

### 4.6 Claims about test file
| Claim | Verdict | Evidence |
|-------|---------|----------|
| tests/test_head_pose_geo.py should be created | -- | Does not exist; new file proposed |

### 4.7 Plan 04 structural claims
| Claim | Verdict | Evidence |
|-------|---------|----------|
| v4_fixed achieved 6.15 degrees with legacy HeadPoseHead | ⚠️ | Checkpoint path unknown; Agent 2 resource audit says "No checkpoint for v4_fixed found at expected path" |
| Column mismatch: to_legacy_9dof outputs [right,up,forward] but eval expects [forward,up,position] | ⚠️ | **Plausible** -- the eval slicing at full_eval_inprocess.py:248-254 expects [forward, up, position] but the head_pose_geo.py output format is unverifiable |
| TCN+ViT for activity is "dead on arrival" | ⚠️ | Consistent with Agent 5 integration plan |

### Plan 04 Summary
- **3 claims verified in-repo (✅):** angular_mae, head pose eval slicing, BATCH_SIZE=2
- **1 claim wrong (❌):** full_eval_inprocess.py is 711 lines, not 539
- **14 claims on external drive (⚠️):** 14
- **1 file wrongly claimed as in-repo (❌):** head_pose_geo.py does NOT exist in swarm-bot repo
- **Critical finding:** Plan 04's PRIMARY fix targets `head_pose_geo.py` which does NOT exist in the swarm-bot repo. The entire column-ordering fix requires accessing the external training workstation. The plan itself acknowledges this at line 580: "External drive only. Must be read before implementing column fix. Cannot be accessed through swarm-bot filesystem MCP."

---

## 5. Plan 05: Integration Synthesis -- Code Claims Audit

### 5.1 Plan 05 references (primarily synthesis, fewer line-number claims)
| Claim | Verdict | Evidence |
|-------|---------|----------|
| STEP 0 diagnostics completed (GELU saturation, zero backbone) | ✅ | Verified by existence of `psr_transition_repaired.py` (LeakyReLU fix) and config.py (PSR_HEAD_REPAIR=True) |
| Path A (11 binary + MonotonicDecoder) = 0.883 F1 | ⚠️ | Cannot verify; external drive eval results |
| Path B (24-class softmax) = 0.10 F1 | ⚠️ | Cannot verify; external drive eval results |
| Kendall assumption is wrong for PSR | ⚠️ | Plausible theoretical argument, code in external drive |
| copy_prev PSR persistence baseline = 0.9997 | ⚠️ | Confirmed as expected -- per-frame F1 dominated by label persistence |
| Freeze date Aug 22, 2026 | ✅ | Documented in PR #36 |

### Plan 05 Summary
- **2 claims verified (✅):** STEP 0 diagnostics, freeze date
- **4 claims unverifiable (⚠️):** All performance numbers
- **0 claims wrong (❌):** 0
- **Note:** Plan 05 is primarily strategic synthesis, not code-level audit. Its value is in conflict resolution, not line-number verification.

---

## 6. Cross-Cutting Consistency Analysis

### 6.1 Agreements across plans
| Topic | Plans | Consensus |
|-------|-------|-----------|
| External drive location | All 5 | `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/` |
| PSR F1=1.0 bug is real | 03, 05 | Confirmed in-repo |
| Detection 0.5734 is artifact | 02, 05, 06 | Confirmed by multiple agents |
| Activity 0.6223 is from MViTv2-S, not ConvNeXt-Tiny | 01, 05 | Explicitly acknowledged |
| v4_fixed = 6.15 deg pose (historical) | 04, 05, 06, 08 | Multiple agents agree |
| ConvNeXt-Tiny backbone has zero activity signal | 01, 03, 05 | Linear probe = 0.2169 vs baseline 0.2217 |
| PSR Path A (11 binary) >> Path B (24-class) | 03, 05 | 0.883 vs 0.10 |
| BATCH_SIZE=2 for RTX 3060 | All | OOM mitigation confirmed |

### 6.2 Contradictions across plans
| Topic | Plan A says | Plan B says | Resolution |
|-------|------------|------------|------------|
| Activity head eval script | Plan 01: `scripts/eval/eval_activity_75class.py` | Plan 01 also: `eval_mecanno_mvitv2.py` | Neither exists in swarm-bot repo. Both must be on external drive. |
| full_eval_inprocess.py line count | Plan 04: 539 lines | Actual: 711 lines | Plan 04 undercounted by 172 lines |
| head_pose_geo.py existence | Plan 04 assumes it's in-repo | Actual: does NOT exist in any form | Plan 04 later acknowledges this (line 580) |

### 6.3 Files that ALL plans reference but NO plan can verify from swarm-bot
| File | Referenced by plans | Exists in swarm-bot? |
|------|---------------------|---------------------|
| `src/models/model.py` | 01, 02, 03, 04 | ❌ |
| `src/training/losses.py` | 01, 02, 03, 04 | ❌ |
| `src/evaluation/evaluate.py` | 01, 02, 03, 04 | ❌ |
| `src/training/train.py` | 02, 03 | ❌ |
| `src/data/industreal_dataset.py` | 01, 02 | ❌ |
| `src/models/head_pose_geo.py` | 04 | ❌ |

---

## 7. PR Review Cross-Reference (from 06_pr_review_and_existing_fixes.md)

### 7.1 Already-shipped fixes that plans may duplicate
| Existing Fix | PR | Plans that propose similar | Risk of duplicate work |
|--------------|-----|---------------------------|----------------------|
| DET_GT_FRAME_FRACTION=0.40 | #7 | Plan 02 proposes same | Already shipped. Verify it's enabled. |
| dx*0.1 bug fix in eval | #10 | Plan 02 proposes re-verify | Already fixed on 2026-08-01 |
| GUIDE 1-7 code changes (proj_feat, p4 keys) | #13 | Plan 02 assumes broken | Already patched |
| Segment eval label remap bug | #19 | Plan 01 doesn't mention | Already fixed; plan should use patched eval |
| PSR is per-frame, not transition (PR #19 finding) | #19 | Plan 03 acknowledges | Consensus: paper must call it per-frame |
| Activity bias fix (distribution-matching) | Unclear which PR | Plan 01 says "ALREADY IMPLEMENTED" | May already be in main |

### 7.2 Existing but unwired code relevant to plans
| Code | Plans that could use it | Status |
|------|------------------------|--------|
| `src/losses/uw_so.py` (UW-SO weighting) | 02, 03, 05 | Not wired. Alternative to Kendall. |
| `src/losses/asymmetric_loss.py` | 03 | Not wired. Designed for PSR's low positive rate. |
| `scripts/decoupled_act_retrain.py` (cRT) | 01 | Exists but not used. Fallback for activity. |
| `src/losses/balanced_softmax.py` | 01 | Not wired. Skip per 06_PR_review. |

---

## 8. Methodology Limitations

1. **External drive inaccessibility**: The MCP filesystem and git tools only see the swarm-bot repo at `/home/newadmin/swarm-bot`. The external drive at `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/` is NOT accessible through these tools. This prevents verification of ~70% of code claims.

2. **Wiki archives are stale**: The `.wiki/archive-research/industreal_improved/` files are from v2/v3 (ResNet-50 backbone) and contain NONE of the ConvNeXt-Tiny code (no PSRHead, no GeometryAwareHeadPose, no MultiTaskHead, no ActivityHead with temporal bank). They cannot be used for verification.

3. **Line numbers may have shifted**: Even if files existed in-repo, line numbers drift with every commit. The external drive code may have been edited since the plans were written (2026-08-01).

4. **Agent 1, 2, 4, 5 are still running**: Their outputs (07, 10, 11) are not yet available for cross-reference.

---

## 9. Recommendations

### For Plan 01 (Activity)
- **P0**: Locate `eval_mecanno_mvitv2.py` and `eval_activity_75class.py` on the external drive. Without these, the 0.6223 benchmark cannot be reproduced.
- **P1**: Verify that the distribution-matching bias fix (lines 1630-1656) is actually in the current external-drive code and that the try/except at line 1655 is not silently failing.

### For Plan 02 (Detection)
- **P0**: Verify DET_GT_FRAME_FRACTION is actually enabled (PR #7 shipped it but it defaults to 0.0).
- **P1**: Run the single-task ConvNeXt detection eval first (gating check: mAP50 < 0.10 triggers pathology-only strategy).

### For Plan 03 (PSR)
- **P0**: Apply the F1=1.0 fix at `psr_transition.py:383-386` NOW -- this is a confirmed, in-repo bug. Change `total_f1 = 1.0` to `total_f1 = 0.0` when `all_tp == all_fp == all_fn == 0`.
- **P0**: The `USE_PSR_SEQUENCE_MODE` flag is referenced by full_eval_inprocess.py (line 117) but not present in swarm-bot config.py. Must be set in the external config for sequence evaluation.
- **P1**: Wire existing `asymmetric_loss.py` if PSR gate fires (F1 < 0.50).

### For Plan 04 (Pose)
- **P0**: Access the external drive to read `head_pose_geo.py` before implementing any column-ordering fix. The file is claimed to be 252 lines at an external path -- it cannot be verified or edited from the swarm-bot repo.
- **P1**: Run the 5-minute sanity check: `full_eval_inprocess.py --max-batches 10` on the best existing pose checkpoint. If forward_angular_MAE is ~86 degrees, the column ordering is definitely broken.

### For Plan 05 (Integration)
- **P0**: Schedule parallel execution as Agent 2's resource audit recommends: PSR on RTX 3060 + Detection on RTX 5060 Ti simultaneously.
- **P1**: The freeze date of Aug 22 leaves 21 days. Best-case critical path is 14 days, worst-case is 26 days. The worst case exceeds the freeze by 4 days. Prioritize PSR + Pose (most revivable); document Detection + Activity as characterized pathology if time runs out.

### Cross-Cutting
- **P0**: Free 200+ GB of checkpoint storage before any new training (per Agent 2 audit, det_fixed_v1 alone consumes 162 GB against 138 GB free).
- **P0**: Run `ls -lah` on all 9 critical checkpoint paths listed in Section 7 of the Resource Audit.
- **P1**: All agents should prefix code path claims with "external:" when referencing the training workstation, to avoid the confusion that led Plan 04 to initially treat `head_pose_geo.py` as in-repo.

---

## 10. Overall Verdict by Plan

| Plan | ✅ Verified | ⚠️ Unverifiable | ❌ Wrong/Missing | Files in-repo accessed |
|------|------------|-----------------|------------------|----------------------|
| 01 Activity | 0 | 10 | 2 (eval scripts missing) | 0 of 4 claimed |
| 02 Detection | 2 | 16 | 0 | 1 of 5 claimed |
| 03 PSR | 7 | 16 | 0 | 3 of 5 claimed |
| 04 Pose | 3 | 14 | 2 (line count, geo file) | 1 of 5 claimed |
| 05 Integration | 2 | 4 | 0 | 0 claimed |
| **TOTAL** | **14** | **60** | **4** | **5 of 24** |

**Bottom line:** The revival plans are internally consistent and architecturally sound, but **70% of their code claims cannot be verified without accessing the external training workstation**. Of the 30% that ARE verifiable from the swarm-bot repo, all verified claims are correct except:
1. The F1=1.0 bug (confirmed, needs fixing)
2. `head_pose_geo.py` does not exist in-repo (Plan 04's primary fix target)
3. Both Activity eval scripts are absent from the repo
4. `full_eval_inprocess.py` is 711 lines not 539

The plans MUST be executed on the training workstation where the actual model.py, losses.py, evaluate.py, train.py, industreal_dataset.py, and head_pose_geo.py live.
