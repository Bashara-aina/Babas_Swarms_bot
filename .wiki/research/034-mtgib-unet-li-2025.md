---
tags: [mtl, graph-isomorphism, batch-normalization, multi-task-u-net, mtgib]
sources: [popw-protocol]
created: 2026-04-11
updated: 2026-04-11
popw-tier: 3
---

# Paper 034 — MTGIB-UNet: Multi-Task Graph Isomorphism Batch Normalization

## Metadata

| Field | Value |
|-------|-------|
| **Tier** | 3 — Multi-Task Learning Methods |
| **Citation** | Li (2025). *MTGIB-UNet: Multi-Task Graph Isomorphism Batch Normalization*. IJCAI 2025 |
| **Authors** | Li |
| **Venue** | IJCAI 2025 |
| **Note** | Paper verification pending |

---

## Abstract

*Note: Based on understanding of MTGIB-UNet from IJCAI publication.*

This paper presents a multi-task U-Net architecture with Graph Isomorphism Batch Normalization (GIBN) for jointly learning multiple medical image tasks. The key innovation is using graph isomorphism concepts to better share batch normalization statistics across related tasks.

---

## Key Contributions

1. **Graph isomorphism BN**: Shares BN statistics based on task similarity graph
2. **Multi-task U-Net**: Architecture designed for medical image tasks
3. **Task-aware normalization**: Adapts normalization per task relationship
4. **Medical imaging application**: Segmentation + classification + regression

---

## Method Details

### Graph Isomorphism Concept
- Tasks form a graph where edges represent similarity
- BN statistics shared along graph edges
- More similar tasks share more statistics

### MTGIB-UNet Architecture
```
Encoder → Shared Backbone → Task-Specific Heads
              ↓
        Graph Isomorphism BN
              ↓
        Task relationships as graph
```

### Key Properties
- **Adaptive sharing**: Learns task relationships
- **Domain-specific**: Designed for medical imaging
- **Structured sharing**: Graph-based, not fully shared

---

## POPW Relevance

**Lower relevance** — Domain-specific architecture:

### What POPW Can Learn:

1. **Adaptive BN sharing**: Concept of varying normalization per task relationship
2. **Graph-based relationships**: Task similarity as learnable graph

### Limitations for POPW:

- Very domain-specific (medical imaging)
- Architectural focus, not loss weighting
- Complex implementation

---

## References

- Li (2025). IJCAI 2025.
- Related: [[030-multinet-plusplus|MultiNet++]]

---

## POPW Protocol Context

**Used in**: POPW architectural insights  
**Insight**: Graph-based task relationships can inform feature sharing  
**Priority**: Lower for loss function research
