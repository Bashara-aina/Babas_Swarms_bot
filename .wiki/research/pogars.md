---
title: "POGARS: Pose-Graph Attention for Activity Recognition"
created: 2026-04-14
modified: 2026-04-14
tags: [pogars, pose-graph, graph-attention, skeleton-action, spatial-modeling, pose-relations, mtl]
authors: [Thilakarathne et al.]
type: research
summary: "POGARS (Pose-Graph Attention for Activity Recognition, Thilakarathne et al. 2021) represents skeleton as a pose graph with attention-based message passing between body parts. Joints are nodes, bones are edges, and graph attention learns which pose relationships matter for each action. Relevant for POPW's per-joint pose reasoning."
wikilinks:
  - [[mmn]]
  - [[psumnet]]
  - [[pose-conditioned-temporal-modeling]]
  - [[projects/popw-multi-task-ikea]]
source: https://arxiv.org/abs/2108.04186
---

# POGARS: Pose-Graph Attention for Activity Recognition

## Paper Info
- **arXiv**: [2108.04186](https://arxiv.org/abs/2108.04186)
- **Authors**: Thilakarathne et al.
- **Venue**: arXiv 2021

## Core Contribution

POGARS represents skeleton as a **pose graph** and uses **graph attention** to learn which joint relationships are important for each action. Unlike rigid body part decomposition (PSUMNet), POGARS learns **data-driven** pose relationships.

## Pose Graph Representation

```
Skeleton → Pose Graph:
  Nodes: J = 17 joints (COCO keypoints)
  Edges: E = bone connections between adjacent joints
         (skeleton structure: shoulder → elbow → wrist, etc.)

Adjacency matrix A ∈ R^[J×J]:
  A[i,j] = 1 if joint i and j are connected by bone
         = 0 otherwise

Node features X ∈ R^[J×D]:
  X_j = embedding of joint j position + confidence
```

## Graph Attention Message Passing

```
For each joint j, compute attention to neighbor k:
  e_{jk} = LeakyReLU(a^T · [W·x_j ⊕ W·x_k])

  α_{jk} = softmax_jk(e_{jk})  # attention weight

Message from neighbor k to j:
  m_{jk} = α_{jk} · W·x_k

Update node j:
  x'_j = σ(Σ_k m_{jk} + x_j)  # aggregate neighbors + self
```

**What attention learns**:
- For "reach": high attention from shoulder to wrist
- For "stand": high attention between leg joints
- For "grasp": high attention from fingers to palm

## Multi-Head Graph Attention

POGARS uses **multi-head attention** (K=8 heads):
```
Head h: computes x'_j^h using attention
Final: x'_j = concat([x'_j^1, ..., x'_j^K]) · W^O
```

This captures different pose relationship types simultaneously:
- Head 1: parent-child bone relationships
- Head 2: same-limb relationships (left-right symmetry)
- Head 3: action-specific relationships (tool-use hand → object)

## POPW Enhancement: PoseFiLM + Graph Attention

POPW's current approach treats pose flatly (concatenated 34 values):
```
pose_flat = concat([keypoints_17, confidence_17]) → PoseFiLM
```

POGARS suggests **structured pose graph reasoning**:
```
Pose Graph:
  17 nodes (joints), edges (bones)

  Graph Attention → pose_graph_embedding ∈ R^D

  pose_graph_embedding → γ_net, β_net

  C5_mod = γ ⊙ C5 + β  # structured pose-conditioned features
```

**Benefit**: Graph attention captures:
- Bone relationships (arm structure)
- Symmetry (left-right pose similarity)
- Action-relevant pose clusters (hand-joints group for tool use)

## POPW + POGARS Temporal Extension

```
Frame t:
  Pose graph [17 nodes, 19 edges] → Graph Attention → pose_graph_t
  Temporal: BiGRU(pose_graph[0:8]) → temporal_hidden
  → Activity Classification
```

**Why this works for assembly**:
- Graph structure captures body kinematics (shoulder→elbow→wrist chain)
- Graph attention learns action-specific attention (hand→object focus)
- BiGRU adds temporal reasoning (assembly phase progression)

## Comparison with PSUMNet

| Aspect | PSUMNet | POGARS |
|--------|---------|--------|
| Pose structure | Fixed parts (4) | Learnable graph |
| Part decomposition | Explicit | Implicit via attention |
| Attention | Part-wise | Node-wise |
| Body relationships | Predefined | Learned |

**PSUMNet** is better when:
- Body part decomposition is known a priori
- Fixed part-wise processing is sufficient

**POGARS** is better when:
- Action-specific pose relationships matter
- Learning from data is preferred over predefined structure

## Practical Considerations for POPW

POGARS requires:
1. **Graph construction**: Define adjacency from skeleton topology
2. **Graph attention implementation**: MessagePassing or PyG
3. **Training**: Sufficient data for attention to learn meaningful relationships

**For POPW's 254 videos**: PSUMNet's predefined parts may be more practical than POGARS's learned attention (less data needed).

## Future POPW Enhancement: Hybrid PSUMNet + POGARS

```
Pose → Part Decomposition (PSUMNet):
  upper, lower, left_arm, right_arm

Pose Graph (POGARS):
  Within each part: graph attention between joints
  Cross-part: attention between part centroids

Part-wise modulation:
  part_graph_embedding → γ_part, β_part
  C5_mod_part = γ_part ⊙ C5_part + β_part

Fusion + Temporal:
  concat(part_modulated) → BiGRU → Activity Classification
```

## References

- Thilakarathne et al. (2021). "POGARS: Pose-Graph Attention for Activity Recognition." arXiv:2108.04186
