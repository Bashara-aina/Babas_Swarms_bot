---
title: Contract 006 Industreal Evaluate
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

### CONTRACT #6: Create IndustReal evaluate.py

WHAT:
  Write `/home/newadmin/swarm-bot/project/popw/working/code/industreal/evaluate.py` adapted from IKEA POPW evaluate.py for IndustReal metrics: mAP@0.5 for ASD (24 classes), accuracy/F1 for AR (74 classes), temporal F1 for PSR (36 steps).

FILES:
  READ:
    - /media/newadmin/master/POPW/popw_main/evaluate.py
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/config.py (after Contract #1)
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/model.py (after Contract #2)
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/industreal_dataset.py (after Contract #3)
  WRITE:
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/evaluate.py

DONE_WHEN:
  - File exists at /home/newadmin/swarm-bot/project/popw/working/code/industreal/evaluate.py
  - File imports IndustRealDataset
  - File imports MultiTaskIndustReal
  - File computes ASD mAP@0.5 and mAP@[0.5:0.95] (24 classes)
  - File computes AR frame accuracy, Macro-F1, Weighted-F1
  - File computes PSR temporal F1@10, F1@25, F1@50 and Edit Score
  - File supports --split argument (train/val/test)
  - File supports --checkpoint argument
  - File writes eval outputs to C.EVAL_SAVE_DIR

PROOF_FORMAT:
  python3 -c "
import sys
sys.path.insert(0, '/home/newadmin/swarm-bot/project/popw/working/code/industreal')
import config as C
print('EVAL_SAVE_DIR:', C.EVAL_SAVE_DIR)
print('NUM_AR_CLASSES:', C.NUM_AR_CLASSES)
print('NUM_ASD_CLASSES:', C.NUM_ASD_CLASSES)
print('NUM_PSR_STEPS:', C.NUM_PSR_STEPS)
"

BLOCKER_IF:
  - Any dependency not created

DEPENDS_ON: 1, 2, 3
