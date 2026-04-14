---
title: Industreal Dataset 2024
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
summary: 'IndustReal addresses a fundamental flaw in action recognition for procedural
  tasks: the lack of success measurement. While action recognition focuses on classifying
  actions, it ignores whether acti...'
wikilinks: []
confidence: medium
source: research
---

# Summary

IndustReal addresses a fundamental flaw in action recognition for procedural tasks: the lack of success measurement. While action recognition focuses on classifying actions, it ignores whether actions were completed correctly. This dataset introduces Procedure Step Recognition (PSR), focusing on recognizing both the correct completion and proper ordering of procedural steps, including execution errors.

## Key Contributions

1. **Novel PSR Task**: Procedure Step Recognition measuring completion and order correctness
2. **Error-Rich Dataset**: Includes omissions and execution errors in validation/test sets
3. **Multi-modal Annotations**: Action recognition, assembly state, and procedure step labels

## Dataset Characteristics

- **Content**: Assembly and maintenance of construction-toy car
- **Participants**: 27 subjects
- **Duration**: ~6 hours of egocentric video
- **Error Types**: Execution errors present exclusively in val/test sets for robustness evaluation

## Relevance to POPW

Error detection and procedure step recognition are critical for real-world assembly assistance. POPW should address the PSR task and demonstrate robustness to execution errors.

## Citation

```bibtex
@article{industreal2024,
  title={IndustReal: A Dataset for Procedure Step Recognition Handling Execution Errors in Egocentric Videos},
  author={Schoonbeek, Tim J. and Houben, Tim and Onvlee, Hans and de With, Peter H.N. and van der Sommen, Fons},
  journal={arXiv preprint arXiv:2310.17323},
  year={2024},
  note={WACV 2024}
}
```
