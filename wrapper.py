#![shabang]
import os
from path import Path
import sys

base = Path.home() / "ventoy"
target = base / "baseexec"

os.chdir(base)
os.execv(target, [str(target), *sys.argv[1:]])
