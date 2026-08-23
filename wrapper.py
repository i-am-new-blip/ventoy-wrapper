%simport os
from path import Path
import sys

base = Path.home() / "ventoy"
target = base / "%s"

os.chdir(base)
os.execv(target, [str(target), *sys.argv[1:]])
