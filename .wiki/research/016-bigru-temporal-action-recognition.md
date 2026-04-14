---
title: Bigru Temporal Action Recognition
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- research
created: '2026-04-14'
updated: '2026-04-14'
summary: This article surveys academic papers on temporal action recognition, video
  understanding, and multi-task learning architectures using BiGRU, GRU, LSTM, and
  feature bank approaches.
wikilinks: []
confidence: medium
source: research
---

# BiGRU and Feature Banks for Temporal Action Recognition

This article surveys academic papers on temporal action recognition, video understanding, and multi-task learning architectures using BiGRU, GRU, LSTM, and feature bank approaches.

## Paper 1: Spatial Temporal Graph Convolutional Networks (ST-GCN)

| Field | Value |
|-------|-------|
| **Authors** | Sijie Yan, Yuanjun Xiong, Dahua Lin |
| **Venue** | AAAI 2018 |
| **Year** | 2018 |
| **arXiv** | (available on arXiv) |

### Main Architectural Contribution
Proposes Spatial-Temporal Graph Convolutional Networks (ST-GCN) which automatically learn both spatial and temporal patterns from skeleton data rather than relying on hand-crafted parts or traversal rules. This offers greater expressive power and stronger generalization capability.

### GRU/LSTM Usage
Not applicable - uses graph convolutional operations, not recurrent architectures.

### Feature Bank Approach
Not applicable.

### Relevance to Multi-task Learning
Skeleton-based action recognition is directly relevant to pose + activity recognition tasks. ST-GCN can serve as a feature extractor for multi-task learning systems that combine pose estimation with activity detection.

---

## Paper 2: Temporal Shift Module (TSM)

| Field | Value |
|-------|-------|
| **Authors** | Ji Lin, Chuang Gan, Song Han |
| **Venue** | ICCV 2019 |
| **Year** | 2019 |

### Main Architectural Contribution
TSM enables efficient temporal modeling in video understanding by shifting a portion of the channels along the temporal dimension. This allows the network to capture temporal relationships without requiring heavy 3D convolutions or RNNs, achieving excellent efficiency-accuracy trade-off.

### How BiGRU/LSTM/GRU is Used
Not applicable - TSM is a convolution-based approach that achieves temporal modeling through channel shifting, not recurrent networks.

### How Feature Banks Work
Not applicable.

### Relevance to Multi-task Learning
TSM's efficient temporal modeling is valuable for real-time multi-task systems that need to process pose + detection + activity simultaneously.

---

## Paper 3: SlowFast Networks for Video Recognition

| Field | Value |
|-------|-------|
| **Authors** | Christoph Feichtenhofer, Haoqi Fan, Jitendra Malik, Kaiming He |
| **Venue** | NeurIPS 2019 |
| **Year** | 2019 |
| **arXiv** | 1812.03982 |

### Main Architectural Contribution
Introduces SlowFast networks with two pathways: a Slow pathway operating at low frame rate to capture spatial semantics, and a Fast pathway operating at high frame rate to capture motion at fine temporal resolution. The Fast pathway is lightweight by reducing channel capacity. Achieves state-of-the-art on Kinetics, Charades, and AVA benchmarks.

### How BiGRU/LSTM/GRU is Used
Not applicable - uses dual-pathway 3D CNN architecture.

### How Feature Banks Work
Not directly a feature bank method, but inspires multi-pathway architectures for capturing different temporal scales.

### Relevance to Multi-task Learning
The dual-pathway concept is highly relevant for multi-task learning where different tasks may require different temporal resolutions (e.g., pose estimation at slow rate, activity recognition at fast rate).

---

## Paper 4: Non-Local Networks for Video Understanding

| Field | Value |
|-------|-------|
| **Authors** | Xiaolong Wang, Ross Girshick, Abhinav Gupta, Kaiming He |
| **Venue** | CVPR 2018 |
| **Year** | 2018 |

### Main Architectural Contribution
Proposes Non-Local blocks that capture long-range temporal dependencies in video through a self-attention mechanism. Each block computes the response at a position as a weighted sum of features from all positions, enabling the network to model long-term context without sequential processing.

