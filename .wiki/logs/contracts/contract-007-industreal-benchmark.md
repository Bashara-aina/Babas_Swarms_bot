### CONTRACT #7: Create IndustReal benchmark.py

WHAT:
  Write `/home/newadmin/swarm-bot/project/popw/working/code/industreal/benchmark.py` adapted from IKEA POPW benchmark.py for IndustReal model GFLOPs/FPS/GPU memory measurement.

FILES:
  READ:
    - /media/newadmin/master/POPW/popw_main/benchmark.py
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/config.py (after Contract #1)
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/model.py (after Contract #2)
  WRITE:
    - /home/newadmin/swarm-bot/project/popw/working/code/industreal/benchmark.py

DONE_WHEN:
  - File exists at /home/newadmin/swarm-bot/project/popw/working/code/industreal/benchmark.py
  - File imports MultiTaskIndustReal
  - File uses config.IMG_HEIGHT, IMG_WIDTH for benchmark
  - File supports --checkpoint argument
  - File measures GFLOPs, FPS batch=1, FPS batch=N, peak GPU memory

PROOF_FORMAT:
  python3 -c "
import sys
sys.path.insert(0, '/home/newadmin/swarm-bot/project/popw/working/code/industreal')
import config as C
from model import MultiTaskIndustReal
print('IMG_SIZE:', C.IMG_SIZE)
print('Model: MultiTaskIndustReal available')
"

BLOCKER_IF:
  - Any dependency not created

DEPENDS_ON: 1, 2
