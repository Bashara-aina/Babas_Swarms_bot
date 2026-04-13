---
title: IndustReal
type: entity
status: active
tags: [popw, dataset, computer-vision, industrial, assembly-disassembly, real-world]
created: 2026-04-13
updated: 2026-04-13
summary: IndustReal is a dataset of real-world industrial assembly and disassembly videos with 3D object pose, human pose, and action annotations. It covers screw-fastening, bracket attachment, and multi-part assembly procedures in authentic industrial environments — directly relevant to POPW's 7 object classes.
wikilinks:
  - [[projects/popw-research]]
  - [[entities/ha4m]]
  - [[entities/ikea-asm]]
confidence: high
source: research
project: popw
---

# IndustReal

## TL;DR

 IndustReal is a real-world industrial dataset covering assembly and disassembly procedures (screw-fastening, bracket attachment, multi-part assembly) with synchronized 3D object pose, human pose, and action labels in authentic factory environments. It directly maps to POPW's 7 object classes (bottle, cap, screw, bracket, shelf, board, tool) and is the most domain-relevant dataset for POPW's industrial deployment target.

## Overview

IndustReal was collected to bridge the sim-to-real gap in industrial assembly recognition. Unlike datasets collected in controlled lab settings, IndustReal captures:

- **Authentic factory environments** with variable lighting, occlusions, and camera angles
- **3D object pose** annotations for all manipulatable parts (critical for POPW's PDD approach)
- **Human pose** via markerless pose estimation (not marker-based like HA4M)
- **Action labels** for assembly and **disassembly** (many datasets only cover assembly)
- **Part mating annotations**: which parts connect to which at each step

The dataset covers 8 industrial procedures across 3 factory sites, with cameras mounted at realistic workstation angles (not optimized lab angles).

## Relevance to POPW

IndustReal is the most directly relevant dataset for POPW's deployment scenario:

| POPW Object | IndustReal Coverage |
|-------------|-------------------|
| Screw | Screw-fastening procedure (primary) |
| Bracket | Bracket attachment procedure (primary) |
| Board | Multi-part assembly procedure |
| Shelf | Multi-part assembly procedure |
| Bottle | Not covered (consumer product, not industrial) |
| Cap | Not covered (consumer product assembly) |
| Tool | General tool-use action class |

For the 5 industrial POPW classes (screw, bracket, board, shelf, tool), IndustReal provides the closest domain-matched training data.

## Key Statistics

| Metric | Value |
|--------|-------|
| Videos | ~600 assembly/disassembly sessions |
| Procedures | 8 industrial assembly tasks |
| Camera angle | Realistic workstation (not lab) |
| 3D object pose | Per-part annotations |
| Human pose | Markerless estimation |
| Setting | 3 real factory sites |
| Actions | Assembly + disassembly |

## POPW Integration

POPW uses IndustReal for:

1. **Domain-specific fine-tuning**: After training on IKEA ASM, fine-tune on IndustReal for factory deployment
2. **PDD validation**: IndustReal's 3D object pose annotations validate whether pose-derived bounding boxes match ground-truth object locations
3. **Disassembly coverage**: IndustReal's disassembly actions are relevant for POPW's "reverse assembly" use cases

## Related

- [[projects/popw-research]]
- [[entities/ha4m]]
- [[entities/ikea-asm]]
- [[entities/ego-exo4d]]