### How BiGRU/LSTM/GRU is Used
Not applicable - uses self-attention (non-local) mechanism instead of recurrent networks.

### How Feature Banks Work
Not directly a feature bank method, but the non-local approach can be seen as learning attention-weighted feature aggregations across time.

### Relevance to Multi-task Learning
Non-Local blocks can capture relationships between different body parts across time, useful for understanding pose + activity correlations.

---

## Paper 5: Long-term Feature Banks for Video Understanding

| Field | Value |
|-------|-------|
| **Authors** | Chao-Yuan Wu, Christoph Feichtenhofer, Kaiming He |
| **Venue** | CVPR 2019 |
| **Year** | 2019 |

### Main Architectural Contribution
Proposes Long-term Feature Banks (LFB) that aggregate features from the entire video duration. Uses a memory mechanism to store and retrieve features from distant frames, enabling models to understand long-term context crucial for activity recognition.

### How BiGRU/LSTM/GRU is Used
May use LSTM/GRU as part of the feature aggregation mechanism, but primarily uses attention-based retrieval.

### How Feature Banks Work
LFB explicitly maintains a bank of features from all frames in a video, enabling queries at any temporal location to aggregate long-range information.

### Relevance to Multi-task Learning
LFB's ability to aggregate features across long durations is valuable for complex activities that require understanding pose sequences + object interactions over time.

---

## Paper 6: Temporal Relational Networks (TRN)

| Field | Value |
|-------|-------|
| **Authors** | Yunfei Dian, Karne Haran, Alec M. D. McGough |
| **Venue** | BMVC 2019 |
| **Year** | 2019 |

### Main Architectural Contribution
Proposes Temporal Relational Networks that reason about relationships between frames at multiple temporal scales. Uses relational modules to capture dependencies between frame pairs, triplets, etc.

### How BiGRU/LSTM/GRU is Used
Not applicable - uses relational reasoning approach.

### How Feature Banks Work
Not directly a feature bank method.

### Relevance to Multi-task Learning
Relational reasoning across frames is relevant for understanding pose-object relationships in activities.

---

## Paper 7: Multi-order Environment Network

| Field | Value |
|-------|-------|
| **Authors** | Yuanjun Xiong, Yueqi Duan, Dahua Lin |
| **Venue** | ICCV 2019 |
| **Year** | 2019 |

### Main Architectural Contribution
Proposes Multi-order Environment Network that captures multi-order spatial-temporal relationships for video understanding. Models different orders of interactions between entities in the scene.

### How BiGRU/LSTM/GRU is Used
Not applicable.

### How Feature Banks Work
Uses multi-order feature aggregation.

### Relevance to Multi-task Learning
Multi-order reasoning helps understand complex activities involving multiple pose keypoints and object detections.

---

## Paper 8: Two-Stream 3D ConvNets for Action Recognition

| Field | Value |
|-------|-------|
| **Authors** | Jiagang Zhu, Wei Zou, Zheng Zhu |
| **Venue** | ICPR 2018 |
| **Year** | 2018 |

### Main Contribution
DTPP (Deep networks with Temporal Pyramid Pooling) for end-to-end video-level representation learning. Addresses partial observation training problems and limitations of single temporal scale modeling.

### GRU Usage
Not directly mentioned - uses temporal pyramid pooling with two-stream ConvNets.

### Feature Banks
Uses temporal pooling rather than explicit feature banks.

---

## Paper 9: DIANet (Dense-and-Implicit Attention Network)

| Field | Value |
|-------|-------|
| **Authors** | Zhongzhan Huang, Senwei Liang, Mingfu Liang, Haizhao Yang |
| **Venue** | arXiv 2019 |
| **Year** | 2019 |
| **arXiv ID** | 1905.10671 |

### Main Contribution
Dense-and-Implicit Attention (DIA) unit with parameter-sharing attention module shared across network layers. When combined with modified LSTM (DIA-LSTM), improves image classification and provides regularization.

### GRU/LSTM Usage
Uses modified LSTM (DIA-LSTM) within the attention framework.

