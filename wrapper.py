%simport os
from pathlib import Path

import sys

base = %s
target = base / "%s"
  
import updater
updater.updater_check()
  
os.chdir(base)
if os.name == "nt":
    import subprocess
    subprocess.Popen(
        [str(target), *sys.argv[1:]],
        cwd=base,
    )
    sys.exit(0)
else:
    os.execv(str(target), [str(target), *sys.argv[1:]])
