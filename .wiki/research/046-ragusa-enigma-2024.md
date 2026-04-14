---
title: Ragusa Enigma 2024
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
summary: The ENIGMA datasets provide egocentric video data for understanding human
  behavior in industrial scenarios. ENIGMA-51 focuses on electrical board repair tasks
  with 19 subjects, while ENIGMA-360 exp...
wikilinks: []
confidence: medium
source: research
---

# Summary

The ENIGMA datasets provide egocentric video data for understanding human behavior in industrial scenarios. ENIGMA-51 focuses on electrical board repair tasks with 19 subjects, while ENIGMA-360 expands to 180 egocentric and 180 exocentric synchronized videos for comprehensive industrial procedure coverage.

## ENIGMA-51 (WACV 2024)

**Task**: Repair of electrical boards using industrial tools (electric screwdriver, oscilloscope)

- 51 egocentric video sequences
- 19 subjects following instruction-based procedures
- Dense annotations for human-object interactions

**Tasks Benchmarked**:
1. Temporal detection of human-object interactions
2. Egocentric human-object interaction detection
3. Short-term object interaction anticipation
4. Natural language understanding of intents and entities

## ENIGMA-360 (arXiv 2026)

**Task**: Real industrial scenario procedural activities

- 360 temporally synchronized videos (180 ego + 180 exo)
- Complementary ego-exo viewpoint coverage
- Baseline experiments for temporal action segmentation, keystep recognition, and HOI detection

## Relevance to POPW

Egocentric perspective is crucial for wearable assistant applications. ENIGMA-360's synchronized ego-exo views enable study of viewpoint-invariant recognition. POPW should demonstrate competitive performance on these benchmarks.

## Citation

```bibtex
@article{ragusa2024enigma51,
  title={ENIGMA-51: Towards a Fine-Grained Understanding of Human-Object Interactions in Industrial Scenarios},
  author={Ragusa, Francesco and Leonardi, Rosario and Mazzamuto, Michele and Bonanno, Claudia and Scavo, Rosario and Furnari, Antonino and Farinella, Giovanni Maria},
  journal={arXiv preprint arXiv:2309.14809},
  year={2024},
  note={WACV 2024}
}

@article{ragusa2026enigma360,
  title={ENIGMA-360: An Ego-Exo Dataset for Human Behavior Understanding in Industrial Scenarios},
  author={Ragusa, Francesco and Leonardi, Rosario and Mazzamuto, Michele and Di Mauro, Daniele and Quattrocchi, Camillo and Passanisi, Alessandro and D'Ambra, Irene and Furnari, Antonino and Farinella, Giovanni Maria},
  journal={arXiv preprint arXiv:2603.09741},
  year={2026}
}
```
