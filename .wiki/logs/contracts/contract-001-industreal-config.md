---
title: Contract 001 Industreal Config
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

### CONTRACT #1: Create IndustReal config.py

WHAT:
  Write `/home/newadmin/swarm-bot/project/popw/working/code/industreal/config.py` adapting IKEA POPW config for IndustReal dataset with correct paths, class counts (74 AR + 24 ASD), single egocentric camera, PSR task constants.

FILES:
  READ:
    - /media/newadmin/master/POPW/popw_main/config.py
    - /media/newadmin/dataset/industreal/README.md
  WRITE:
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/config.py

DONE_WHEN:
  - File exists at /home/newadmin/swarm-bot/project/popw/working/code/industreal/config.py
  - File contains NUM_AR_CLASSES = 74
  - File contains NUM_ASD_CLASSES = 24
  - File contains NUM_PSR_STEPS = 36 (or appropriate max from PSR data)
  - File contains IMG_WIDTH = 1920, IMG_HEIGHT = 1080 (original IndustReal resolution)
  - File contains INDUSTREAL_ROOT pointing to /media/newadmin/dataset/industreal
  - File contains SINGLE_CAMERA = True
  - File contains CAMERAS = ['rgb'] (not multi-camera)
  - File contains train.csv/val.csv/test.csv split file paths
  - File does NOT contain FURNITURE_TYPES (IKEA-specific)
  - File does NOT contain IKEA multi-camera paths

PROOF_FORMAT:
  python3 -c "
import sys
sys.path.insert(0, '/home/newadmin/swarm-bot/project/popw/working/code/industreal')
import config as C
print('NUM_AR_CLASSES:', getattr(C, 'NUM_AR_CLASSES', 'MISSING'))
print('NUM_ASD_CLASSES:', getattr(C, 'NUM_ASD_CLASSES', 'MISSING'))
print('IMG_WIDTH:', getattr(C, 'IMG_WIDTH', 'MISSING'))
print('IMG_HEIGHT:', getattr(C, 'IMG_HEIGHT', 'MISSING'))
print('INDUSTREAL_ROOT:', getattr(C, 'INDUSTREAL_ROOT', 'MISSING'))
print('CAMERAS:', getattr(C, 'CAMERAS', 'MISSING'))
"

BLOCKER_IF:
  - /media/newadmin/dataset/industreal/ directory not accessible
  - Missing IndustReal train.csv/val.csv/test.csv split files

DEPENDS_ON: none