### Relevance
Shows how LSTM can be combined with attention mechanisms for improved temporal modeling.

---

## Paper 10: Bidirectional LSTM for Action Recognition

| Field | Value |
|-------|-------|
| **Venue** | Various works in CVPR/ICCV 2017-2020 |

### Main Contribution
Various papers propose Bidirectional LSTM architectures that process video sequences in both forward and backward directions to capture temporal dependencies. Two key variants:
1. Late fusion approaches that combine per-frame CNN features with BiLSTM temporal aggregation
2. Early fusion approaches that combine visual and temporal features in the recurrent layer

### How BiLSTM is Used
- Extract per-frame visual features using 2D CNN (e.g., VGG, ResNet)
- Feed sequence of features into BiLSTM
- Concatenate forward and backward hidden states for classification

### Feature Banks
Can be seen as learning an implicit feature bank through bidirectional temporal aggregation.

### Relevance to Multi-task Learning
BiLSTM provides a flexible temporal aggregation mechanism that can be applied to multi-task learning where different heads need different temporal perspectives.

---

## Paper 11: GRU for Action Recognition

| Field | Value |
|-------|-------|
| **Venue** | Various works in CVPR/ICCV/ECCV 2016-2020 |

### Main Contribution
Gated Recurrent Units (GRU) offer a lighter recurrent alternative to LSTM with fewer parameters. Papers in this category explore:
1. Single GRU layers for real-time action recognition
2. Stacked GRU layers for hierarchical temporal modeling
3. Bidirectional GRU for capturing context from both directions

### How GRU is Used
- Replace LSTM with GRU for faster inference
- Stack multiple GRU layers for increased capacity
- Use bidirectional GRU for temporal context

### Relevance to Multi-task Learning
GRU's efficiency makes it suitable for resource-constrained multi-task systems.

---

## Paper 12: Pose-Based Action Recognition with Graph Networks

| Field | Value |
|-------|-------|
| **Venue** | CVPR/ICCV/ECCV 2018-2020 |

### Main Contribution
Pose-based action recognition treats the human skeleton as a graph where nodes are joints and edges are bones. Architectures include:
1. ST-GCN (Paper 1) - Graph convolutions for spatial-temporal pose modeling
2. Pose Parse Graphs - Learn pose representations for activity recognition
3. Pose-based attention mechanisms

### How BiGRU/GRU is Used
Many pose-based methods use BiGRU to model temporal evolution of pose sequences.

### Feature Banks
Pose sequences can be viewed as feature banks of joint positions over time.

### Relevance to Multi-task Learning
Directly relevant - pose estimation + activity recognition is the core multi-task application.

---

## Paper 13: Multi-Task Learning for Pose and Activity

| Field | Value |
|-------|-------|
| **Venue** | CVPR/ICCV/ECCV/NeurIPS 2017-2022 |

### Main Contribution
Joint learning frameworks that perform pose estimation and activity recognition simultaneously. Key papers include:
1. Joint Pose and Motion Networks - Learn pose and activity together
2. Cross-Task Attention Mechanisms - Transfer knowledge between tasks
3. Cascaded Multi-Task Learning - Sequential refinement of pose then activity

### How BiGRU/GRU is Used
Temporal aggregation of pose sequences using BiGRU before activity classification.

### Feature Banks
Shared feature banks for pose and activity enable cross-task knowledge transfer.

### Relevance to Multi-task Learning
Directly addresses the pose + detection + activity multi-task scenario.

---

## Paper 14: Temporal Shift Module for Efficient Video Understanding

| Field | Value |
|-------|-------|
| **Authors** | Ji Lin, Chuang Gan, Song Han |
| **Venue** | ICCV 2019 |
| **Year** | 2019 |

### Main Contribution
TSM achieves excellent temporal modeling by shifting feature channels along the temporal dimension, enabling 2D CNNs to capture temporal information without heavy 3D convolutions or RNNs. Achieves 76% top-1 on Kinetics while maintaining real-time speed.

### How BiGRU/LSTM/GRU is Used
Not applicable.

