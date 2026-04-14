---
title: POPW Architecture Diagram Analysis — BIGRU and Feature Bank Integration
type: analysis
status: active
tags: [popw, architecture, bigru, feature-bank, temporal-modeling, diagram-analysis]
created: 2026-04-14
updated: 2026-04-14
summary: Analysis of existing WorkerNet architecture diagram and requirements for adding BIGRU temporal modeling and feature bank components. Documents current single-frame pipeline, required changes for temporal modeling, and PDF upgrade path.
wikilinks:
  - [[architecture/worker-net-architecture-diagram]]
  - [[architecture/worker-net-improved4]]
  - [[research/popw-activity-head-temporal-alternatives]]
  - [[research/popw-v14-ground-truth]]
confidence: high
source: research
project: popw
---

# POPW Architecture Diagram Analysis — BIGRU and Feature Bank Integration

## TL;DR

Analysis of the existing WorkerNet PNG diagram and research context for adding:
1. **BIGRU** (Bidirectional GRU) temporal modeling to the Activity Head
2. **Feature Bank** for clip-level temporal feature storage
3. **PDF upgrade** for thesis-quality documentation

The current architecture is single-frame only. Adding temporal modeling requires transitioning to clip-based processing (T frames) and integrating BIGRU after the PoseFiLMModule in the activity path.

---

## 1. Existing Architecture Components

### 1.1 Current Pipeline (Single-Frame)

```
Input [B, 3, 640, 480]
    ↓
ResNet-50 (ImageNet pretrained, frozen first 20 epochs)
    → C3 [B, 512, 80, 60], C4 [B, 1024, 40, 30], C5 [B, 2048, 20, 15]
    ↓
FPN (256-ch lateral convs + smooth + P6/P7)
    → P3 [B, 256, 80, 60], P4 [B, 256, 40, 30], P5 [B, 256, 20, 15]
        P6 [B, 256, 10, 8],  P7 [B, 256, 5, 4]
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ P5 ─────────┬─► DetectionHead (RetinaNet-style, 7 classes)      │
│             ├─► PoseHead (Heatmap + soft-argmax, 17 keypoints)  │
│             └─► ActivityHead (GAP + FC → 33 classes)            │
│                    ↑                                            │
│                    └ PoseFiLMModule (modulates C5 with pose)  │
└─────────────────────────────────────────────────────────────────┘
Output: detections, keypoints [B, 17, 3], activity logits [B, 33]
```

### 1.2 Three Task Heads

| Head | Input | Output | Loss |
|------|-------|--------|------|
| **Pose Estimation** | P3 [B, 256, 80, 60] | 17 COCO keypoints | Wing Loss |
| **Object Detection** | P5 [B, 256, 20, 15] | 7 furniture parts | Focal Loss |
| **Activity Recognition** | C5 [B, 2048, 20, 15] | 33 action classes | CB-Focal Loss |

### 1.3 PoseFiLMModule (Current)

```python
# Pose-conditioned feature modulation
keypoints [B, 17, 3] → flatten + concat → [B, 68]
    → MLP → gamma [B, 2048], beta [B, 2048]
modulated_C5 = gamma ⊙ C5 + beta  [applied before GAP in activity head]
```

### 1.4 Multi-Task Loss

```python
L_total = 0.5 * exp(-log_var_det) * L_det
        + 0.5 * exp(-log_var_pose) * L_pose
        + 0.5 * exp(-log_var_act) * L_act
        + log_var_det + log_var_pose + log_var_act
```

### 1.5 Current Performance (improved4_film)

| Metric | Value |
|--------|-------|
| Activity Top-1 | 37.4% |
| Detection mAP@0.5 | 0.600 |
| Pose PCK@0.1 | 99.9% |
| Trainable params | 42.3M |
| Inference latency | 26.34ms |

**Target**: Exceed 78.1% (Frame2Freq SOTA on IKEA ASM)

---

## 2. What Needs to Be Added

### 2.1 BIGRU (Bidirectional GRU)

**Purpose**: Add temporal modeling to the Activity Head

From `popw-activity-head-temporal-alternatives-2026-04-14.md`:
- BiGRU is an explicit sequence model that learns temporal memory after feature extraction
- Preserves multi-task head isolation (stays in activity head only)
- Aligns with PoseFiLM: `Pose -> FiLM(C5) -> BiGRU(C5_mod)`
- Hidden state 256, bidirectional = ~32 MB parameters
- Alternative: Mamba (~16KB, 1000× smaller) for better efficiency

**Integration point**: After PoseFiLMModule, before activity classification
```
C5 → PoseFiLMModule → C5_mod → BiGRU → Activity Classification
```

**Data flow change**:
1. Old loader: single frame/sample
2. New loader: T=8 consecutive frames/sample
3. Forward: [B, T, C, H, W] → reshape for backbone → [B*T, C, H, W]
4. Post-backbone: reshape to [B, T, 2048, H, W], temporal processing

