---
title: Contract 005 Industreal Train
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

### CONTRACT #5: Create IndustReal train.py

WHAT:
  Write `/home/newadmin/swarm-bot/project/popw/working/code/industreal/train.py` adapted from IKEA POPW train.py for IndustReal 3-task training (ASD + AR + PSR), using IndustRealDataset, MultiTaskIndustReal model, and MultiTaskLoss.

FILES:
  READ:
    - /media/newadmin/master/POPW/popw_main/train.py
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/config.py (after Contract #1)
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/model.py (after Contract #2)
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/industreal_dataset.py (after Contract #3)
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/losses.py (after Contract #4)
  WRITE:
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/train.py

DONE_WHEN:
  - File exists at /home/newadmin/swarm-bot/project/popw/working/code/industreal/train.py
  - File imports IndustRealDataset (not IKEAMultiTaskDataset)
  - File imports MultiTaskIndustReal (not MultiTaskIKEA)
  - File imports MultiTaskLoss (not IKEA loss module)
  - File uses config.INDUSTREAL_ROOT for dataset paths
  - File uses config.NUM_AR_CLASSES, NUM_ASD_CLASSES, NUM_PSR_STEPS
  - File trains all 3 tasks simultaneously (det + act + psr)
  - File supports --resume checkpoint flag
  - File supports --preset flags for ablation (TRAIN_DET, TRAIN_ACT, TRAIN_PSR)
  - File saves checkpoints to OUTPUT_ROOT / 'checkpoints'
  - File logs to OUTPUT_ROOT / 'logs'

PROOF_FORMAT:
  python3 -c "
import sys
sys.path.insert(0, '/home/newadmin/swarm-bot/project/popw/working/code/industreal')
# Verify imports work
import config as C
from model import MultiTaskIndustReal
from losses import MultiTaskLoss
print('All imports successful')
print('NUM_PSR_STEPS:', C.NUM_PSR_STEPS)
"

BLOCKER_IF:
  - Any dependency not created

DEPENDS_ON: 1, 2, 3, 4