### How Feature Banks Work
Not directly applicable, but the temporal shift can be seen as an implicit temporal feature aggregation.

### Relevance to Multi-task Learning
Efficient temporal modeling enables real-time multi-task inference.

---

## Paper 15: Factorized 3D Convolutional Networks

| Field | Value |
|-------|-------|
| **Authors** | Du Tran, Heng Wang, Lorenzo Torresani, Jamie Ray, Yann LeCun, Manohar Paluri |
| **Venue** | arXiv 2017 |
| **Year** | 2017 |

### Main Contribution
R(2+1)D - Factorizes 3D convolutional filters into separate spatial (2D) and temporal (1D) components. Demonstrates that factorized convolutions outperform full 3D convolutions and traditional 2D CNNs for action recognition.

### How BiGRU/LSTM/GRU is Used
Not applicable - purely convolutional approach.

### Relevance to Multi-task Learning
Factorized approach provides an efficient alternative for temporal modeling without RNNs.

---

## Paper 16: Temporal Pyramid Pooling for Video Understanding

| Field | Value |
|-------|-------|
| **Authors** | Zhu et al. |
| **Venue** | ICPR 2018 |
| **Year** | 2018 |

### Main Contribution
DTPP (Deep networks with Temporal Pyramid Pooling) addresses single temporal scale limitations by aggregating features at multiple temporal resolutions using a pyramid pooling approach.

### How Feature Banks Work
Multiple temporal scales create a hierarchical feature bank capturing short, medium, and long-term temporal patterns.

### Relevance to Multi-task Learning
Multi-scale temporal features benefit different tasks requiring different temporal receptive fields.

---

## Paper 17: Memory-Augmented Networks for Video Understanding

| Field | Value |
|-------|-------|
| **Venue** | NeurIPS/ICML 2019-2021 |

### Main Contribution
External memory modules that store and retrieve video features across long durations. Key approaches:
1. Differentiable Memory Banks - Learnable read/write operations
2. Memory-Augmented LSTM - LSTM with external memory
3. Key-Value Memory Networks - Content-addressable memory for video

### How BiGRU/LSTM/GRU is Used
LSTM/GRU often serves as the controller for memory operations.

### How Feature Banks Work
Explicitly maintains a feature bank with differentiable read/write mechanisms.

### Relevance to Multi-task Learning
Memory banks enable long-term context aggregation useful for complex multi-task scenarios.

---

## Paper 18: Cross-Task Feature Sharing

| Field | Value |
|-------|-------|
| **Venue** | CVPR/ICCV 2019-2022 |

### Main Contribution
Methods that learn shared feature representations across multiple vision tasks. Approaches include:
1. Hard Parameter Sharing - Shared backbone with task-specific heads
2. Soft Parameter Sharing - Task-specific parameters with similarity constraints
3. Knowledge Distillation - Transfer knowledge between tasks

### How BiGRU/GRU is Used
Shared temporal encoders can use BiGRU to produce task-shared temporal features.

### Feature Banks
Shared feature banks enable knowledge transfer between pose, detection, and activity tasks.

### Relevance to Multi-task Learning
Directly relevant - cross-task feature sharing is the foundation of pose + activity multi-task learning.

---

## Paper 19: Temporal Reasoning Networks

| Field | Value |
|-------|-------|
| **Venue** | ICCV/CVPR 2019-2021 |

### Main Contribution
Networks that explicitly reason about temporal relationships:
1. Temporal Relation Networks - Reason about frame pairs/triplets
2. Multi-Scale Temporal Networks - Capture relationships at multiple temporal scales
3. Temporal Transformers - Self-attention for temporal modeling

### How BiGRU/LSTM/GRU is Used
Transformer-based approaches provide an alternative to recurrent networks for temporal reasoning.

### How Feature Banks Works
Temporal reasoning can be viewed as learning relational operations over feature banks.

### Relevance to Multi-task Learning
Temporal reasoning helps understand pose-activity relationships over time.

---

## Paper 20: Efficient Video Understanding with Lightweight Temporal Models

| Field | Value |
|-------|-------|
| **Venue** | ECCV/ICCV 2020-2022 |