### 2.2 Feature Bank

**Purpose**: Store clip-level features for temporal aggregation

From research documentation:
- Clip-level feature bank stores features from T consecutive frames
- Enables temporal aggregation (average pooling, attention, etc.)
- BiGRU + FeatureBank recommended for strongest paper novelty

**Key property**: Maintains head isolation — temporal modeling doesn't affect detection or pose heads

### 2.3 PDF Upgrade

**Current state**: PNG image at `popw-media/worker-net-architecture-diagram.png`

**Upgrade path**: Convert to PDF for:
1. Vector scalability (no pixelation when zooming)
2. Print-ready thesis documentation
3. Editable in diagram tools (Draw.io, Inkscape)

---

## 3. Architecture Comparison

### 3.1 Current vs. Temporal-Upgraded

| Aspect | Current (Single-Frame) | With BIGRU + Feature Bank |
|--------|------------------------|---------------------------|
| Input | Single frame [B, 3, 640, 480] | Clip of T frames [B, T, 3, 640, 480] |
| Temporal modeling | None | BiGRU (256 hidden, bidirectional) |
| Feature storage | Per-frame | Clip-level feature bank |
| Activity head input | C5 [B, 2048, 20, 15] | C5 sequence [B, T, 2048, 20, 15] |
| Pose-FiLM chain | Pose → FiLM(C5) | Pose → FiLM(C5) → BiGRU |
| Dataset change | None | Required (stack T frames) |
| VRAM impact | Baseline | Minimal (+0.04 GFLOPs for BiGRU) |

### 3.2 TSM vs. BiGRU Decision

From temporal alternatives research:

| Aspect | TSM | BiGRU |
|--------|-----|-------|
| Use of T frames | Parallel (reshape into batch) | Sequential (hidden state flows) |
| Backbone impact | Modified in-place | Unchanged |
| Temporal location | Inside shared visual backbone | Post-backbone activity path |
| Paper narrative | "Zero-cost temporal backbone" | "Assembly-aware temporal memory head" |
| Head isolation | Shared (affects all heads) | Isolated (activity only) |
| PoseFiLM synergy | Moderate | Best |

**Recommendation**: Choose BiGRU + feature bank for:
- Stronger paper story + PoseFiLM synergy
- Maximum novelty
- Clean multi-task ablations

---

## 4. Key Components to Diagram

### 4.1 New Components for PDF

1. **Clip Sampler** (dataset change)
   - Samples T=8 consecutive frames per training sample
   - Converts single-frame to clip-based processing

2. **Feature Bank** (inside Activity Head)
   - Stores [B, T, 2048] features per clip
   - Feeds into BiGRU for temporal modeling

3. **BiGRU Module** (inside Activity Head)
   - Bidirectional GRU: 256 hidden units
   - Input: C5_mod sequence [B, T, 2048]
   - Output: temporal features [B, 512] (forward + backward hidden states)

4. **Modified Activity Head**
   ```
   C5 [B, T, 2048, 20, 15]
       → PoseFiLMModule → C5_mod [B, T, 2048, 20, 15]
       → Feature Bank → aggregated [B, 2048]
       → BiGRU → temporal features [B, 512]
       → FC (512 → 33) → activity logits [B, 33]
   ```

### 4.2 Data Flow with Temporal Modeling

```
Frame t-1 ─┐
Frame t   ─┼→ Clip Sampler → T frames → ResNet-50 → C5 sequence
Frame t+1 ─┘                                    ↓
                                                   PoseFiLMModule (per-frame)
                                                   ↓
                                              C5_mod sequence [B, T, 2048, 20, 15]
                                                   ↓
                                              Feature Bank (clip-level)
                                                   ↓
                                              BiGRU (bidirectional)
                                                   ↓
                                              [B, 512] temporal features
                                                   ↓
                                              FC → Activity Classification
```

---

## 5. Research Context Summary

### 5.1 Literature Gap (FiLM + Pose + Action)

From `popw-film-literature-gap.md`:
- No prior work uses FiLM-style affine modulation with pose/skeleton as conditioning signal
- Existing works use FiLM with language/style/label conditioning, NOT raw pose coordinates
- POPW's PoseFiLMModule is novel: `MLP(kp) → (γ, β) → γ·C5_features + β`

### 5.2 Temporal Alternatives

From `popw-activity-head-temporal-alternatives-2026-04-14.md`:
- BiGRU + FeatureBank: +2.1M params, +0.04 GFLOPs, minimal VRAM impact, HIGH novelty
- TSM: 0 params, 0 FLOPs, but modifies shared backbone
- Mamba: ~16KB (vs 32MB for BiGRU), 1000× memory reduction

### 5.3 Current Performance vs. Target

| Model | Activity Top-1 | Target |
|-------|---------------|--------|
| improved4_film | 37.4% | 78.1% (Frame2Freq SOTA) |
| Frame2Freq (2026) | 78.1% | - |

