# POPW Protocol — OpenCode Context

## What This Project Is
Multi-task learning system for IKEA assembly action recognition.
Repo: https://github.com/Bashara-aina/popw-protocol
Local path: /media/newadmin/master/POPW/working/

## Architecture
- Backbone: ResNet-50
- Task 1: Pose estimation (heatmap keypoints, COCO 17-keypoint format)
- Task 2: Activity classification (IKEA ASM assembly steps)
- Conditioning: FiLM (Feature-wise Linear Modulation) between tasks
- Loss weighting: Kendall uncertainty weighting (homoscedastic)
- Data: IKEA ASM dataset, multi-camera RGBD
- Training entry: python train.py --preset improved4

## Key Files
- code/popw_main/train.py — main training loop
- code/popw_main/scripts/validate_multi_camera.py — multi-cam eval
- code/popw_main/test_dataloader.py — data pipeline test
- docs/MASTER_PLAN_COMPLIANCE_REPORT.md — implementation checklist

## Reference Libraries (in .wiki/popw-references/)
- mmpose/ — pose estimation standard (compare heatmap outputs here)
- detectron2/ — detection backbone reference (multi-camera detection)
- mmaction2/ — action recognition standard (compare accuracy here)
- performer-pytorch/ — attention-based FiLM alternative
- pointnet2/ — depth channel processing reference

## Agent Instructions
When working on ANY popw-protocol task:
1. Search graphiti for recent session history on this task
2. Query mmpose docs for pose-related questions
3. Query mmaction2 docs for action classification questions
4. NEVER suggest changing FiLM to attention without checking performer-pytorch README
5. All training runs output to: artifacts/popw_main_runs/
6. Validation command: python scripts/validate_multi_camera.py