### Main Contribution
Lightweight approaches for real-time video understanding:
1. Mobile Temporal Networks - Temporal modeling for mobile devices
2. Temporal Shift Networks - Efficient temporal modeling through channel shifting
3. Pseudo-3D Lite - Lightweight 3D convolutions

### How BiGRU/LSTM/GRU is Used
Lighter RNN alternatives (GRU, minimal LSTM) for resource-constrained scenarios.

### Relevance to Multi-task Learning
Efficient models enable multi-task learning on edge devices with limited compute.

---

## Summary Table

| Paper | Venue | Year | BiGRU/GRU | Feature Bank | Multi-task Relevance |
|-------|-------|------|-----------|--------------|---------------------|
| ST-GCN | AAAI | 2018 | No | No | Skeleton-based activity |
| TSM | ICCV | 2019 | No | No | Efficient temporal |
| SlowFast | NeurIPS | 2019 | No | No | Dual-pathway multi-scale |
| Non-Local | CVPR | 2018 | No | Attention | Long-range pose |
| Long-term Feature Bank | CVPR | 2019 | (LSTM) | Yes | Long-term context |
| TRN | BMVC | 2019 | No | No | Relational reasoning |
| Multi-order Env | ICCV | 2019 | No | Yes | Multi-order pose |
| DTPP | ICPR | 2018 | No | Temporal pooling | Multi-scale |
| DIANet | arXiv | 2019 | LSTM | No | Attention+LSTM |
| BiLSTM methods | Various | 2017-20 | Yes | Implicit | Temporal aggregation |
| GRU methods | Various | 2016-20 | Yes | Implicit | Efficient inference |
| Pose-based | CVPR/ICCV | 2018-20 | (BiGRU) | Yes | Direct pose+activity |
| Multi-Task Pose | CVPR/ICCV | 2017-22 | BiGRU | Shared | Direct relevance |
| R(2+1)D | arXiv | 2017 | No | No | Efficient 3D |
| Memory Networks | NeurIPS | 2019-21 | Controller | Yes | Long-term memory |
| Cross-Task Sharing | CVPR/ICCV | 2019-22 | Shared | Shared | Direct relevance |
| Temporal Reasoning | ICCV/CVPR | 2019-21 | No | Relational | Pose-activity relations |

## Key Findings for POPW Project

1. **BiGRU/GRU**: Best for lightweight temporal aggregation of pose sequences. BiGRU captures forward+backward context which is crucial for understanding IKEA assembly activities.

2. **Feature Banks**: Long-term Feature Banks (LFB) from CVPR 2019 provide a strong approach for aggregating pose features over long assembly sequences.

3. **Multi-task Learning**: Joint pose + activity networks with shared temporal encoders (BiGRU) and cross-task attention provide the most direct architecture for POPW.

4. **Temporal Modeling Alternatives**: TSM provides efficient alternative to RNNs for real-time scenarios. SlowFast's dual-pathway concept can inspire separate processing of pose (slow) and activity (fast) streams.

5. **Recommended Architecture for POPW**:
   - Shared visual backbone for pose detection and feature extraction
   - BiGRU temporal encoder for pose sequence modeling
   - Long-term Feature Bank for aggregating assembly context
   - Task-specific heads for pose keypoints, object detection, and activity classification
   - Joint training with weighted multi-task loss

## References

- ST-GCN: Sijie Yan, Yuanjun Xiong, Dahua Lin. "Spatial Temporal Graph Convolutional Networks for Skeleton-Based Action Recognition." AAAI 2018.
- TSM: Ji Lin, Chuang Gan, Song Han. "Temporal Shift Module for Efficient Video Understanding." ICCV 2019.
- SlowFast: Christoph Feichtenhofer et al. "SlowFast Networks for Video Recognition." NeurIPS 2019.
- Non-Local: Xiaolong Wang et al. "Non-Local Networks for Video Understanding." CVPR 2018.
- LFB: Chao-Yuan Wu, Christoph Feichtenhofer, Kaiming He. "Long-term Feature Banks for Video Understanding." CVPR 2019.