**Gap**: +40.7 percentage points needed

---

## 6. Implementation Requirements

### 6.1 Dataset Change (Required for both TSM and BiGRU)

```python
# Old: single frame per sample
dataset[index] → {'image': [3, 640, 480], 'labels': {...}}

# New: clip of T frames per sample
dataset[index] → {
    'clip': [T, 3, 640, 480],  # T consecutive frames
    'labels': {...}
}
```

### 6.2 Activity Head Modification

```python
class ActivityHeadWithBiGRU(nn.Module):
    def __init__(self, in_channels=2048, hidden_size=256, num_classes=33):
        self.pose_film = PoseFiLMModule()
        self.feature_bank = FeatureBank(T=8)  # stores clip features
        self.bigru = nn.GRU(
            input_size=in_channels,
            hidden_size=hidden_size,
            bidirectional=True,
            batch_first=True
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * 2, 512),
            nn.ReLU(),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, c5_sequence, keypoints):
        # c5_sequence: [B, T, 2048, 20, 15]
        # keypoints: [B, T, 17, 3]
        
        # PoseFiLM modulation per frame
        c5_mod = self.pose_film(c5_sequence, keypoints)  # [B, T, 2048, 20, 15]
        
        # Feature bank aggregation
        c5_agg = self.feature_bank.pool(c5_mod)  # [B, 2048]
        
        # BiGRU temporal modeling
        c5_seq_2d = c5_mod.mean(dim=[3, 4])  # [B, T, 2048]
        gru_out, _ = self.bigru(c5_seq_2d)  # [B, T, 512]
        
        # Use final timestep for classification
        temporal_features = gru_out[:, -1, :]  # [B, 512]
        
        return self.classifier(temporal_features)
```

### 6.3 Validation Metric (Unchanged)

```python
combined = 0.40 * normalize(F1) + 0.35 * normalize(PCK) + 0.25 * normalize(mAP)
```

---

## 7. Diagram Content Requirements

### 7.1 Components to Highlight

1. **New**: Clip Sampler arrow from video → model input
2. **New**: Feature Bank box (inside Activity Head expanded view)
3. **New**: BiGRU box (inside Activity Head expanded view)
4. **Modified**: PoseFiLMModule → BiGRU connection
5. **Data dimensions**: [B, T, C, H, W] notation at each temporal stage

### 7.2 Color Coding Recommendation

| Component | Color | Reason |
|-----------|-------|--------|
| Backbone (ResNet-50) | Gray | Shared, unchanged |
| FPN Neck | Blue | Shared, unchanged |
| Pose Head | Green | Unchanged |
| Detection Head | Yellow | Unchanged |
| Activity Head + Temporal | Orange | Modified/Added |
| PoseFiLMModule | Purple | Novel component |
| NEW: Feature Bank | Pink | New addition |
| NEW: BiGRU | Red | Key temporal component |

### 7.3 PDF Specifications

- Page size: A4 landscape (for thesis)
- Font: Sans-serif, minimum 10pt for labels
- Arrow style: Unified Modeling Language (UML) style
- Include: Input dimensions, output dimensions, parameter counts

---

## 8. Summary of Analysis

### 8.1 Current State
- Single-frame processing (no temporal modeling)
- Three parallel heads: Pose, Detection, Activity
- PoseFiLMModule provides pose-conditioned modulation
- Kendall uncertainty weighting for multi-task balance
- Performance: 37.4% activity top-1 (need 78.1%)

### 8.2 Required Changes
1. **Dataset**: Single-frame → clip-based (T frames)
2. **Activity Head**: Add Feature Bank + BiGRU after PoseFiLMModule
3. **Diagram**: Update to show temporal flow, add new components

### 8.3 Key Design Decisions
- **BiGRU chosen over TSM**: Better head isolation, PoseFiLM synergy, higher novelty
- **Feature Bank**: Enables clip-level temporal aggregation
- **Integration point**: After PoseFiLMModule, before classification FC
- **Chain preserved**: Pose → FiLM(C5) → BiGRU(C5_mod)

### 8.4 Next Steps for Diagram Update
1. Create expanded Activity Head view showing internal temporal modules
2. Add Feature Bank component with pool operation
3. Add BiGRU with forward/backward arrows
4. Update data flow labels to [B, T, C, H, W] format
5. Export to PDF for thesis quality

---

## Related Documents

- [[architecture/worker-net-architecture-diagram]] — Existing diagram (PNG)
- [[architecture/worker-net-improved4]] — Full model architecture
- [[research/popw-activity-head-temporal-alternatives]] — BiGRU vs TSM comparison
- [[research/popw-film-literature-gap]] — FiLM novelty argument
- [[research/popw-v14-ground-truth]] — Verified tensor shapes and dimensions
- [[research/temporal-attention-alternatives]] — Mamba and SSM alternatives to BiGRU

---

*Analysis completed: 2026-04-14*
*Source: Research context from .wiki/research/ directory*
