---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/045-industreal-dataset-2024.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-11T18:14:42.342825"
}
---

---
paper_id: "045"
title: "IndustReal: A Dataset for Procedure Step Recognition Handling Execution Errors in Egocentric Videos"
authors: "Schoonbeek, Tim J.; Houben, Tim; Onvlee, Hans; de With, Peter H.N.; van der Sommen, Fons"
year: 2024
venue: "WACV 2024"
arxiv: "2310.17323"
doi: "10.48550/arXiv.2310.17323"
domain: "Assembly & Industrial Action Recognition"
popw_relevance: "Introduces procedure step recognition (PSR) task; addresses error detection in assembly"
key_contribution: "Defines novel Procedure Step Recognition (PSR) task; includes execution errors (omissions, mistakes) in dataset"
tags:
  - egocentric video
  - procedure step recognition
  - error detection
  - industrial assembly
  - WACV 2024
dataset_stats:
  videos: 84
  participants: 27
  duration: "6 hours"
  error_types: ["omissions", "execution errors"]
tasks_enabled:
  - "Action Recognition (AR)"
  - "Assembly State Detection (ASD)"
  - "Procedure Step Recognition (PSR)"
key_insight: "Traditional action recognition lacks success measurement; PSR focuses on correct completion AND order of procedural steps"
code_url: "https://github.com/TimSchoonbeek/IndustReal"
dataset_url: "https://timschoonbeek.github.io/industreal.html"
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
