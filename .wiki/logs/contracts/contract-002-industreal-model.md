### CONTRACT #2: Create IndustReal model.py

WHAT:
  Write `/home/newadmin/swarm-bot/project/popw/working/code/industreal/model.py` with ResNet50-FPN backbone and 3 task heads adapted for IndustReal: ASD head (24 COCO detection classes), AR head (74 activity classes), PSR head (temporal segmentation via per-frame step classification).

FILES:
  READ:
    - /media/newadmin/master/POPW/popw_main/model.py
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/config.py (after Contract #1)
  WRITE:
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/model.py

DONE_WHEN:
  - File exists at /home/newadmin/swarm-bot/project/popw/working/code/industreal/model.py
  - File contains class MultiTaskIndustReal
  - File contains DetectionHead (ASD, 24 classes)
  - File contains ActivityHead (AR, 74 classes)
  - File contains PSRHead (per-frame step completion classification, 36 steps)
  - File does NOT contain PoseHead (COCO keypoints not in IndustReal)
  - File does NOT contain PoseFiLMModule (pose-conditioned FiLM not applicable)
  - File does NOT contain IKEA multi-camera logic
  - forward() returns dict with keys: cls_preds, reg_preds, anchors, act_logits, psr_logits
  - PSRHead uses temporal convolution or MLP for frame-level step completion

PROOF_FORMAT:
  python3 -c "
import sys
sys.path.insert(0, '/home/newadmin/swarm-bot/project/popw/working/code/industreal')
import config as C
from model import MultiTaskIndustReal
model = MultiTaskIndustReal(pretrained=False)
outputs = model(torch.randn(1, 3, 480, 640))
print('Keys:', list(outputs.keys()))
print('cls_preds shape:', outputs['cls_preds'].shape if 'cls_preds' in outputs else 'MISSING')
print('act_logits shape:', outputs['act_logits'].shape if 'act_logits' in outputs else 'MISSING')
print('psr_logits shape:', outputs['psr_logits'].shape if 'psr_logits' in outputs else 'MISSING')
"

BLOCKER_IF:
  - config.py not created (depends on Contract #1)
  - PSRHead architecture unclear (may need ADR decision)

DEPENDS_ON: 1
