---
title: Contract 003 Industreal Dataset
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

### CONTRACT #3: Create IndustReal dataset loader

WHAT:
  Write `/home/newadmin/swarm-bot/project/popw/working/code/industreal/industreal_dataset.py` handling single-camera rgb frames, AR_labels.csv parsing, OD_labels.json (COCO) parsing, PSR_labels.csv parsing, pose.csv/hands.csv parsing.

FILES:
  READ:
    - /media/newadmin/master/POPW/popw_main/ikea_dataset.py
    - /media/newadmin/swarm-bot/project/popw/working/code/industreal/config.py (after Contract #1)
  WRITE:
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/industreal_dataset.py

DONE_WHEN:
  - File exists at /home/newadmin/swarm-bot/project/popw/working/code/industreal/industreal_dataset.py
  - File contains class IndustRealDataset
  - File loads AR_labels.csv for action labels (recording_id, action_class_id, action_description, start_frame.jpg, end_frame.jpg)
  - File loads OD_labels.json for COCO-format detection (24 categories)
  - File loads PSR_labels.csv for procedure step completion
  - File loads rgb frames from single camera (rgb/ directory)
  - File loads pose.csv and hands.csv (head pose + hand joints)
  - File uses train.csv/val.csv/test.csv split files
  - File resizes frames to IMG_HEIGHT x IMG_WIDTH (480x640)
  - File implements __getitem__ returning dict with: images, action_label, step_label, asd_boxes, asd_labels, head_pose, hand_joints, metadata
  - File implements collate_fn for batch loading

PROOF_FORMAT:
  python3 -c "
import sys
sys.path.insert(0, '/home/newadmin/swarm-bot/project/popw/working/code/industreal')
from industreal_dataset import IndustRealDataset
ds = IndustRealDataset(split='train', augment=False)
print('Dataset size:', len(ds))
if len(ds) > 0:
    sample = ds[0]
    print('Sample keys:', list(sample.keys()))
    print('action_label:', sample.get('action_label', 'MISSING'))
    print('step_label:', sample.get('step_label', 'MISSING'))
"

BLOCKER_IF:
  - config.py not created
  - IndustReal recordings directory not accessible

DEPENDS_ON: 1
