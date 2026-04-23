### CONTRACT #4: Create IndustReal losses.py

WHAT:
  Write `/home/newadmin/swarm-bot/project/popw/working/code/industreal/losses.py` with Focal Loss (ASD), Class-Balanced Focal Loss (AR), PSR Binary Cross-Entropy, and MultiTaskLoss with Kendall uncertainty weighting for 3 tasks.

FILES:
  READ:
    - /media/newadmin/master/POPW/popw_main/losses.py
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/config.py (after Contract #1)
  WRITE:
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/losses.py

DONE_WHEN:
  - File exists at /home/newadmin/swarm-bot/project/popw/working/code/industreal/losses.py
  - File contains FocalLoss (for ASD detection)
  - File contains ClassBalancedFocalLoss (for AR activity)
  - File contains PSRLoss (binary CE per step, for PSR task)
  - File contains MultiTaskLoss with Kendall weighting for 3 tasks (det, act, psr)
  - File does NOT contain WingLoss (COCO pose not in IndustReal)
  - MultiTaskLoss.forward() returns dict with keys: total, det, activity, psr, w_det, w_pose, w_act

PROOF_FORMAT:
  python3 -c "
import sys
sys.path.insert(0, '/home/newadmin/swarm-bot/project/popw/working/code/industreal')
from losses import FocalLoss, ClassBalancedFocalLoss, PSRLoss, MultiTaskLoss
print('FocalLoss:', FocalLoss)
print('ClassBalancedFocalLoss:', ClassBalancedFocalLoss)
print('PSRLoss:', PSRLoss)
print('MultiTaskLoss:', MultiTaskLoss)
"

BLOCKER_IF:
  - config.py not created

DEPENDS_ON: 1
