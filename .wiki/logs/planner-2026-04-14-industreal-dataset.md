---
title: Planner 2026 04 14 Industreal Dataset
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '- **Source folders**:'
wikilinks: []
confidence: medium
source: research
---
## Plan: Prepare IndustReal Dataset
Date: 2026-04-14
Type: FILE_OPERATION

## Context Gathered
- **Source folders**:
  - `/home/newadmin/swarm-bot/project/popw/working/data/IndustReal-main/` - contains AR/ASD/PSR code and readme
  - `/home/newadmin/swarm-bot/project/popw/working/data/IndustReal_Dataset_v2_all/` - contains zipped data (train_p1-4.zip, val_p1-2.zip, test_p1-3.zip, action_recognition_labels.zip)
- **Target folder**: `/home/newadmin/swarm-bot/project/popw/working/data/datasets/industreal`
- **Split info**: action_recognition_labels.zip contains train.csv (36 recordings), val.csv (17 recordings), test.csv (31 recordings) = 84 total
- **Recording structure per README**: `recordings/{train,val,test}/recording_x/{rgb,stereo_*,depth,ambient_light,gaze.csv,hands.csv,pose.csv,AR_labels.csv,OD_labels.json,PSR_labels.csv}`
- **Code folder**: `popw_main` is designed for IKEA dataset with multi-camera structure, NOT IndustReal

## Risk Assessment
- The IKEA code expects IKEA-specific data structures (furniture types, cameras dev1/dev2/dev3, COCO annotations)
- IndustReal has different structure (single egocentric view, different annotations)
- Cannot force IndustReal into IKEA data format without significant code changes
- Task says "Do NOT modify original code" - so compatibility must be achieved via config/adapter

## Approach
1. Create the IndustReal dataset folder with proper train/val/test splits
2. Extract data zips to proper locations (using symlinks to avoid data duplication)
3. Copy the author-provided split CSVs
4. Create an IndustReal config that can work with the existing code framework
5. Verify structure matches author expectations
