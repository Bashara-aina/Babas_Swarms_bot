---
title: Ego-Exo4D
type: entity
status: active
tags: [popw, dataset, computer-vision, egocentric, multi-view, skill-assessment]
created: 2026-04-13
updated: 2026-04-13
summary: Ego-Exo4D is a massive-scale egocentric video dataset (1,400 hours, 800+ performers) designed for skill assessment and，动作迁移。 It provides synchronized egocentric (head-mounted) + exocentric (third-person) video, 3D hand pose, body pose, and 2,500+ skill labels across 900+ natural task activities.
wikilinks:
  - [[projects/popw-research]]
  - [[entities/ikea-asm]]
  - [[entities/ha4m]]
confidence: high
source: research
project: popw
---

# Ego-Exo4D

## TL;DR

Ego-Exo4D is Meta's massive-scale video dataset for egocentric skill assessment, featuring 1,400 hours of synchronized egocentric (head-mounted AR glasses) + exocentric (third-person) video, 3D hand/body pose, and 2,500+ skill labels across 900+ natural task activities. It is the canonical benchmark for head-mounted camera activity recognition — directly relevant to POPW's industrial AR glasses deployment scenario.

## Overview

Ego-Exo4D (pronounced "ego-exo-for-dee") was created by Meta AI Research to enable **fine-grained skill understanding** from first-person video. It represents the state of the art in:

- **Egocentric video capture**: Head-mounted cameras (Meta AR glasses prototype) recording 800+ performers
- **Synchronized multi-view**: Each egocentric video has corresponding exocentric (tripod-mounted) reference views
- **3D hand pose**: All 21 hand joints per frame (ArtiBoost or similar markerless system)
- **3D body pose**: Full-body SMPL fitting
- **Skill taxonomy**: 2,500+ atomic skill labels (e.g., "pours-cereal", "tightens-screw", "folds-paper")
- **Natural task variety**: 900+ distinct activities across cooking, assembly, repair, craft, sports

The dataset is 10x larger than prior egocentric datasets (Ego4D had ~100 hours; Ego-Exo4D has 1,400 hours).

## Why It Matters for POPW

Ego-Exo4D is the **most relevant dataset** for POPW's deployment hardware (head-mounted industrial AR camera):

1. **Egocentric perspective**: POPW uses a head-mounted camera, not a workstation camera — Ego-Exo4D is the only large-scale dataset with this perspective
2. **Skill assessment focus**: POPW's goal (counting completed assembly cycles) maps directly to Ego-Exo4D's skill evaluation use case
3. **Hand pose emphasis**: Ego-Exo4D annotates 21 hand joints, critical for POPW's "is the worker holding the bottle?" detection
4. **Scale**: 1,400 hours provides enough data to validate whether POPW's FiLM-modulated architecture scales to real deployment

## Key Statistics

| Metric | Value |
|--------|-------|
| Video hours | 1,400 (egocentric + exocentric paired) |
| Performers | 800+ unique |
| Activities | 900+ natural tasks |
| Skill labels | 2,500+ atomic skills |
| Hand pose | 21 joints per frame |
| Body pose | Full SMPL |
| Camera | Meta AR glasses + tripod reference |

## POPW Relevance

POPW's relationship with Ego-Exo4D:

| POPW Need | Ego-Exo4D Coverage |
|-----------|-------------------|
| Head-mounted camera | Egocentric video (primary) |
| Hand pose (21 joints) | Full 21-joint hand pose |
| Activity recognition | 2,500 skill labels |
| Multi-view validation | Egocentric + exocentric paired |
| Assembly procedures | Partial (cooking, repair, craft also included) |

POPW's 7 object classes are **not** directly annotated in Ego-Exo4D, but the hand pose annotations would enable training a "hand + object" joint detector.

## Comparison Summary

| Dataset | Hours | Camera | Pose Detail | POPW Alignment |
|---------|-------|--------|-------------|----------------|
| IKEA ASM | ~60 | Fixed workstation | 17 body | Medium |
| Assembly101 | ~120 | Multi-view | 25 SMPL | Medium |
| HA4M | Large | Industrial CCTV | OptiTrack marker | Low (industrial) |
| IndustReal | ~40 | Workstation | Markerless | High (industrial) |
| **Ego-Exo4D** | **1,400** | **Head-mounted** | **21 hand + body** | **High (camera type)** |

## Related

- [[projects/popw-research]]
- [[entities/ikea-asm]]
- [[entities/assembly101]]
- [[entities/ha4m]]
- [[entities/industreal]]
