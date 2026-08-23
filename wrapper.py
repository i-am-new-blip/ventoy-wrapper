%simport os
from pathlib import Path

import sys

base = Path.home() / "ventoy"
target = base / "%s"
  
import updater
updater.updater_check()
  
os.chdir(base)
os.execv(target, [str(target), *sys.argv[1:]])
