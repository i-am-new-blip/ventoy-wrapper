#![shabang]
import os
import sys

base = "base-folder"
target = os.path.join(base, "baseexec")

os.chdir(base)
os.execv(target, [target, *sys.argv[1:]])
